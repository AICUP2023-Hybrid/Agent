import networkx as nx
import numpy as np
from networkx import NetworkXNoPath

from game_components.Node import Node
from utils.attack_chance import get_expected_casualty
from utils.update_details import GameData


def get_surprise_danger(gdata: GameData, target: Node, player):
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
    for src in source_nodes:
        try:
            subgraph = graph.subgraph(passable_nodes + [src])
            max_attack_power = max(
                max_attack_power,
                remaining_troops - nx.shortest_path_length(subgraph, src, target.id, weight='weight')
            )
        except NetworkXNoPath:
            continue

    return max_attack_power


def get_normal_attack(gdata: GameData, target, player):
    graph = gdata.get_board_graph()

    passable_nodes = []
    source_nodes = []
    for node in gdata.nodes:
        if node.owner not in [player, None]:
            passable_nodes.append(node.id)
        elif node.owner is not None:
            source_nodes.append(node.id)

    max_attack_power = 0
    for src in source_nodes:
        try:
            subgraph = graph.subgraph(passable_nodes + [src])
            max_attack_power = max(
                max_attack_power,
                gdata.nodes[src].number_of_troops - nx.shortest_path_length(subgraph, src, target.id, weight='weight')
            )
        except NetworkXNoPath:
            continue
    return max_attack_power


def get_node_danger(gdata: GameData, node: Node):
    attack_power = 0
    for player in range(gdata.player_cnt):
        if player == gdata.player_id:
            continue
        attack_power = max(attack_power, get_surprise_danger(gdata, node, player))
        attack_power = max(attack_power, get_normal_attack(gdata, node, player))

    return attack_power  # returns expected amount of troops left after being attacked

