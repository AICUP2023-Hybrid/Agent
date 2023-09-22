import networkx as nx
import numpy as np

import online_src
from clients.game_client import GameClient
from clients.utils.attack_chance import get_expected_casualty
from clients.utils.get_possible_danger import get_node_danger
from clients.utils.update_details import GameData
from components.node import Node


def get_init_score(gdata: GameData, nodes):
    graph = gdata.get_board_graph()
    strategics = [[node, 0] for node in gdata.nodes if node.is_strategic and node.owner != gdata.player_id]
    for src in nodes:
        too_close = len([nei for nei in src.adj_main_map if nei.is_strategic]) > 0
        if too_close:
            continue
        lengths = nx.shortest_path_length(graph, source=src.id)
        for i, (node, cnt) in enumerate(strategics):
            if node.id in lengths and lengths[node.id] <= 3:
                point = [0, 0, 1, 0.25]
                strategics[i][1] += point[lengths[node.id]]
    score = 0
    for node, cnt in strategics:
        score += max(cnt, 1)
    return score


def initialize_turn(game: GameClient | online_src.game.Game):
    game.game_data.update_game_state()

    gdata = game.game_data

    # Get the strategic resource
    nodes_sorted = sorted(gdata.nodes, key=lambda x: -x.score_of_strategic)
    for node in nodes_sorted:
        if not node.is_strategic:
            break
        if node.owner is None:
            print(game.put_one_troop(node.id), "-- putting one troop on", node.id)
            return

    # Add two nodes to initialization for reachability and extra troop
    my_nodes = [node for node in gdata.nodes if node.owner == gdata.player_id]
    if len(my_nodes) < 4:
        max_score, tar = -np.Inf, None
        for mid1 in gdata.nodes:
            if mid1.owner is not None:
                continue
            score = get_init_score(gdata, my_nodes + [mid1])
            if max_score < score:
                max_score = score
                tar = mid1
            if len(my_nodes) < 3:
                for mid2 in gdata.nodes:
                    if mid1 == mid2 or mid2.owner is not None:
                        continue
                    score = get_init_score(gdata, my_nodes + [mid1, mid2])
                    if max_score < score:
                        max_score = score
                        tar = mid1
        if tar is not None:
            print(game.put_one_troop(tar.id), "-- putting one troop on", tar.id)
            return

    my_nodes = [
        (node, get_node_danger(game.game_data, node))
        for node in nodes_sorted if node.owner == gdata.player_id and node.is_strategic
    ]
    my_nodes = sorted(my_nodes, key=lambda x: -x[1])
    for node, danger in my_nodes:
        if danger > 0:
            print(game.put_one_troop(node.id), "-- putting one troop on", node.id)
            return
