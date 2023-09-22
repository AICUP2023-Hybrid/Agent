from typing import List, Optional

from clients.strategy.startegy import FortAction
from clients.utils.attack_chance import get_expected_casualty
from clients.utils.get_possible_danger import get_node_danger
from clients.utils.update_details import GameData
from components.node import Node


def get_fort_from_nodes(gdata: GameData, nodes: List[Node]):
    nodes = [
        node for node in nodes if node.is_strategic and node.owner == gdata.player_id and node.number_of_troops > 1
    ]
    if gdata.done_fort or len(nodes) == 0:
        return None

    expected_causalty = get_expected_casualty()
    possibilities = []
    for target in nodes:
        danger = get_node_danger(gdata, target)
        if danger <= 0:
            continue
        total_count = target.number_of_troops
        fortify_count = None
        for to_fortify in range(total_count):
            delta = expected_causalty[target.number_of_troops + to_fortify] - expected_causalty[target.number_of_troops]
            if danger - delta <= 0:
                fortify_count = to_fortify
            if danger - delta <= -10:  # TODO tune this hyperparameter
                break
        if fortify_count:
            possibilities.append(FortAction(node=target, count=fortify_count))
    best_option: Optional[FortAction] = None
    for pos in possibilities:
        better = best_option is None
        better = better or pos.node.score_of_strategic > best_option.node.score_of_strategic
        if better:
            best_option = pos
    return best_option
