from collections import defaultdict

import networkx as nx
from math import ceil, floor

from clients.game_client import GameClient
from clients.utils.attack_chance import get_expected_casualty


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
        min_w, par, tar = 1000, None, None
        for u, v, a in graph.edges(data=True):
            weight = a['weight']
            if u not in cur_nodes or v in cur_nodes:
                continue
            pot = potential[src_node[u].id]
            if weight <= min_w and weight <= pot + remaining_troops:
                min_w = weight
                par = gdata.nodes[u]
                tar = gdata.nodes[v]
        if min_w == 1000:
            break
        attack_graph.add_edge(par.id, tar.id, weight=min_w)
        src = src_node[par.id]
        src_node[tar.id] = src_node[par.id]
        left = ceil(max(0, min_w - potential[src.id]))
        potential[src.id] = floor(max(0, potential[src.id] - min_w))
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
                game.attack(node.id, nei, 1, max(0.001, min(0.999, exp_cas[nei] / exp_sum)))
                has_attack = True
            except:
                pass
            exp_sum -= exp_cas[nei]
        if has_attack:
            gdata.update_game_state()
