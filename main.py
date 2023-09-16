# author: Vahid Ghafourian
# Date: 2023/09/06
import math
from typing import List, Any

from Kernel import Kernel
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


def main():
    n_iterations = 1
    for player in range(1):
        wins = [0, 0, 0]
        by_score = [0, 0, 0]
        by_strategic = [0, 0, 0]
        losses_list = []
        for i in tqdm(range(n_iterations)):
            block_print()
            # Creating and running game
            kernel = get_kernel()
            clients = get_clients(kernel, player)
            wp, end_type = run_game(kernel, clients, game_vis_file_name=f'p{player}-game{i}')

            enable_print()
            wins[wp] += 1
            if end_type == 'by_score':
                by_score[wp] += 1
            else:
                by_strategic[wp] += 1
            if wp != player:
                losses_list.append(i)
        print(f'player turn: {player}')
        print(f'lost games: {losses_list}')
        print(f'player names: {", ".join([client.__name__() for client in clients])}')
        print(f'wins: {wins}')
        print(f'by_score: {by_score}')
        print(f'by_strategic: {by_strategic}')


def run_game(kernel, clients, game_vis_file_name=None):
    winning_player, end_type = change_turn(kernel.main_game, *clients,
                                           visualize=game_vis_file_name is not None)
    if game_vis_file_name:
        kernel.main_game.save_gif(game_vis_file_name)
        kernel.main_game.save_mp4(game_vis_file_name)
    return winning_player, end_type


if __name__ == '__main__':
    main()
