import math

from clients.game_client import GameClient
import random

from clients.stages.attack import plan_attack
from clients.stages.initializer import initialize_turn
from clients.utils.get_possible_danger import get_node_danger


class ClientSalar:

    def __init__(self, kernel, name_id=0) -> None:
        self.flag = False
        self.kernel = kernel
        self.game = self.join_kernel()
        self.non_strategic_node = 0
        self.name_id = name_id
        print(self.kernel.ready(self.game.get_player_id()))

    def join_kernel(self):
        login_response = self.kernel.login()
        id = login_response['player_id']
        # generate game object
        game = GameClient(self.kernel, id)
        return game

    def initializer_turn(self):
        self.game.game_data.update_game_state()

        gdata = self.game.game_data

        # Get the strategic resource
        nodes_sorted = sorted(gdata.nodes, key=lambda x: -x.score_of_strategic)
        for node in nodes_sorted:
            if not node.is_strategic:
                break
            if node.owner is None:
                print(self.game.put_one_troop(node.id), "-- putting one troop on", node.id)
                return

        my_nodes = [
            (node, get_node_danger(self.game.game_data, node))
            for node in nodes_sorted if node.owner == gdata.player_id and node.is_strategic
        ]
        my_nodes = sorted(my_nodes, key=lambda x: -x[1])
        print([(node.id, node.number_of_troops, danger) for node, danger in my_nodes])
        print('complex calculation')
        for node, danger in my_nodes:
            if danger > 0:
                print(self.game.put_one_troop(node.id), "-- putting one troop on", node.id)
                return

        if self.non_strategic_node >= 0:
            return

        for node in nodes_sorted:
            if node.is_strategic:
                continue
            if node.owner is None and get_node_danger(self.game.game_data, node) <= 0:
                print(self.game.put_one_troop(node.id), "-- putting one troop on", node.id)
                return

    def turn(self):
        print('start attack')
        print(self.game.game_data.player_id)
        self.game.game_data.update_game_state()

        gdata = self.game.game_data

        if self.game.player_id != 1:
            # Get the strategic resource
            my_nodes = [
                (node, get_node_danger(gdata, node))
                for node in gdata.nodes if node.owner == gdata.player_id and node.is_strategic
            ]
            my_nodes = sorted(my_nodes, key=lambda x: -x[1])

            for node, danger in my_nodes:
                if danger > 0:
                    troops = min(math.ceil(danger / 2), gdata.remaining_init[gdata.player_id])
                    print(self.game.put_troop(node.id, troops), f"-- putting {troops} troop on {node.id}")
                    break
            plan_attack(self.game, should_fort=False)

            my_nodes = [
                (node, get_node_danger(gdata, node))
                for node in gdata.nodes if node.owner == gdata.player_id and node.is_strategic
            ]
            my_nodes = sorted(my_nodes, key=lambda x: -x[1])
            for node, danger in my_nodes:
                if danger > 0:
                    troops = min(math.ceil(danger / 2), node.number_of_troops)
                    print(self.game.fort(node.id, troops), f"-- forting {troops} troop on {node.id}")
                    break
        else:
            plan_attack(self.game, should_fort=True)

        self.game.game_data.phase_2_turns += 1

    def get_game(self):
        return self.game

    def __name__(self):
        return f"Madar khoda Chad {self.name_id}"
