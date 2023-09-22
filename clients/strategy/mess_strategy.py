import numpy as np

from clients.strategy.startegy import *
from clients.strategy.utils.balance_two_strategic import balance_troops_between_two_strategics
from clients.strategy.utils.path_attack_sequence import get_one_path_attack_sequence
from clients.utils.attack_chance import get_expected_casualty
from clients.utils.get_possible_danger import get_surprise_danger, get_min_loss_path


class MessStrategy(Strategy):
    def __init__(self, game: GameClient | Game):
        super().__init__(game)
        self.troops_to_put = 0
        self.attack_path = None

    def put_troops(self) -> List[PutTroopsAction]:
        return [PutTroopsAction(node=self.attack_path[0], number_of_troops=self.troops_to_put)]

    def attacks(self) -> List[AttackAction]:
        return get_one_path_attack_sequence(self.attack_path)

    def move_troop(self) -> Optional[MoveTroopAction]:
        gdata = self.game.game_data
        attack_path = self.attack_path
        if attack_path[0].is_strategic and attack_path[-1].owner == gdata.player_id:
            return balance_troops_between_two_strategics(gdata, attack_path[-1], attack_path[0])

    def fortify(self) -> Optional[FortAction]:
        return None

    def compute_plan(self):
        gdata = self.game.game_data

        remaining_troops = gdata.remaining_init[gdata.player_id]
        opposing_players = [i for i in range(gdata.player_cnt) if i != gdata.player_id]

        final_troops_to_put, target_n_strategics, target_troop_gain, final_path = 0, 0, 0, []
        for player in opposing_players:
            strategics = [node for node in gdata.nodes if node.owner == player and node.is_strategic]
            player_troop_gain = 0
            for node in strategics:
                player_troop_gain += node.score_of_strategic
            player_troop_gain += len([node for node in gdata.nodes if node.owner == player]) // 4
            n_strategics = len(strategics)

            troops_to_put, best_score, best_path = 0, 0, []
            attack_power_threshold = 3
            for st_node in strategics:
                final_to_place, loss, path = 0, np.Inf, []
                for to_place in range(remaining_troops + 1):
                    loss, path = get_min_loss_path(
                        gdata, st_node, gdata.player_id,
                        max_troops_to_put=to_place,
                        attack_power_threshold=attack_power_threshold
                    )
                    final_to_place = to_place
                    # threshold
                    if len(path) > 0:
                        break
                if len(path) == 0:
                    continue

                # +3 for troops gain after attack
                p_gain = st_node.score_of_strategic * 0.75
                score = p_gain - loss + 3 - attack_power_threshold
                if best_score <= score:
                    troops_to_put = final_to_place
                    best_score = score
                    best_path = path

            if n_strategics > target_n_strategics or (
                    n_strategics == target_n_strategics and player_troop_gain > target_troop_gain
            ):
                final_troops_to_put = troops_to_put
                target_n_strategics = n_strategics
                target_troop_gain = player_troop_gain
                final_path = best_path

        self.attack_path = final_path
        self.troops_to_put = final_troops_to_put
        return len(final_path) > 0
