from clients.strategy.startegy import *
from clients.utils.attack_chance import get_expected_casualty
from math import floor

from clients.utils.get_possible_danger import get_surprise_danger, get_node_danger


class MessStrategy(Strategy):
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
        return None

    def fortify(self) -> Optional[FortAction]:
        return None

    def compute_plan(self):
        gdata = self.game.game_data

        remaining_troops = gdata.remaining_init[gdata.player_id]
        opposing_players = [i for i in range(gdata.player_cnt) if i != gdata.player_id]

        final_troops_to_put, final_objective, final_path = 0, 0, []
        for player in opposing_players:
            strategics = [node for node in gdata.nodes if node.owner == player and node.is_strategic]
            n_strategics = len(strategics)
            troops_to_put, min_loss, min_path = 0, 1000, []
            for st_node in strategics:
                p_gain = st_node.score_of_strategic
                final_to_place, attack_power, path = 0, 0, []
                for to_place in range(remaining_troops + 1):
                    attack_power, path = get_surprise_danger(
                        gdata, st_node, gdata.player_id,
                        return_max_path=True, include_src_troops=True,
                        put_all_remaining_troops=True,
                        troops_to_put=to_place
                    )
                    final_to_place = to_place
                    # threshold
                    if attack_power > 3:
                        break
                if len(path) == 0:
                    continue
                total_troops_src = final_to_place + path[0].number_of_troops
                loss = total_troops_src - attack_power
                if loss < min_loss:
                    troops_to_put = final_to_place
                    min_loss = loss
                    min_path = path
            if n_strategics > final_objective:
                final_troops_to_put = troops_to_put
                final_objective = n_strategics
                final_path = min_path

        self.attack_path = final_path
        self.troops_to_put = final_troops_to_put
        return len(final_path) > 0
