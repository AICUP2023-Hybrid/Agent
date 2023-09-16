# author: Vahid Ghafourian
# Date: 2023/09/06
import math
import random
from typing import List, Any

from Kernel import Kernel
from clients.salar.SalarAgent import ClientSalar
from components.game import Game
from clients.client_ai import ClientAi
import networkx as nx
import matplotlib.pyplot as plt
from clients.client_enemy_one import ClientEnemyOne
from clients.client_enemy_two import ClientEnemyTwo
from turn_controllers import change_turn
from collections import defaultdict
import sys, os
from tqdm import tqdm

import json


def read_config():
    with open('config.json', 'r') as f:
        config = json.load(f)
    return config


# Disable
def block_print():
    sys.stdout = open(os.devnull, 'w')


# Restore
def enable_print():
    sys.stdout = sys.__stdout__


def get_clients_specific(kernel, client, player_turn: int) -> List[Any]:
    # Build Enemy clients
    clients = []
    for i in range(3):
        if player_turn == i:
            clients.append(client(kernel))
        else:
            clients.append(ClientEnemyTwo(kernel))
    return clients


def get_clients_random(kernel, *args, **kwargs):
    clients = [ClientEnemyTwo, ClientAi, ClientSalar]

    random.shuffle(clients)

    return [client(kernel) for client in clients]


def get_kernel():
    # ask player to choose map from the list of maps
    maps = os.listdir('maps')

    kernel_main_game = Game()
    # get the selected map from the player
    selected_map = '3'

    while selected_map.isdigit() is False or int(selected_map) >= len(maps) or int(selected_map) < 0:
        # show the list of maps from the maps folder
        print("Choose a map from the list of maps:")
        for i, map in enumerate(maps):
            print(i, '-', map)
        selected_map = input("Enter the number of the map you want to choose: ")

    # read the selected map
    kernel_main_game.read_map('maps/' + maps[int(selected_map)])

    # read config
    kernel_config = read_config()

    # Build Kernel
    return Kernel(kernel_main_game, kernel_config)


def get_score_by_client(d: dict):
    return "\n".join([f"{k}:\t{v}" for k, v in d.items()])


def main():
    n_iterations = 1000
    for player in range(1):
        wins_by_pos = defaultdict(lambda: [0, 0, 0])
        wins = defaultdict(lambda: 0)
        by_score = defaultdict(lambda: 0)
        by_strategic = defaultdict(lambda : 0)
        losses_list = []
        for i in tqdm(range(n_iterations)):
            block_print()
            # Creating and running game
            kernel = get_kernel()
            clients = get_clients_random(kernel, player)
            wp, end_type = run_game(kernel, clients)

            enable_print()
            wins[clients[wp].__name__()] += 1
            wins_by_pos[clients[wp].__name__()][wp] += 1
            if end_type == 'by_score':
                by_score[clients[wp].__name__()] += 1
            else:
                by_strategic[clients[wp].__name__()] += 1
            if wp != player:
                losses_list.append(i)
        print(f'player turn: {player}')
        print(f'lost games: {losses_list}')
        print(f'---wins---\n{get_score_by_client(wins)}')
        print(f'---wins by pos---\n{get_score_by_client(wins_by_pos)}')
        print(f'---by score---\n{get_score_by_client(by_score)}')
        print(f'---by strategic---\n{get_score_by_client(by_strategic)}')


def run_game(kernel, clients, game_vis_file_name=None):
    winning_player, end_type = change_turn(kernel.main_game, *clients,
                                           visualize=game_vis_file_name is not None)
    if game_vis_file_name:
        kernel.main_game.save_gif(f'{game_vis_file_name}.gif')
        kernel.main_game.save_mp4(f'{game_vis_file_name}.gif', f'{game_vis_file_name}.mp4')
    return winning_player, end_type


if __name__ == '__main__':
    main()
