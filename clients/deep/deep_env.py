from typing import Optional

import gym
import networkx as nx
import numpy as np

from clients.client_ai import ClientAi
from clients.game_client import GameClient
from clients.stages.initializer import initialize_turn
from clients.utils.update_details import GameData
from env import GameEnv


class DummyClient:

    def __init__(self, kernel, name_id=0) -> None:
        self.flag = False
        self.kernel = kernel
        self.game = self.join_kernel()
        self.game.ai_client = self
        self.name_id = name_id
        print(self.kernel.ready(self.game.get_player_id()))

    def join_kernel(self):
        login_response = self.kernel.login()
        id = login_response['player_id']
        # generate game object
        game = GameClient(self.kernel, id)
        return game

    def initializer_turn(self):
        # print('start')
        initialize_turn(self.game)
        self.game.next_state()

    def __name__(self):
        return f"Aggressive Chad {self.name_id}"


class OnePlayerEnv(gym.Env):

    def __init__(self, player_id):
        clients = [ClientAi, ClientAi, ClientAi]
        clients[player_id] = DummyClient
        self.env = GameEnv(clients)
        self.player_id = player_id
        self.game_data: Optional[GameData] = None

    def reset(self, seed=None, options=None):
        self.env.reset()
        self.game_data: GameData = self.env.clients[self.player_id].game.game_data
        i = 1
        while i != self.player_id:
            i = (i + 1) % 3
            self.env.step()
        self.env.start_step()
        return self._get_obs(), self._get_info()

    def step(self, action):
        # convert action to real chain of actions and perform it?

        self.env.end_step()

        is_finished, index, end_type = self.env.step()
        if not is_finished:
            is_finished, index, end_type = self.env.step()

        self.env.start_step()

        reward = 0
        if is_finished and index == self.player_id:
            reward = 10000
        return self._get_obs(), reward, is_finished, False, self._get_info()

    def _get_obs(self):
        gdata = self.game_data

        # assuming each strategic has an owner
        final_graph = nx.DiGraph()
        for i in range(gdata.player_cnt):
            final_graph.add_node(-i - 1)  # a node representing all non-strategic nodes for player
        for node in gdata.get_strategic_nodes():
            final_graph.add_node(node.id)
        # TODO number of source troops matter!
        for pid in range(3):
            pgraph = gdata.get_passable_board_graph(pid)
            for dst in gdata.get_strategic_nodes():
                lengths = nx.shortest_path_length(pgraph, target=dst.id, weight='weight')
                for src in gdata.get_strategic_nodes(player_id=pid):
                    if src.id in lengths:
                        final_graph.add_edge(src.id, dst.id, weight=lengths[src.id])
                empty_node_weight = np.Inf
                for src in [n for n in gdata.nodes if n.owner is None]:
                    empty_node_weight = min(lengths[src.id], empty_node_weight)
                if empty_node_weight != np.Inf:
                    final_graph.add_edge(-pid - 1, dst.id, weight=empty_node_weight)

    def _get_info(self):
        return {"turn_number": self.env.game.turn_number}

    def render(self):
        self.env.render(0)