import json
import online_src
from clients.game_client import GameClient
from clients.strategy.mess_strategy import MessStrategy
from clients.strategy.one_surprise_attack import OneSurpriseAttack
from clients.strategy.plus3_strategy import Plus3Strategy
from clients.strategy.two_surprise_attack import TwoSurpriseAttack
from clients.utils.maximize_score import maximize_score
from clients.utils.update_details import GameData
game_config = json.load(open('config.json', 'r'))


def plan_attack(game: GameClient | online_src.game.Game):
    gdata: GameData = game.game_data
    gdata.update_game_state()
    my_strategic = [node for node in gdata.nodes if node.owner == gdata.player_id and node.is_strategic]

    # surprise two strategic attack
    condition = (gdata.phase_2_turns > 7 and len(my_strategic) >= 2)
    two_surprise_attack_strategy = TwoSurpriseAttack(game, condition)
    shall_pass = two_surprise_attack_strategy.compute_plan()
    if shall_pass:
        two_surprise_attack_strategy.run_strategy()
        return

    # "get much as territory when last player in last round" strategy
    is_last_turn = (game_config['number_of_turns'] - game.get_turn_number()['turn_number'] < 3)
    if is_last_turn and gdata.player_id == 0:
        maximize_score(game)
        return

    # surprise one strategic attack
    one_surprise_attack_strategy = OneSurpriseAttack(game)
    shall_pass = one_surprise_attack_strategy.compute_plan()
    if shall_pass:
        one_surprise_attack_strategy.run_strategy()
        return

    # mess with the opposition
    mess_strategy = MessStrategy(game)
    shall_pass = mess_strategy.compute_plan()
    if shall_pass:
        mess_strategy.run_strategy()
        return

    # +3 force attack
    plus3_strategy = Plus3Strategy(game)
    plus3_strategy.run_strategy_until_success()
