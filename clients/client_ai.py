# author: Vahid Ghafourian
# Date: 2023/09/06

from clients.game_client import GameClient
import random

from clients.stages.attack import plan_attack
from clients.stages.initializer import initialize_turn


class ClientAi:
    def __init__(self, kernel) -> None:
        self.flag = False
        self.kernel = kernel
        self.game = self.join_kernel()
        print(self.kernel.ready(self.game.get_player_id()))

    def join_kernel(self):
        login_response = self.kernel.login()
        id = login_response['player_id']
        # generate game object
        game = GameClient(self.kernel, id)
        return game

    def initializer_turn(self):
        print('start')
        initialize_turn(self.game)

    def turn(self):
        print('start attack')
        print(self.game.game_data.player_id)
        plan_attack(self.game)

    def get_game(self):
        return self.game