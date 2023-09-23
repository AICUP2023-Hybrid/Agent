import networkx as nx
import numpy as np

from clients.strategy.startegy import *
from clients.strategy.utils.balance_two_strategic import balance_troops_between_two_strategics
from clients.strategy.utils.choose_fort_nodes import get_fort_from_nodes

from clients.utils.get_possible_danger import get_surprise_danger, get_node_danger


class OneSurpriseAttack(Strategy):
    def __init__(self, game: GameClient | Game):
        super().__init__(game)
        self.troops_to_put = 0
        self.attack_path = None

    def put_troops(self) -> List[PutTroopsAction]:
        put_troops_action = PutTroopsAction(node=self.attack_path[0], number_of_troops=self.troops_to_put)

        return [put_troops_action]

    def attacks(self) -> List[AttackAction]:
        path = self.attack_path
        attack_actions = []
        for i in range(len(path) - 1):
            attack = AttackAction(src=path[i], dest=path[i + 1], fraction=0, move_fraction=1)
            attack_actions.append(attack)
        return attack_actions

    def move_troop(self) -> Optional[MoveTroopAction]:
        gdata = self.game.game_data
        max_path = self.attack_path
        if max_path[0].is_strategic and max_path[-1].owner == gdata.player_id:
            return balance_troops_between_two_strategics(gdata, max_path[-1], max_path[0])

    def fortify(self) -> Optional[FortAction]:
        gdata = self.game.game_data
        max_path = self.attack_path
        return get_fort_from_nodes(gdata, [max_path[0], max_path[-1]])

    def get_scenario_danger(self, path: List[Node], attack_power: int, strategic_src_matter=True):
        gdata = self.game.game_data
        src, tar = path[0], path[-1]
        for node in path:
            node.save_version()
            node.owner = gdata.player_id
            node.number_of_troops = 1
        danger = np.Inf
        if not src.is_strategic or not strategic_src_matter:
            tar.number_of_troops = int(attack_power if gdata.done_fort else 2 * attack_power - 1)
            danger = min(danger, get_node_danger(gdata, tar))
        else:
            danger = min(danger, balance_troops_between_two_strategics(gdata, tar, src, return_danger=True)[1])

        for node in path:
            node.restore_version()
        return danger

    # TODO define some theoretical basis for this
    def calculate_gain(self, opposition):
        gdata = self.game.game_data
        other_opposition = [i for i in range(3) if i != opposition and i != gdata.player_id][0]
        player_troop_gains = [0, 0, 0]
        for node in gdata.nodes:
            if node.owner is None:
                continue
            player_troop_gains[node.owner] += node.score_of_strategic + 0.25
        for i in range(3):
            player_troop_gains[i] = int(player_troop_gains[i])
        if min(player_troop_gains[gdata.player_id] * 1.5, 10) < player_troop_gains[opposition]:
            if player_troop_gains[other_opposition] - player_troop_gains[gdata.player_id] > 3:
                return 0.25
            else:
                return 0.75
        return 0.5

    def get_trade_off_score(self, path: List[Node], attack_power: int):
        # it should be a little higher because trade off is a risky move
        if attack_power < 2:  # TODO tune the safety threshold for attack power
            return -np.Inf
        danger = self.get_scenario_danger(path, attack_power, strategic_src_matter=False)
        if danger > 0:
            return -np.Inf
        src, tar = path[0], path[-1]
        return tar.score_of_strategic * (1 + self.calculate_gain(tar.owner)) - src.score_of_strategic

    def get_hold_score(self, path: List[Node], attack_power: int):
        if attack_power < 2:  # TODO tune the safety threshold for attack power
            return -np.Inf
        danger = self.get_scenario_danger(path, attack_power, strategic_src_matter=True)
        if danger > 0:
            return -np.Inf
        tar = path[-1]
        return tar.score_of_strategic * (1 + self.calculate_gain(tar.owner))

    def check_attack_pairs(self, max_troops_to_put=None):
        gdata = self.game.game_data
        graph = gdata.get_passable_board_graph(gdata.player_id)
        strategic_nodes = [node for node in gdata.nodes if node.owner != gdata.player_id and node.is_strategic]
        troops_to_put = gdata.remaining_init[gdata.player_id]
        if max_troops_to_put is not None:
            troops_to_put = min(troops_to_put, max_troops_to_put)

        trade_off_plan = (None, (-np.Inf, -np.Inf, -np.Inf))
        hold_plan = (None, (-np.Inf, -np.Inf, -np.Inf))
        for target in strategic_nodes:
            paths = nx.shortest_path(graph, target=target.id, weight='weight')
            paths_length = nx.shortest_path_length(graph, target=target.id, weight='weight')
            for src in [n for n in gdata.nodes if n.owner in [gdata.player_id, None] and n.id in paths]:
                attack_power = src.number_of_troops + troops_to_put - paths_length[src.id]
                path = [gdata.nodes[x] for x in paths[src.id]]
                trade_off_score = self.get_trade_off_score(path, attack_power)
                hold_score = self.get_hold_score(path, attack_power)
                if trade_off_score != -np.Inf:
                    score = (trade_off_score, -paths_length[src.id], attack_power)
                    if trade_off_plan[1] < score:
                        trade_off_plan = (path, score)
                if hold_score != -np.Inf:
                    score = (hold_score, -paths_length[src.id], attack_power)
                    if hold_plan[1] < score:
                        hold_plan = (path, score)
        return trade_off_plan, hold_plan

    def check_only_capture_attack(self, bypass_by_owner=None):
        gdata = self.game.game_data
        strategic_nodes = [node for node in gdata.nodes if node.owner != gdata.player_id and node.is_strategic]

        max_attack_power, max_path = 0, None
        for st_node in strategic_nodes:
            attack_power, path = get_surprise_danger(
                gdata, st_node, gdata.player_id,
                return_max_path=True, include_src_troops=True
            )
            if len(path) == 0:
                continue
            if bypass_by_owner is not None and path[-1].owner != bypass_by_owner:
                continue
            if max_attack_power < attack_power:
                max_attack_power = attack_power
                max_path = path
        return max_path, max_attack_power

    def compute_plan(self, attempt=0):
        gdata = self.game.game_data
        strategic_nodes = [node for node in gdata.nodes if node.owner != gdata.player_id and node.is_strategic]
        my_strategic = [node for node in gdata.nodes if node.owner == gdata.player_id and node.is_strategic]

        bypass_danger = len(my_strategic) == 3 and gdata.turn_number >= 126
        max_strategics, max_owner = -1, None
        for pi in range(gdata.player_cnt):
            if pi == gdata.player_id:
                continue
            num_stra = len([n for n in strategic_nodes if n.owner == pi])
            if max_strategics < num_stra:
                max_strategics = num_stra
                max_owner = pi
        # last chance before losing
        if gdata.turn_number >= 124 and max_strategics >= 4:
            bypass_danger = True

        chosen_plan = (None, (-np.Inf, -np.Inf, -np.Inf))
        if bypass_danger:
            chosen_plan = self.check_only_capture_attack(
                bypass_by_owner=max_owner if max_strategics >= 4 else None
            )
        else:
            plans = self.check_attack_pairs(gdata.remaining_init[gdata.player_id])
            for plan in plans:
                if plan[0] is not None and chosen_plan[1] < plan[1]:
                    chosen_plan = plan
        self.troops_to_put = gdata.remaining_init[gdata.player_id]
        self.attack_path = chosen_plan[0]
        return self.attack_path is not None
