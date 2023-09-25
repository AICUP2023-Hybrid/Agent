import networkx as nx
import numpy as np

from clients.strategy.startegy import MoveTroopAction
from clients.utils.get_possible_danger import get_node_danger
from clients.utils.update_details import GameData
from components.node import Node


def get_node_attack_advantage(gdata: GameData, node: Node):
    graph = gdata.get_passable_board_graph(node.number_of_troops)
    shortest_paths = nx.shortest_path_length(graph, source=node.id, weight="weight")
    targets = [n for n in gdata.nodes if n.is_strategic and n.owner != node.owner and n.id in shortest_paths]

    score = 0
    for target in targets:
        score = max(score, node.number_of_troops - shortest_paths[target.id])
    return score


def balance_troops_between_two_strategics(gdata: GameData, src: Node, dst: Node, can_fort=True, return_danger=False):
    troop_cnt = src.number_of_troops
    player = src.owner

    src.save_version()
    dst.save_version()
    min_danger, move_troops = np.Inf, 0
    for fort_node in ([src, dst] if not gdata.players_done_fort[player] and can_fort else [None]):
        for i in range(0, troop_cnt):
            src.number_of_troops = troop_cnt - i
            dst.number_of_troops = i + 1
            if fort_node:
                fort_node.number_of_troops *= 2
                fort_node.number_of_troops -= 1

            src_strategic_danger = get_node_danger(gdata, src)
            dst_strategic_danger = get_node_danger(gdata, dst)
            danger = max(src_strategic_danger, dst_strategic_danger)

            if danger < min_danger:
                move_troops = i
                min_danger = danger
    src.restore_version()
    dst.restore_version()

    move = None
    if min_danger > 0 and dst.score_of_strategic > src.score_of_strategic:
        move = MoveTroopAction(src=src, dest=dst, count=troop_cnt - 1)
    if min_danger <= 0 < move_troops:
        move = MoveTroopAction(src=src, dest=dst, count=move_troops)
    if return_danger:
        return move, min_danger
    return move


def check_balance_two_strategic_possible(gdata: GameData, src: Node, dst: Node, can_fort=True):
    troop_cnt = src.number_of_troops
    player = src.owner

    fort_possible = can_fort and not gdata.players_done_fort[player]
    src.number_of_troops = troop_cnt * 2 - 1 if fort_possible else troop_cnt
    dst.number_of_troops = 1
    danger_src = get_node_danger(gdata, src)
    if danger_src > 0:
        return False
    start_at = int(-danger_src / (0.7 * 2 if fort_possible else 0.7))

    src.save_version()
    dst.save_version()
    for fort_node in ([src, dst] if not gdata.players_done_fort[player] and can_fort else [None]):
        prev_src_danger, prev_dst_danger = None, None
        for i in range(start_at, troop_cnt):
            src.number_of_troops = troop_cnt - i
            dst.number_of_troops = i + 1
            if fort_node:
                fort_node.number_of_troops *= 2
                fort_node.number_of_troops -= 1

            src_strategic_danger = get_node_danger(gdata, src)
            dst_strategic_danger = get_node_danger(gdata, dst)
            danger = max(src_strategic_danger, dst_strategic_danger)

            if danger <= 0:
                src.restore_version()
                dst.restore_version()
                return True

            if prev_src_danger is not None:
                if src_strategic_danger > prev_src_danger:
                    break

            prev_src_danger, prev_dst_danger = src_strategic_danger, dst_strategic_danger
    src.restore_version()
    dst.restore_version()

    return False
