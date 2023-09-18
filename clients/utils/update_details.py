from typing import List

import networkx as nx
import math
import numpy as np

from clients.game_client import GameClient
from clients.utils.attack_chance import get_expected_casualty
from components.node import Node
from collections import defaultdict
import online_src


class GameData:
    def __init__(self, game: GameClient | online_src.game.Game):
        self.nodes: List[Node] = []
        self.player_id = None
        self.player_cnt = 3
        self.game = game
        self.remaining_init = [35, 35, 35]
        self.later_added = [0,0,0]
        self.stage = 0
        self.phase_2_turns = 1
        self.done_fort = False

    def update_game_state(self):
        if len(self.nodes) == 0:
            self.player_id = self.game.get_player_id()

            adjs = [z[1] for z in sorted(self.game.get_adj().items(), key=lambda x: int(x[0]))]
            for i in range(len(adjs)):
                node = Node(i)
                self.nodes.append(node)
            for idx, adj in enumerate(adjs):
                for adj_idx in adj:
                    self.nodes[idx].adj_main_map.append(self.nodes[adj_idx])

            strategic_data = self.game.get_strategic_nodes()
            strategic_nodes = strategic_data['strategic_nodes']
            scores = strategic_data['score']
            strategic_nodes = list(zip(strategic_nodes, scores))
            for node, score in strategic_nodes:
                self.nodes[node].is_strategic = True
                self.nodes[node].score_of_strategic = score

        for node_idx_str, owner_id in self.game.get_owners().items():
            self.nodes[int(node_idx_str)].owner = owner_id if owner_id != -1 else None

        for node_idx_str, troops_cnt in self.game.get_number_of_troops().items():
            self.nodes[int(node_idx_str)].number_of_troops = troops_cnt

        for node_idx_str, troops_cnt in self.game.get_number_of_fort_troops().items():
            self.nodes[int(node_idx_str)].number_of_fort_troops = troops_cnt

        if self.stage == 0:
            self.remaining_init = [35, 35, 35]
            for node in self.nodes:
                if node.owner is None:
                    continue
                self.remaining_init[node.owner] -= node.number_of_troops
        else:
            self.remaining_init = [0, 0, 0]
            self.remaining_init[self.player_id] = self.game.get_number_of_troops_to_put()['number_of_troops']
            # TODO calculate other players troop count

    def update_remaining_troops_by_map(self):
        n_nodes_belonging = defaultdict(lambda: 0)
        for node in self.nodes:
            if node.owner is None:
                continue
            n_nodes_belonging[node.owner] += 1
        n_strategic_belonging = defaultdict(lambda: 0)
        for node in self.nodes:
            if node.is_strategic and node.owner is not None:
                n_strategic_belonging[node.owner] += node.score_of_strategic
        for i in range(self.player_cnt):
            if i == self.player_id:
                continue
            self.later_added[i] = n_nodes_belonging[i] // 4 + n_strategic_belonging[i]
            self.remaining_init[i] = self.later_added[i]  # temporary substitute for remaining troops

    def get_board_graph(self) -> nx.DiGraph:
        graph: nx.DiGraph = nx.DiGraph()
        expected_casualty = get_expected_casualty()

        for node in self.nodes:
            graph.add_node(node)
        for node in self.nodes:
            for nei in node.adj_main_map:
                graph.add_edge(node.id, nei.id,
                               weight=1 + expected_casualty[nei.number_of_troops + nei.number_of_fort_troops])
        return graph

    def get_passable_board_graph(self, player) -> nx.DiGraph:
        graph: nx.DiGraph = nx.DiGraph()
        expected_casualty = get_expected_casualty()

        for node in self.nodes:
            graph.add_node(node.id)
        for node in self.nodes:
            for nei in node.adj_main_map:
                weight = 1 + expected_casualty[nei.number_of_troops + nei.number_of_fort_troops]
                if nei.owner in [player, None]:
                    continue
                graph.add_edge(node.id, nei.id, weight=weight)
        return graph

