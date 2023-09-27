from typing import Optional

from Kernel import Kernel
from clients.client_ai import ClientAi
from clients.client_enemy_two import ClientEnemyTwo
from components.game import Game
import json
import os

from turn_controllers import check_finish, calculate_score

kernel_config = None


def read_config():
    global kernel_config
    if kernel_config is None:
        with open('config.json', 'r') as f:
            config = json.load(f)
        kernel_config = config
    return kernel_config


class GameEnv:

    def __init__(self, clients_classes):
        self.clients_classes = clients_classes
        self.clients = None
        self.game: Optional[Game] = None

    def reset(self):
        global kernel_config
        kernel_main_game = Game()
        kernel_main_game.read_map('./maps/map3.json')
        read_config()
        kernel = Kernel(kernel_main_game, kernel_config)

        clients = [client(kernel, i) for i, client in enumerate(self.clients_classes)]
        kernel.main_game.team_names = [client.__name__() for client in clients]
        kernel.main_game.game_id = 0
        self.game = kernel.main_game
        self.clients = clients
        while self.game.turn_number < 105:
            player_id = self.game.start_turn()
            self.clients[player_id].initializer_turn()
            self.game.end_turn()

    def start_step(self):
        if self.game.turn_number < 105:
            raise Exception("the step function is called before initialization")
        return self.game.start_turn()

    def end_step(self):
        self.game.end_turn()
        # check if the game is finished
        is_finished, index, end_type = check_finish(self.game, enable_logs=False)
        return is_finished, index, end_type

    def step(self):
        player_id = self.start_step()
        # wait for the player to play
        if self.game.game_state == 2:
            self.clients[player_id].turn()
        return self.end_step()

    def render(self, game_id):
        if not os.path.exists("log"):
            os.makedirs("log")

        # add score the log file
        self.game.log["score"] = calculate_score(self.game)
        self.game.log["team_names"] = self.game.team_names

        # generate and save the main_game.log file into a json file in the log folder
        with open(f"log/{game_id}.json", "w") as log_file:
            json.dump(self.game.log, log_file)
