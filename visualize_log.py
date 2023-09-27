import json

import numpy as np
import requests
import sys

from components.game import Game
from offline_main import read_config

responses = []
if sys.argv[1] == '-f':
    responses = [('local', 'map4.json', json.load(open(sys.argv[2])))]
elif sys.argv[1] == '-g':
    game_id = int(sys.argv[2])
    api_url = 'https://api.aicup2023.ir/api/match/'
    auth = 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjk1ODQzMDM2LCJpYXQiOjE2OTU3NTY2MzYsImp0aSI6ImNhZDgxZjkyZGUwMTRjYzdhOGRkYzExOGRhMDRjM2I4IiwidXNlcl9pZCI6MTIzNH0.7P5fu2d1TYXCkoRMjFgbKFB5nOZWI4cgb6BhtLYUm1M'
    games = requests.get(api_url, headers={'Authorization': auth}).json()
    game = games[len(games) - game_id]
    matches = game['sub_matches']
    for i, match in enumerate(matches):
        mx_score = max(match[f'team{i}_score'] for i in range(1, 4))
        my_score = [match[f'team{i}_score'] for i in range(1, 4) if match[f'team{i}'] == 'Hybrid'][0]
        s = 'loss'
        print(mx_score, my_score)
        if mx_score == my_score:
            s = 'win'
        log_url = match['game_log']
        responses.append((f'{game_id}-{i + 1}-{s}', game['map_name'], requests.get(log_url).json()))
else:
    log_url = sys.argv[1]
    map = sys.argv[2]
    responses = [('spec', map, requests.get(log_url).json())]


for game_id, map, response in responses:
    game = Game()
    game.read_map(f'./maps/{map}')
    game.config = read_config()

    for i in range(3):
        game.add_player(i)
        game.players[i].number_of_troops_to_place = game.config['initial_troop']
        game.player_id = i

    init_data = response['initialize']
    turns_data = sorted(response['turns'].items())
    game.initialize_visualization(*[response['team_names'][i] for i in [1, 2, 0]])
    winner = np.argmax(response['score'])

    last_ind = 0
    for _ in range(1, 106):
        player_id = game.start_turn()
        player = game.players[player_id]
        if last_ind < len(init_data) and player_id == init_data[last_ind][0]:
            node = game.nodes[init_data[last_ind][1]]
            node.number_of_troops += 1
            player.number_of_troops_to_place -= 1
            node.owner = player
            if node not in player.nodes:
                player.nodes.append(node)
            last_ind += 1
        game.end_turn()
        # game.visualize(False, None, None)

    for ti, (turn, data) in enumerate(turns_data):
        owners = data['nodes_owner']
        troops = data['troop_count']
        for _, player in game.players.items():
            player.nodes = []
        for node_id in range(len(owners)):
            node = game.nodes[node_id]
            if owners[node_id] != -1:
                node.owner = game.players[owners[node_id]]
                game.players[node.owner.id].nodes.append(node)
            node.number_of_troops = troops[node_id]

        player_id = game.start_turn()
        player = game.players[player_id]
        for item in data['add_troop']:
            node_id, troop_cnt = item
            player.number_of_troops_to_place -= troop_cnt
            game.nodes[node_id].number_of_troops += troop_cnt
            game.nodes[node_id].owner = player
            if game.nodes[node_id] not in player.nodes:
                player.nodes.append(game.nodes[node_id])

        game.log_attack = data['attack']
        game.end_turn()
        game.visualize(ti == len(turns_data) - 1, winner, None)

        forts = data['fort']
        for node_id in range(len(owners)):
            node = game.nodes[node_id]
            node.number_of_fort_troops = forts[node_id]

        for item in data['attack']:
            target = item['target']
            new_owner = item['new_target_owner']
            if new_owner == player_id:
                player.number_of_troops_to_place += read_config()['number_of_troops_after_successful_attack']
                break

    game.save_gif(f'{game_id}')
    game.save_mp4(f'{game_id}')


