from collections import defaultdict
from typing import List, Set

import networkx as nx
from math import ceil, floor

from clients.game_client import GameClient
from clients.utils.attack_chance import get_expected_casualty
from components.node import Node


def maximize_score(game: GameClient, can_put_troops=True):
    gdata = game.game_data
    remaining_troops = gdata.remaining_init[gdata.player_id]
    if not can_put_troops:
        remaining_troops = 0
    puts = defaultdict(lambda: 0)

    for node in gdata.nodes:
        node.save_version()

    cur_nodes = [node.id for node in gdata.nodes if node.owner == gdata.player_id]
    for node in gdata.nodes:
        if node.owner is None and remaining_troops > 0:
            cur_nodes.append(node.id)
            node.number_of_troops = 1
            remaining_troops -= 1
            puts[node.id] += 1

    graph = gdata.get_passable_board_graph(gdata.player_id)
    attack_graph = nx.DiGraph()
    src_node = [node if node.id in cur_nodes else None for node in gdata.nodes]
    potential = [node.number_of_troops - 1 if node.id in cur_nodes else 0 for node in gdata.nodes]

    for node in graph.nodes:
        attack_graph.add_node(node)

    while True:
        max_attack_power, par, tar, w = -1000, None, None, None
        for u, v, a in graph.edges(data=True):
            weight = a['weight']
            if u not in cur_nodes or v in cur_nodes:
                continue
            pot = potential[src_node[u].id]
            attack_power = pot - weight
            if attack_power >= max_attack_power and weight <= pot + remaining_troops:
                max_attack_power = attack_power
                w = weight
                par = gdata.nodes[u]
                tar = gdata.nodes[v]
        if max_attack_power == -1000:
            break
        attack_graph.add_edge(par.id, tar.id, weight=w)
        src = src_node[par.id]
        src_node[tar.id] = src_node[par.id]
        left = ceil(max(0, w - potential[src.id]))
        potential[src.id] = floor(max(0, potential[src.id] - w))
        cur_nodes.append(tar.id)
        remaining_troops -= left
        puts[src.id] += left

    while remaining_troops > 0 and len(puts) > 0:
        for node_id, put_troops in puts.items():
            puts[node_id] += 1
            remaining_troops -= 1
            if remaining_troops == 0:
                break

    for node in gdata.nodes:
        node.restore_version()

    exp_cas = [0 for node in attack_graph.nodes]
    sorted_nodes = reversed(list(nx.topological_sort(attack_graph)))
    expected_casualty = get_expected_casualty()
    for node in sorted_nodes:
        exp_cas[node] += expected_casualty[gdata.nodes[node].number_of_troops]
        for nei in attack_graph.neighbors(node):
            exp_cas[node] += exp_cas[nei]

    if can_put_troops:
        for node_id, put_troops in puts.items():
            game.put_troop(node_id, put_troops)
        gdata.update_game_state()
        game.next_state()

    for node_id in nx.topological_sort(attack_graph):
        node = gdata.nodes[node_id]
        exp_sum = sum([exp_cas[nei] for nei in attack_graph.neighbors(node_id)])
        has_attack = False
        for nei in attack_graph.neighbors(node_id):
            # print(game.attack(node.id, nei, 1, exp_cas[nei] / exp_sum), file=log_file)
            try:
                game.attack(node.id, nei, 0, max(0.001, min(0.999, exp_cas[nei] / exp_sum)))
                has_attack = True
            except:
                pass
            exp_sum -= exp_cas[nei]
        if has_attack:
            gdata.update_game_state()

    while True:
        gdata.update_game_state()

        attack_round_nodes: Set[Node] = set()
        for node in gdata.nodes:
            if node.owner == gdata.player_id and node.number_of_troops > 1 and node not in attack_round_nodes:
                for nei in sorted(node.adj_main_map, key=lambda n: n.number_of_troops):
                    if nei.owner != gdata.player_id and nei not in attack_round_nodes:
                        try:
                            src_neighbours = _get_unowned_neighbours(node, gdata.player_id)
                            dst_neighbours = _get_unowned_neighbours(nei, gdata.player_id)
                            move_fraction = len(dst_neighbours - src_neighbours) / max(
                                len((dst_neighbours | src_neighbours) - set(nei)), 1)
                            game.attack(node.id, nei.id, 0, _std_mv_frac(move_fraction))
                            attack_round_nodes.add(node)
                            attack_round_nodes.add(nei)
                            break
                        except:
                            pass

        if len(attack_round_nodes) == 0:
            break


def _get_unowned_neighbours(node: Node, player_id) -> Set[Node]:
    return set(nei for nei in node.adj_main_map if nei.owner != player_id)


def _std_mv_frac(frac: float):
    return max(min(frac, 0.999), 0.001)
