from collections import defaultdict

import networkx as nx
import numpy as np
from networkx import NetworkXNoPath

from clients.utils.attack_chance import get_expected_casualty
from clients.utils.update_details import GameData
from components.node import Node


def get_min_loss_path(gdata: GameData, target: Node, player,
                      max_troops_to_put=None, attack_power_threshold=0):
    graph = gdata.get_passable_board_graph(player)
    gdata.update_remaining_troops_by_map()
    if max_troops_to_put is None:
        remaining_troops = gdata.remaining_init[player]
    else:
        remaining_troops = min(max_troops_to_put, gdata.remaining_init[player])

    distances = nx.shortest_path_length(graph, target=target.id, weight='weight')
    min_loss = np.Inf
    min_path, min_src = [], None
    for src in gdata.nodes:
        if src.owner not in [player, None] or src.id not in distances:
            continue
        attack_power = gdata.nodes[src.id].number_of_troops + remaining_troops - distances[src.id]
        if attack_power_threshold <= attack_power and distances[src.id] < min_loss:
            min_loss = distances[src.id]
            min_src = src
    if min_src is not None:
        min_path = [gdata.nodes[x] for x in nx.shortest_path(graph, min_src.id, target.id, weight='weight')]
    return min_loss, min_path


def get_surprise_danger(gdata: GameData, target: Node, player, return_max_path=False, include_src_troops=False,
                        max_troops_to_put=None):
    graph = gdata.get_passable_board_graph(player)
    gdata.update_remaining_troops_by_map()
    if max_troops_to_put is None:
        remaining_troops = gdata.remaining_init[player]
    else:
        remaining_troops = min(max_troops_to_put, gdata.remaining_init[player])

    distances = nx.shortest_path_length(graph, target=target.id, weight='weight')
    max_attack_power = -np.Inf
    max_path, max_src = [], None
    for src in gdata.nodes:
        if src.owner not in [player, None] or src.id not in distances:
            continue
        attack_power = remaining_troops - distances[src.id]
        if include_src_troops:
            attack_power += gdata.nodes[src.id].number_of_troops
        if max_attack_power < attack_power:
            max_attack_power = attack_power
            max_src = src
    if return_max_path:
        if max_src is not None:
            max_path = [gdata.nodes[x] for x in nx.shortest_path(graph, max_src.id, target.id, weight='weight')]
        return max_attack_power, max_path
    return max_attack_power


def get_targets_by_attacker(gdata: GameData, attacker_id):
    res = []
    for node in [node for node in gdata.nodes if node.is_strategic]:
        if node.owner == attacker_id:
            continue
        res.append((
            get_surprise_danger(gdata, node, attacker_id, include_src_troops=True),
            node
        ))
    return sorted(res, key=lambda x: x[0], reverse=True)


def get_node_danger(gdata: GameData, node: Node, return_path=False, max_troops_to_expect=None):
    # return get_relative_strategic_node_danger(gdata, node.owner)[node]
    max_attack_power, path = -np.Inf, None
    for player in range(gdata.player_cnt):
        if player == node.owner:
            continue
        res = get_surprise_danger(gdata, node, player,
                                  include_src_troops=True,
                                  max_troops_to_put=max_troops_to_expect,
                                  return_max_path=return_path)
        if return_path:
            attack_power = res[0]
        else:
            attack_power = res
        if max_attack_power < attack_power:
            max_attack_power = attack_power
            if return_path:
                path = res[1]

    if return_path:
        return max_attack_power, path
    return max_attack_power  # returns expected amount of troops left after being attacked


def get_relative_strategic_node_danger(gdata: GameData, defender_id):
    node_dangers = defaultdict(lambda: 0)
    for attacker_id in range(gdata.player_cnt):
        if attacker_id == defender_id:
            continue
        non_defender_danger = 0
        res = get_targets_by_attacker(gdata, attacker_id)
        for danger, node in res:
            if node.owner != defender_id:
                non_defender_danger = max(danger, non_defender_danger)
        for danger, node in res:
            if node.owner == defender_id:
                node_dangers[node] = max(node_dangers[node], danger - non_defender_danger)
    return node_dangers


def get_two_way_attack(gdata: GameData, node_st1: Node, node_st2: Node):
    graph: nx.DiGraph = gdata.get_passable_board_graph(gdata.player_id)
    remaining_troops = gdata.remaining_init[gdata.player_id]
    candidate = None

    # two separated the shortest paths
    n1_paths, n2_paths = [nx.shortest_path_length(graph, target=n.id, weight='weight') for n in [node_st1, node_st2]]
    mx1, mx2 = -np.Inf, -np.Inf
    s1, s2 = None, None
    for node in gdata.nodes:
        if node.id not in n1_paths or node.id not in n2_paths:
            continue
        if node.owner in [None, gdata.player_id]:
            p1 = node.number_of_troops - n1_paths[node.id]
            p2 = node.number_of_troops - n2_paths[node.id]
            if mx1 < p1:
                s1 = node
                mx1 = p1
            if mx2 < p2:
                s2 = node
                mx2 = p2
    if None not in [s1, s2] and s1.id != s2.id:
        candidate = (min(0, mx1) + min(0, mx2), 0, s1, s2, node_st1, node_st2, mx1, mx2)  # (score, type, src1, src2)

    for mid_node in gdata.nodes:
        if mid_node.owner in [None, gdata.player_id]:
            s_dist = nx.shortest_path_length(graph, target=mid_node.id, weight='weight')
            e_dist = nx.shortest_path_length(graph, source=mid_node.id, weight='weight')
            if node_st1.id not in e_dist or node_st2.id not in e_dist:
                continue
            b, c = e_dist[node_st1.id], e_dist[node_st2.id]
            for src, dist in s_dist.items():
                if gdata.nodes[src] in [None, gdata.player_id]:
                    a = gdata.nodes[src].number_of_troops - dist
                    if candidate is None or candidate[0] > a - b - c:
                        candidate = (a - b - c, 1, gdata.nodes[src], mid_node, node_st1, node_st2, b, c)

    if candidate is not None:
        score = remaining_troops + candidate[0]
        if score < 2:
            return None
    return candidate
