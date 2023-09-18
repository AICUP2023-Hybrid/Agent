import random

from clients.stages.attack import plan_attack
from clients.stages.initializer import initialize_turn
from online_src.game import Game

flag = False


def initializer(game: Game):
    initialize_turn(game)
    game.next_state()


def turn(game):
    game.game_data.stage = 1
    plan_attack(game)
    game.game_data.phase_2_turns += 1
    game.next_state()
