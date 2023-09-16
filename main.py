# author: Vahid Ghafourian
# Date: 2023/09/06
import math

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


def main():
    n_iterations = 1
    for player in range(1):
        wins = [0, 0, 0]
        by_score = [0, 0, 0]
        by_strategic = [0, 0, 0]
        for i in tqdm(range(n_iterations)):
            block_print()
            wp, end_type = run_game(player)
            enable_print()
            wins[wp] += 1
            if end_type == 'by_score':
                by_score[wp] += 1
            else:
                by_strategic[wp] += 1
        print(f'results when player turn is {player}: {wins}')
        print(f'by_score results when player turn is {player}: {by_score}')
        print(f'by_strategic results when player turn is {player}: {by_strategic}')


def run_game(player_turn):
    # read map file
    kernel_main_game = Game()
    # ask player to choose map from the list of maps
    maps = os.listdir('maps')

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
    kernel = Kernel(kernel_main_game, kernel_config)

    #Build Enemy clients
    clients = []
    for i in range(3):
        if player_turn == i:
            clients.append(ClientAi(kernel))
        else:
            clients.append(ClientAi(kernel))

    winning_player, end_type = change_turn(kernel.main_game, *clients,
                                           visualize=True)
    return winning_player, end_type


if __name__ == '__main__':
    main()
