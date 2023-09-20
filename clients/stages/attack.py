import json
from math import floor, ceil
from typing import List

import networkx as nx

import online_src
from clients.game_client import GameClient
from clients.strategy.one_surprise_attack import OneSurpriseAttack
from clients.strategy.plus3_strategy import Plus3Strategy
from clients.strategy.startegy import Strategy
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
    one_surprise_attack_strategy = OneSurpriseAttack(game)
    shall_pass = one_surprise_attack_strategy.compute_plan()
    if shall_pass:
        one_surprise_attack_strategy.run_strategy()
        return

    # +3 force attack
    plus3_strategy = Plus3Strategy(game)
    shall_pass = plus3_strategy.compute_plan()
    if shall_pass:
        plus3_strategy.run_strategy()
        return
