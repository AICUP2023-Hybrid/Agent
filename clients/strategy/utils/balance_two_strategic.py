import networkx as nx
import numpy as np

from clients.strategy.startegy import MoveTroopAction
from clients.utils.get_possible_danger import get_node_danger
from clients.utils.update_details import GameData
from components.node import Node


def get_node_attack_advantage(gdata: GameData, node: Node):
    graph = gdata.get_passable_board_graph(node.number_of_troops)
    shortest_paths = nx.shortest_path_length(graph, source=node.id)
    targets = [n for n in gdata.nodes if n.is_strategic and n.owner != node.owner and n.id in shortest_paths]

    score = 0
    for target in targets:
        score = max(score, node.number_of_troops - shortest_paths[target.id])
    return score


def balance_troops_between_two_strategics(gdata: GameData, src: Node, dst: Node):
    troop_cnt = src.number_of_troops
    possible_assigns = []

    src.save_version()
    dst.save_version()
    for i in range(0, troop_cnt):
        src.number_of_troops = troop_cnt - i
        dst.number_of_troops = i + 1 if gdata.done_fort else i * 2

        src_strategic_danger = get_node_danger(gdata, src)
        dst_strategic_danger = get_node_danger(gdata, dst)
        danger = max(src_strategic_danger, dst_strategic_danger)

        if danger <= 0:
            possible_assigns.append((src.number_of_troops, dst.number_of_troops, i))
    src.restore_version()
    dst.restore_version()

    if len(possible_assigns) == 0:
        if src.score_of_strategic > dst.score_of_strategic:
            return MoveTroopAction(src=src, dest=dst, count=troop_cnt - 1)

    src.save_version()
    dst.save_version()

    scores = []
    for pos in possible_assigns:
        src.number_of_troops = pos[0]
        dst.number_of_troops = pos[1]
        min_score = 1
        src_score = max(min_score, get_node_attack_advantage(gdata, src))
        dst_score = max(min_score, get_node_attack_advantage(gdata, dst))
        scores.append(src_score + dst_score)

    src.restore_version()
    dst.restore_version()

    best_move = np.argmax(scores)
    if possible_assigns[best_move][2] > 0:
        return MoveTroopAction(src=src, dest=dst, count=possible_assigns[best_move][2])
    return None
