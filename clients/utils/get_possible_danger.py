import networkx as nx
import numpy as np
from networkx import NetworkXNoPath

from clients.utils.attack_chance import get_expected_casualty
from clients.utils.update_details import GameData
from components.node import Node


def get_surprise_danger(gdata: GameData, target: Node, player, return_max_path=False, include_src_troops=False):
    graph = gdata.get_board_graph()
    remaining_troops = gdata.remaining_init[player]

    passable_nodes = []
    source_nodes = []
    for node in gdata.nodes:
        if node.owner not in [player, None]:
            passable_nodes.append(node.id)
        else:
            source_nodes.append(node.id)
    max_attack_power = 0
    max_path = []
    for src in source_nodes:
        try:
            subgraph = graph.subgraph(list(set(passable_nodes + [src] + [target.id])))
            attack_power = remaining_troops - nx.shortest_path_length(subgraph, src, target.id, weight='weight')
            if include_src_troops:
                attack_power += gdata.nodes[src].number_of_troops
            if max_attack_power < attack_power:
                max_attack_power = attack_power
                max_path = [gdata.nodes[x] for x in nx.shortest_path(subgraph, src, target.id, weight='weight')]
        except NetworkXNoPath:
            continue
    if return_max_path:
        return max_attack_power, max_path
    return max_attack_power


def get_normal_attack_danger(gdata: GameData, target, player, return_max_path=False):
    graph = gdata.get_board_graph()

    passable_nodes = []
    source_nodes = []
    for node in gdata.nodes:
        if node.owner not in [player, None]:
            passable_nodes.append(node.id)
        elif node.owner is not None:
            source_nodes.append(node.id)

    max_attack_power = 0
    max_path = []
    for src in source_nodes:
        try:
            subgraph = graph.subgraph(list(set(passable_nodes + [src] + [target.id])))
            attack_power = gdata.nodes[src].number_of_troops - nx.shortest_path_length(subgraph, src, target.id, weight='weight')
            if max_attack_power < attack_power:
                max_attack_power = attack_power
                max_path = [gdata.nodes[x] for x in nx.shortest_path(subgraph, src, target.id, weight='weight')]
        except NetworkXNoPath:
            continue
    if return_max_path:
        return max_attack_power, max_path
    return max_attack_power


def get_node_danger(gdata: GameData, node: Node):
    attack_power = 0
    for player in range(gdata.player_cnt):
        if player == gdata.player_id:
            continue
        attack_power = max(attack_power, get_surprise_danger(gdata, node, player))
        attack_power = max(attack_power, get_normal_attack_danger(gdata, node, player))

    return attack_power  # returns expected amount of troops left after being attacked


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
