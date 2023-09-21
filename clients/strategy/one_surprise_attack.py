from clients.strategy.startegy import *
from clients.strategy.utils.balance_two_strategic import balance_troops_between_two_strategics
from clients.strategy.utils.choose_fort_nodes import get_fort_from_nodes
from clients.utils.attack_chance import get_expected_casualty
from math import floor

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

    def compute_plan(self):
        gdata = self.game.game_data

        remaining_troops = gdata.remaining_init[gdata.player_id]
        strategic_nodes = [node for node in gdata.nodes if node.owner != gdata.player_id and node.is_strategic]
        my_strategic = [node for node in gdata.nodes if node.owner == gdata.player_id and node.is_strategic]

        max_attack_power, max_path = 0, []
        for st_node in strategic_nodes:
            attack_power, path = get_surprise_danger(
                gdata, st_node, gdata.player_id,
                return_max_path=True, include_src_troops=True
            )
            path: List[Node]
            if len(path) == 0 or attack_power < 1:
                continue
            for node in path:
                node.save_version()
                node.owner = gdata.player_id
                node.number_of_troops = 1

            danger = 1000
            for i in range(0 if path[0].is_strategic else int(attack_power), int(attack_power) + 1):
                path[0].number_of_troops = int(attack_power) - i + 1
                # fort can't be done to all troops according to game rules so in the next line we have 1 + i * 2
                path[-1].number_of_troops = i + 1 if gdata.done_fort else 1 + i * 2
                if path[0].is_strategic:
                    danger = min(danger, max(get_node_danger(gdata, path[0]), get_node_danger(gdata, st_node)))
                else:
                    danger = min(danger, get_node_danger(gdata, st_node))

            for node in path:
                node.restore_version()
            bypass_danger = len(my_strategic) == 3 and gdata.phase_2_turns > 7

            max_strategics, max_owner = -1, None
            for pi in range(gdata.player_cnt):
                if pi == gdata.player_id:
                    continue
                num_stra = len([n for n in strategic_nodes if n.owner == pi])
                if max_strategics < num_stra:
                    max_strategics = num_stra
                    max_owner = pi
            # last chance before losing
            if gdata.turn_number >= 124 and max_strategics >= 4 and path[-1].owner == max_owner:
                bypass_danger = True
            if path[-1].owner != max_owner and gdata.turn_number >= 124 and max_strategics >= 4:
                continue

            if danger > 0 and not bypass_danger:
                continue

            if max_attack_power < attack_power:
                max_attack_power = attack_power
                max_path = path
        self.attack_path = max_path
        self.troops_to_put = remaining_troops
        return len(max_path) > 0