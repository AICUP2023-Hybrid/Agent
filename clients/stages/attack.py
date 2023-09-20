import json
from math import floor, ceil
from typing import List

import networkx as nx

import online_src
from clients.game_client import GameClient
from clients.utils.attack_chance import get_expected_casualty
from clients.utils.get_possible_danger import get_surprise_danger, get_node_danger, \
    get_two_way_attack
from clients.utils.maximize_score import maximize_score
from clients.utils.update_details import GameData
from components.node import Node

f = open(f'log0.txt', 'w')
game_config = json.load(open('config.json', 'r'))


def attack_path(game: GameClient, path):
    gdata = game.game_data

    for i in range(len(path) - 1):
        if path[i].owner != gdata.player_id or path[i].number_of_troops < 2:
            print('attack chain broke', file=f)
            break
        print(game.attack(path[i].id, path[i + 1].id, 0, 1),
              path[i].id, path[i + 1].id,
              'troops', path[i].number_of_troops, path[i + 1].number_of_troops,
              file=f)
        gdata.update_game_state()


def plan_attack(game: GameClient | online_src.game.Game, should_fort=True):
    gdata: GameData = game.game_data
    gdata.update_game_state()
    remaining_troops = gdata.remaining_init[gdata.player_id]
    strategic_nodes = [node for node in gdata.nodes if node.owner != gdata.player_id and node.is_strategic]
    my_strategic = [node for node in gdata.nodes if node.owner == gdata.player_id and node.is_strategic]

    # surprise two strategic attack
    if gdata.phase_2_turns > 7 and len(my_strategic) == 2:
        candidate = None
        for node_st1 in strategic_nodes:
            for node_st2 in strategic_nodes:
                attack_plan = get_two_way_attack(gdata, node_st1, node_st2)
                if attack_plan is None:
                    continue
                if candidate is None or candidate[0] < attack_plan[0]:
                    candidate = attack_plan
        if candidate is not None:
            print('attack two strategic', file=f)
            t1, t2 = candidate[4], candidate[5]
            l1, l2 = -candidate[6], -candidate[7]
            remaining_troops = gdata.remaining_init[gdata.player_id]
            if candidate[1] == 0:
                s1: Node = candidate[2]
                s2: Node = candidate[3]
                p1, p2 = 0, 0
                print('needs', l1, l2, file=f)
                tmp = remaining_troops
                while tmp > 0:
                    if l1 < l2:
                        p2 += 1
                        l2 -= 1
                    else:
                        p1 += 1
                        l1 -= 1
                    tmp -= 1
                if p1 > 0:
                    print(game.put_troop(s1.id, p1), s1.id, p1, file=f)
                if p2 > 0:
                    print(game.put_troop(s2.id, p2), s2.id, p2, file=f)
            else:
                s: Node = candidate[2]
                mid: Node = candidate[3]
                if remaining_troops > 0:
                    print(game.put_troop(s.id, remaining_troops), s.id, remaining_troops, file=f)
            gdata.update_game_state()
            game.next_state()

            print('beginning attack', file=f)
            graph = gdata.get_passable_board_graph(gdata.player_id)
            if candidate[1] == 0:
                path1 = [gdata.nodes[x] for x in nx.shortest_path(graph, s1.id, t1.id, weight='weight')]
                path2 = [gdata.nodes[x] for x in nx.shortest_path(graph, s2.id, t2.id, weight='weight')]
                attack_path(game, path1)
                attack_path(game, path2)
            else:
                path = [gdata.nodes[x] for x in nx.shortest_path(graph, s.id, mid.id, weight='weight')]
                attack_path(game, path)
                path1 = [gdata.nodes[x] for x in nx.shortest_path(graph, mid.id, t1.id, weight='weight')]
                path2 = [gdata.nodes[x] for x in nx.shortest_path(graph, mid.id, t2.id, weight='weight')]
                if len(path1) > 1:
                    next_node = path1[1]
                    l1p = max(0, l1 - graph.edges[mid.id, next_node.id])
                    l2p = max(0, l2)
                    print(game.attack(mid.id, next_node.id, 0, l1p / (l1p + l2p) if l1p + l2p > 0 else 0.5),
                          'split attack', file=f)
                    attack_path(game, path1[1:])
                attack_path(game, path2)
            game.next_state()
            # no moving troops
            game.next_state()
            return

    is_last_turn = (game_config['number_of_turns'] - game.get_turn_number()['turn_number'] < 3)
    if is_last_turn and gdata.player_id == 0:
        with open('valad.txt', 'a') as rs:
            print(remaining_troops, len([node for node in gdata.nodes if node.owner == gdata.player_id]), file=rs)
            maximize_score(game, rs)
            print('got them nodes: ', len([node for node in gdata.nodes if node.owner == gdata.player_id]), file=rs)
        return

    # surprise one strategic attack
    max_attack_power, max_path = 0, []
    for st_node in strategic_nodes:
        attack_power, path = get_surprise_danger(
            gdata, st_node, gdata.player_id,
            return_max_path=True, include_src_troops=True
        )
        path: List[Node]
        if len(path) == 0 or attack_power < 1:
            continue
        for node in path:
            node.save_version()
            node.owner = gdata.player_id
            node.number_of_troops = 1

        danger = 1000
        for i in range(0 if path[0].is_strategic else int(attack_power), int(attack_power) + 1):
            path[0].number_of_troops = int(attack_power) - i + 1
            # fort can't be done to all troops according to game rules so in the next line we have 1 + i * 2
            path[-1].number_of_troops = i + 1 if gdata.done_fort else 1 + i * 2
            if path[0].is_strategic:
                danger = min(danger, max(get_node_danger(gdata, path[0]), get_node_danger(gdata, st_node)))
            else:
                danger = min(danger, get_node_danger(gdata, st_node))

        for node in path:
            node.restore_version()
        bypass_danger = len(my_strategic) == 3 and gdata.phase_2_turns > 7

        max_strategics, max_owner = -1, None
        for pi in range(gdata.player_cnt):
            if pi == gdata.player_id:
                continue
            num_stra = len([n for n in strategic_nodes if n.owner == pi])
            if max_strategics < num_stra:
                max_strategics = num_stra
                max_owner = pi
        # last chance before losing
        if gdata.turn_number == 125 and max_strategics >= 4 and max_path[-1].owner == max_owner:
            bypass_danger = True

        if danger > 0 and not bypass_danger:
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
        attack_path(game, max_path)
        game.next_state()

        max_path[0].save_version()
        max_path[-1].save_version()

        if max_path[0].is_strategic and max_path[-1].owner == gdata.player_id:
            troop_cnt = max_path[-1].number_of_troops
            min_danger, move_back = 1000, None
            for i in range(1, troop_cnt + 1):
                max_path[0].number_of_troops = troop_cnt - i + 1
                # same reason as last time we have 2i - 1 in the next line
                max_path[-1].number_of_troops = i if gdata.done_fort else i * 2 - 1

                src_strategic_danger = get_node_danger(gdata, max_path[0])
                target_strategic_danger = get_node_danger(gdata, max_path[-1])

                danger = max(src_strategic_danger,target_strategic_danger)
                if danger < min_danger:
                    min_danger = danger
                    move_back = troop_cnt - i
            if min_danger <= 0 < move_back:
                game.move_troop(max_path[-1].id, max_path[0].id, move_back)
                gdata.update_game_state()
            # Based on higher score
            if min_danger > 0:
                if max_path[0].score_of_strategic > max_path[-1].score_of_strategic:
                    game.move_troop(max_path[-1].id, max_path[0].id, troop_cnt - 1)
                    gdata.update_game_state()


        max_path[0].restore_version()
        max_path[1].restore_version()

        game.next_state()
        if not gdata.done_fort and max_path[-1].owner == gdata.player_id and max_path[-1].number_of_troops > 1:
            danger = get_node_danger(gdata, max_path[-1])
            if danger > 0:
                max_path[-1].save_version()
                max_path[-1].number_of_troops *= 2
                danger = get_node_danger(gdata, max_path[-1])
                max_path[-1].restore_version()
                if danger <= 0 and should_fort:  # TODO tune this based on the risk
                    game.fort(max_path[-1].id, max_path[-1].number_of_troops - 1)
                    gdata.done_fort = True
                    gdata.update_game_state()
        return

    # +3 force attack
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
        troops_to_put = max(0, int(3 - floor(max_score)))
        if troops_to_put > 0:
            print(game.put_troop(src.id, troops_to_put), troops_to_put, src.id, file=f)
        gdata.update_game_state()
        game.next_state()
        print(game.attack(src.id, tar.id, fraction=0, move_fraction=0 if src.is_strategic else 1), file=f)
        gdata.update_game_state()
        game.next_state()
        # no moving troops
        game.next_state()
