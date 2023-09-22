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
                              move_fraction=0 if self.src.is_strategic else 1)
        return [attack]

    def move_troop(self) -> Optional[MoveTroopAction]:
        return None

    def fortify(self) -> Optional[FortAction]:
        return None

    def compute_plan(self):
        gdata = self.game.game_data
        # +3 force attack
        max_score, src, tar, src_troops_to_put = 0, None, None, 0
        for node in gdata.nodes:
            if node.owner not in [gdata.player_id, None]:
                continue
            for troops_to_put in range(4):
                for nei in node.adj_main_map:
                    if nei.owner not in [None, gdata.player_id]:
                        attacking_troops = node.number_of_troops + troops_to_put
                        defending_troops = nei.number_of_troops + nei.number_of_fort_troops
                        casualty = get_expected_casualty_by_troops(attacking_troops, defending_troops) + 1
                        win_prob = get_win_rate(attacking_troops, defending_troops)
                        loss = casualty + 0.3 * troops_to_put
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
