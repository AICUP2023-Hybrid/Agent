# author: Vahid Ghafourian
# Date: 2023/09/06
import math
import random
from multiprocessing import Pool
from typing import List, Any
from tqdm.contrib.concurrent import process_map
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


def get_clients(kernel, player_turn: int) -> List[Any]:
    # Build Enemy clients
    clients = []
    for i in range(3):
        if player_turn == i:
            clients.append(ClientAi(kernel))
        else:
            clients.append(ClientEnemyTwo(kernel))
    return clients


def get_clients_random(kernel, *args, **kwargs):
    clients = list(enumerate([ClientEnemyTwo, ClientAi, ClientEnemyTwo]))

    random.shuffle(clients)

    return [client(kernel, i) for i, client in clients]


def get_kernel():
    # ask player to choose map from the list of maps
    maps = os.listdir('maps')

    kernel_main_game = Game()
    # get the selected map from the player
    selected_map = '3'  # str(random.choice(list(range(1, 5))))

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


def get_score_by_client(score: dict):
    return "\n".join([f"{k}: {v}" for k, v in sorted(score.items(), key=lambda x: x[0])])


def do(i):
    block_print()
    # Creating and running game
    kernel = get_kernel()
    clients = get_clients_random(kernel)
    wp, end_type = run_game(kernel, clients)  #, f'game{i}')

    enable_print()
    return wp, end_type, [client.__name__() for client in clients]


def main():
    n_iterations = 100
    wins = defaultdict(lambda: 0)
    total_by_pos = defaultdict(lambda: [0, 0, 0])
    wins_by_pos = defaultdict(lambda: [0, 0, 0])
    by_score = defaultdict(lambda: [0, 0, 0])
    by_strategic = defaultdict(lambda: [0, 0, 0])
    losses_list = []
    for wp, end_type, client_names in process_map(do, range(n_iterations), max_workers=8):
        wins[client_names[wp]] += 1
        wins_by_pos[client_names[wp]][wp] += 1
        if end_type == 'by_score':
            by_score[client_names[wp]][wp] += 1
        else:
            by_strategic[client_names[wp]][wp] += 1
        for pos, client_name in enumerate(client_names):
            total_by_pos[client_name][pos] += 1

    print(f'---wins---\n{get_score_by_client(wins)}')
    print('---by player results---')
    client_names = sorted([item[0] for item in total_by_pos.items()])
    win_percentage_by_pos = {
        name: [round(wins_by_pos[name][i] / max(1, total_by_pos[name][i]), ndigits=2) for i in range(3)]
        for name in client_names
    }
    print("{:<15} {:<20} {:<20} {:<20}".format(*([''] + client_names)))
    for row_name, dct in [
        ('wins', wins_by_pos), ('by_score', by_score),
        ('by_strategic', by_strategic), ('total', total_by_pos),
        ('win_percentage', win_percentage_by_pos)
    ]:
        print("{:<15} {:<20} {:<20} {:<20}".format(
            *([row_name] + [str(dct[name]) for name in client_names])
        ))


def run_game(kernel, clients, game_vis_file_name=None):
    winning_player, end_type = change_turn(kernel.main_game, *clients,
                                           visualize=game_vis_file_name is not None)
    if game_vis_file_name:
        kernel.main_game.save_gif(game_vis_file_name)
        kernel.main_game.save_mp4(game_vis_file_name)
    return winning_player, end_type


if __name__ == '__main__':
    main()
