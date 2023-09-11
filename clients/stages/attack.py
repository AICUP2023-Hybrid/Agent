from math import floor, ceil
from typing import List

from clients.game_client import GameClient
from clients.utils.attack_chance import get_expected_casualty
from clients.utils.get_possible_danger import get_surprise_danger, get_node_danger, get_normal_attack_danger
from clients.utils.update_details import GameData
from components.node import Node

f = open('log.txt', 'w')


def plan_attack(game: GameClient):
    gdata: GameData = game.game_data
    remaining_troops = gdata.remaining_init[gdata.player_id]
    strategic_nodes = [node for node in gdata.nodes if node.owner != gdata.player_id and node.is_strategic]
    my_strategic = [node for node in gdata.nodes if node.owner == gdata.player_id and node.is_strategic]

    max_attack_power, max_path = 0, []
    for st_node in strategic_nodes:
        attack_power, path = get_surprise_danger(gdata, st_node, gdata.player_id, return_max_path=True)
        path: List[Node]
        if len(path) == 0:
            continue
        for node in path:
            node.save_version()
            node.owner = gdata.player_id
            node.number_of_troops = 1
        path[-1].number_of_troops = int((attack_power + 1) * 2 if not gdata.done_fort else attack_power + 1)
        danger = get_node_danger(gdata, st_node)
        for node in path:
            node.restore_version()
        if danger > 0:
            continue
        if max_attack_power < attack_power:
            max_attack_power = attack_power
            max_path = path

    if len(max_path) > 0:
        print('doing strategic attack', file=f)
        game.put_troop(max_path[0].id, remaining_troops)
        gdata.update_game_state()
        game.next_state()
        print([node.id for node in max_path], file=f)
        for i in range(len(max_path) - 1):
            if max_path[i].owner != gdata.player_id and max_path[i].number_of_troops < 2:
                break
            print(game.attack(max_path[i].id, max_path[i + 1].id, 0, 1), file=f)
            gdata.update_game_state()
        game.next_state()
        # no moving troops
        game.next_state()
        if not gdata.done_fort and max_path[-1].owner == gdata.player_id:
            game.fort(max_path[-1].id, max_path[-1].number_of_troops)
            gdata.update_game_state()
        return

    expected_casualty = get_expected_casualty()
    max_score, src, tar = 0, None, None
    for node in gdata.nodes:
        if node.owner not in [gdata.player_id, None]:
            continue
        for nei in node.adj_main_map:
            if nei.owner not in [None, gdata.player_id]:
                troops = nei.number_of_troops + nei.number_of_fort_troops
                casualty = expected_casualty[troops] + 1
                score = node.number_of_troops + 3 - casualty
                if max_score < score:
                    max_score = score
                    src = node
                    tar = nei

    if max_score > 0:
        print('doing single attack', file=f)
        troops_to_put = max(0, int(ceil(3 - floor(max_score))))
        print(troops_to_put, src.id, file=f)
        if troops_to_put > 0:
            game.put_troop(src.id, troops_to_put)
        gdata.update_game_state()
        game.next_state()
        print(game.attack(src.id, tar.id, 0, 1), file=f)
        gdata.update_game_state()
        game.next_state()
        # no moving troops
        game.next_state()
