from clients.strategy.startegy import *
from clients.utils.attack_chance import get_expected_casualty, get_expected_casualty_by_troops, get_win_rate
from math import floor


class Plus3Strategy(Strategy):
    def __init__(self, game: GameClient | Game):
        super().__init__(game)
        self.troops_to_put = 0
        self.src = None
        self.tar = None

    def put_troops(self) -> List[PutTroopsAction]:
        put_troops_action = PutTroopsAction(node=self.src, number_of_troops=self.troops_to_put)

        return [put_troops_action]

    def attacks(self) -> List[AttackAction]:
        attack = AttackAction(src=self.src, dest=self.tar, fraction=0,
                              move_fraction=0.001 if self.src.is_strategic else 0.999)
        return [attack]

    def move_troop(self) -> Optional[MoveTroopAction]:
        return None

    def fortify(self) -> Optional[FortAction]:
        return None

    def compute_plan(self, attempt=0):
        gdata = self.game.game_data
        # +3 force attack
        max_score, src, tar, src_troops_to_put = 0, None, None, 0

        max_range = 1
        if attempt == 0:
            max_range = 4
        elif attempt == 1:
            max_range = 1

        for node in gdata.nodes:
            if node.owner not in [gdata.player_id, None]:
                continue
            if node.is_strategic:
                continue  # don't ruin the available paths
            for troops_to_put in range(max_range):
                for nei in node.adj_main_map:
                    if nei.owner not in [None, gdata.player_id]:
                        attacking_troops = node.number_of_troops + troops_to_put
                        defending_troops = nei.number_of_troops + nei.number_of_fort_troops
                        if defending_troops > 5:  # speed up
                            continue
                        attacking_troops = min(attacking_troops, 8)  # speed up
                        casualty = get_expected_casualty_by_troops(attacking_troops, defending_troops) + 1
                        new_troop_remain = troops_to_put - max(0, casualty - node.number_of_troops)
                        loss = casualty + 0.15 * new_troop_remain
                        if 3 - loss < max_score:  # speed up
                            continue
                        win_prob = get_win_rate(attacking_troops, defending_troops)
                        score = win_prob * 3 - loss
                        if max_score < score:
                            src_troops_to_put = troops_to_put
                            max_score = score
                            src = node
                            tar = nei
        self.troops_to_put = src_troops_to_put
        self.src = src
        self.tar = tar
        return tar is not None
