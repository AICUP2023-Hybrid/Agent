import json
import online_src
from clients.game_client import GameClient
from clients.strategy.one_surprise_attack import OneSurpriseAttack
from clients.strategy.plus3_strategy import Plus3Strategy
from clients.strategy.two_surprise_attack import TwoSurpriseAttack
from clients.utils.maximize_score import maximize_score
from clients.utils.update_details import GameData
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
    condition = (gdata.phase_2_turns > 7 and len(my_strategic) == 2)
    two_surprise_attack_strategy = TwoSurpriseAttack(game, condition)
    shall_pass = two_surprise_attack_strategy.compute_plan()
    if shall_pass:
        two_surprise_attack_strategy.run_strategy()
        return

    # "get much as territory when last player in last round" strategy
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
