import networkx as nx
import numpy as np

from clients.strategy.startegy import *
from clients.strategy.utils.balance_two_strategic import balance_troops_between_two_strategics, \
    check_balance_two_strategic_possible
from clients.strategy.utils.choose_fort_nodes import get_fort_from_nodes
from clients.utils.algorithms import binary_search, balance_two_nodes_binary_search
from clients.utils.attack_chance import get_expected_casualty, get_win_rate, get_attack_outcomes, MAX_TROOP_CALC

from clients.utils.get_possible_danger import get_surprise_danger, get_node_danger


class OneSurpriseAttack(Strategy):
    def __init__(self, game: GameClient | Game):
        super().__init__(game)
        self.max_loss_cache = dict()
        self.can_move = None
        self.can_fort = None
        self.troops_to_put = 0
        self.attack_path = None

    def put_troops(self) -> List[PutTroopsAction]:
        put_troops_action = PutTroopsAction(node=self.attack_path[0], number_of_troops=self.troops_to_put)

        return [put_troops_action]

    def attacks(self) -> List[AttackAction]:
        path = self.attack_path
        attack_actions = []
        for i in range(len(path) - 1):
            attack = AttackAction(src=path[i], dest=path[i + 1], fraction=0, move_fraction=0.999)
            attack_actions.append(attack)
        return attack_actions

    def move_troop(self) -> Optional[MoveTroopAction]:
        if not self.can_move:
            return None
        gdata = self.game.game_data
        max_path = self.attack_path
        if max_path[0].is_strategic and max_path[-1].owner == gdata.player_id and len(max_path) > 1:
            return balance_troops_between_two_strategics(gdata, max_path[-1], max_path[0])

    def fortify(self) -> Optional[FortAction]:
        if not self.can_fort:
            return None
        gdata = self.game.game_data
        max_path = self.attack_path
        if len(max_path) == 1:
            return get_fort_from_nodes(gdata, [max_path[0]])
        return get_fort_from_nodes(gdata, [max_path[0], max_path[-1]])

    # TODO define some theoretical basis for this
    def calculate_gain(self, opposition):
        gdata = self.game.game_data
        if opposition == gdata.player_id:
            return 0
        p_gains = gdata.get_players_troop_gain()
        other_opposition = [i for i in range(3) if i != opposition and i != gdata.player_id][0]

        my_gain, op_gain, oop_gain = [
            p_gains[x] for x in [gdata.player_id, opposition, other_opposition]
        ]
        if min(my_gain * 1.5, 10) < op_gain and gdata.phase_2_turns > 1:
            if oop_gain - my_gain > 3:
                return 0
            elif my_gain - oop_gain > 4:
                return 0.8
            else:
                return 0.5
        return 0.5

    def get_loss_node_gain_by_player(self, target: Node, player):
        gdata = self.game.game_data
        attack_power, max_path = get_surprise_danger(
            gdata, target, player, include_src_troops=True, return_max_path=True
        )
        if attack_power <= 0:
            return 0
        for node in max_path:
            node.save_version()
            node.owner = player
            node.number_of_troops = 1
            if node.id != max_path[0].id:
                node.number_of_fort_troops = 0
        win_prob = 1 - get_attack_outcomes(max_path)[0]
        score = 0
        # revert this at the end!
        original_init = gdata.remaining_init[gdata.player_id]
        gdata.remaining_init[gdata.player_id] = gdata.get_players_troop_gain()[gdata.player_id]
        if max_path[0].is_strategic:
            danger = balance_troops_between_two_strategics(gdata, max_path[0], max_path[-1], return_danger=True)[1]
            if danger <= 0:
                score = win_prob * target.score_of_strategic
            else:
                target.number_of_troops = round(
                    attack_power if gdata.players_done_fort[player] else 2 * attack_power - 1
                )
                if get_node_danger(gdata, target) <= 0:
                    score = win_prob * (target.score_of_strategic - max_path[0].score_of_strategic)
        if not max_path[0].is_strategic:
            target.number_of_troops = round(attack_power if gdata.players_done_fort[player] else 2 * attack_power - 1)
            if get_node_danger(gdata, target) <= 0:
                score = win_prob * target.score_of_strategic
        gain = self.calculate_gain(player)
        for node in max_path:
            node.restore_version()
        gdata.remaining_init[gdata.player_id] = original_init
        return max(score, 0) * gain

    def get_max_loss_node(self, node: Node):
        gdata = self.game.game_data
        return max(
            self.get_loss_node_gain_by_player(node, i) for i in range(3) if i != gdata.player_id
        )

    def get_general_attack_score(self, path: List[Node], troops_to_put):
        if path[-1].id == 33:
            if path[0].id == 32:
                tmp = 0
            if path[0].id == 27:
                tmp = 1
        gdata = self.game.game_data
        score = 0
        src, tar = path[0], path[-1]
        src_danger = get_node_danger(gdata, src)

        src.number_of_troops += troops_to_put
        outcomes = get_attack_outcomes(path)
        # print(outcomes[:3])
        first_win_prob = 1 - get_attack_outcomes([path[0], path[1]])[0] if len(path) > 1 else 0
        score += 1. * first_win_prob  # no +3 strategic
        src.number_of_troops -= troops_to_put

        # TODO we can add +3 troops on successfully attacking to score too
        loss_gain_src = 0
        if src.is_strategic:
            if src.id not in self.max_loss_cache:
                self.max_loss_cache[src.id] = self.get_max_loss_node(src)
            loss_gain_src = self.max_loss_cache[src.id]

        tar_gain = tar.score_of_strategic * self.calculate_gain(tar.owner)

        attack_force = path[0].number_of_troops + troops_to_put
        for node in path:
            node.save_version()
            node.owner = gdata.player_id
            node.number_of_troops = 1
            if node.id != path[0].id:
                node.number_of_fort_troops = 0
        if src.is_strategic and src_danger <= 0:  # case of loss outcome = 0
            score -= outcomes[0] * (src.score_of_strategic + loss_gain_src)

        if len(path) == 1:
            if not src.is_strategic or src_danger <= 0:
                score += 0
            else:
                src.number_of_troops = attack_force
                if self.can_fort and not gdata.done_fort:
                    src.number_of_troops *= 2
                    src.number_of_troops -= 1
                danger = get_node_danger(gdata, src)
                if danger <= 0:
                    score += 1. * (src.score_of_strategic + loss_gain_src)
            for node in path:
                node.restore_version()
            # print(f'src: {src.score_of_strategic}, tar: {tar.score_of_strategic} -> {score}')
            return score

        # TODO can move and can fort should be accounted for here
        MAX_NUM = min(MAX_TROOP_CALC, attack_force + 1)
        max_check = MAX_NUM

        def two_nodes_danger_func(remaining_troops: int):
            if remaining_troops == 0:
                return False
            tar.number_of_troops = remaining_troops
            return check_balance_two_strategic_possible(gdata, tar, src, can_fort=self.can_fort)

        if src.is_strategic and tar.is_strategic:  # holding both
            max_check = binary_search(0, max_check, two_nodes_danger_func, left_value=False)
            for i in range(max_check, MAX_NUM):
                prob = outcomes[i]
                score += prob * (tar.score_of_strategic + tar_gain)  # holding new strategic
                score += prob * (
                        src.score_of_strategic + loss_gain_src
                ) if src_danger > 0 else 0  # saving old strategic

        # either save src or target
        def can_save_node(remaining_troops: int, save_node: Node, danger_on_one_troop):
            if remaining_troops == 0:
                return False
            exp = get_expected_casualty()
            save_node.number_of_troops = remaining_troops
            if self.can_fort and not gdata.done_fort:
                save_node.number_of_troops *= 2
                save_node.number_of_troops -= 1
            d = danger_on_one_troop + exp[node.number_of_fort_troops + 1]
            d -= exp[node.number_of_fort_troops + node.number_of_troops]
            return d <= 0

        src_one_troop_danger = get_node_danger(gdata, src)
        save_src_troops = binary_search(
            0, max_check, can_save_node, False, save_node=src, danger_on_one_troop=src_one_troop_danger
        ) if src.is_strategic else MAX_NUM

        tar_one_troop_danger = get_node_danger(gdata, tar)
        save_tar_troops = binary_search(
            0, max_check, can_save_node, False, save_node=tar, danger_on_one_troop=tar_one_troop_danger
        ) if tar.is_strategic else MAX_NUM

        if src.score_of_strategic < tar.score_of_strategic:
            save_tar_range = (save_tar_troops, max_check)
            save_src_range = (min(save_src_troops, save_tar_troops), save_tar_troops)
        else:
            save_src_range = (save_src_troops, max_check)
            save_tar_range = (min(save_src_troops, save_tar_troops), save_src_troops)

        for i in range(save_tar_range[0], save_tar_range[1]):  # save target
            prob = outcomes[i]
            score += prob * (tar.score_of_strategic + tar_gain)
            if src.is_strategic and src_danger <= 0:
                score -= prob * (src.score_of_strategic + loss_gain_src)

        for i in range(save_src_range[0], save_src_range[1]):  # save src
            prob = outcomes[i]
            score += prob * tar_gain
            if src.is_strategic and src_danger > 0:
                score += prob * (src.score_of_strategic + loss_gain_src)

        for i in range(1, min(save_src_troops, save_tar_troops, max_check)):  # can't save anything
            prob = outcomes[i]
            score += prob * tar_gain
            if src.is_strategic and src_danger <= 0:
                score -= prob * (src.score_of_strategic + loss_gain_src)

        for node in path:
            node.restore_version()

        #print(f'src: {src.score_of_strategic} [{src.id}], tar: {tar.score_of_strategic} [{tar.id}] -> {score} /'
        #      f' {src.number_of_troops + troops_to_put} - {tar.number_of_troops + tar.number_of_fort_troops}')
        return score

    def check_attack_pairs(self, max_troops_to_put=None):
        gdata = self.game.game_data
        graph = gdata.get_passable_board_graph(gdata.player_id)
        strategic_nodes = [node for node in gdata.nodes if node.owner != gdata.player_id and node.is_strategic]
        troops_to_put = gdata.remaining_init[gdata.player_id]
        if max_troops_to_put is not None:
            troops_to_put = min(troops_to_put, max_troops_to_put)

        plan = (None, (-np.Inf, -np.Inf, -np.Inf))

        for target in strategic_nodes:
            paths = nx.shortest_path(graph, target=target.id, weight='weight')
            paths_length = nx.shortest_path_length(graph, target=target.id, weight='weight')
            for src in [n for n in gdata.nodes if n.owner in [gdata.player_id, None] and n.id in paths]:
                attack_power = src.number_of_troops + troops_to_put - paths_length[src.id]
                path = [gdata.nodes[x] for x in paths[src.id]]
                score = self.get_general_attack_score(path, troops_to_put)
                score = (score, -paths_length[src.id], attack_power)
                if plan[1] < score:
                    plan = (path, score)

        for src in [n for n in gdata.nodes if n.owner == gdata.player_id and n.is_strategic]:
            paths = nx.shortest_path(graph, source=src.id, weight='weight')
            paths_length = nx.shortest_path_length(graph, source=src.id, weight='weight')
            for target in [
                n for n in gdata.nodes
                # already check other strategics
                if n.owner not in [gdata.player_id, None] and n.id in paths and not n.is_strategic
            ]:
                if paths_length[target.id] > 3:
                    continue
                attack_power = src.number_of_troops + troops_to_put - paths_length[target.id]
                path = [gdata.nodes[x] for x in paths[target.id]]
                score = self.get_general_attack_score(path, troops_to_put)
                score = (score, -paths_length[target.id], attack_power)
                if plan[1] < score:
                    plan = (path, score)

            attack_power = src.number_of_troops + troops_to_put
            score = self.get_general_attack_score([src], troops_to_put)
            score = (score, 0, attack_power)
            if plan[1] < score:
                plan = ([src], score)

        return plan

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

    def compute_plan(self, attempt=0, can_move=True, can_fort=True):
        gdata = self.game.game_data
        self.can_move = can_move
        self.can_fort = can_fort
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

        chosen_plan = (None, (0, -np.Inf, -np.Inf))
        if bypass_danger:
            chosen_plan = self.check_only_capture_attack(
                bypass_by_owner=max_owner if max_strategics >= 4 else None
            )
        else:
            chosen_plan = self.check_attack_pairs(gdata.remaining_init[gdata.player_id])
            if chosen_plan[1][0] < 1:
                chosen_plan = (None, (0, -np.Inf, -np.Inf))
        self.troops_to_put = gdata.remaining_init[gdata.player_id]
        self.attack_path = chosen_plan[0]
        return self.attack_path is not None
