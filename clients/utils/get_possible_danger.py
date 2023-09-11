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
                max_path = [gdata.nodes[x] for x in nx.shortest_path(subgraph, src, target.id)]
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
                max_path = [gdata.nodes[x] for x in nx.shortest_path(subgraph, src, target.id)]
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

