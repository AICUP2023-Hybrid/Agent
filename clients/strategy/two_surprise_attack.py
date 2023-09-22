import networkx as nx
from clients.strategy.startegy import *
from clients.strategy.utils.path_attack_sequence import get_one_path_attack_sequence
from clients.utils.get_possible_danger import get_two_way_attack


class TwoSurpriseAttack(Strategy):
    def __init__(self, game: GameClient | Game, condition):
        super().__init__(game)
        self.candidate = None
        self.l1 = 0
        self.l2 = 0
        self.condition = condition

    def put_troops(self) -> List[PutTroopsAction]:
        gdata = self.game.game_data
        candidate = self.candidate
        l1, l2 = -candidate[6], -candidate[7]
        remaining_troops = gdata.remaining_init[gdata.player_id]

        put_troops_action_list = []

        if candidate[1] == 0:
            s1: Node = candidate[2]
            s2: Node = candidate[3]
            p1, p2 = 0, 0
            tmp = remaining_troops
            while tmp > 0:
                if l1 < l2:
                    p2 += 1
                    l2 -= 1
                else:
                    p1 += 1
                    l1 -= 1
                tmp -= 1
            self.l1 = l1
            self.l2 = l2
            if p1 > 0:
                put_troops_action = PutTroopsAction(node=s1, number_of_troops=p1)
                put_troops_action_list.append(put_troops_action)
            if p2 > 0:
                put_troops_action = PutTroopsAction(node=s2, number_of_troops=p2)
                put_troops_action_list.append(put_troops_action)
        else:
            s: Node = candidate[2]
            if remaining_troops > 0:
                put_troops_action = PutTroopsAction(node=s, number_of_troops=remaining_troops)
                put_troops_action_list.append(put_troops_action)
        return put_troops_action_list

    def attacks(self) -> List[AttackAction]:
        gdata = self.game.game_data
        candidate = self.candidate
        attacks = []
        graph = gdata.get_passable_board_graph(gdata.player_id)
        if candidate[1] == 0:
            t1, t2 = candidate[4], candidate[5]
            s1: Node = candidate[2]
            s2: Node = candidate[3]

            path1 = [gdata.nodes[x] for x in nx.shortest_path(graph, s1.id, t1.id, weight='weight')]
            path2 = [gdata.nodes[x] for x in nx.shortest_path(graph, s2.id, t2.id, weight='weight')]
            attacks.extend(get_one_path_attack_sequence(path1))
            attacks.extend(get_one_path_attack_sequence(path2))
        else:
            t1, t2 = candidate[4], candidate[5]
            s: Node = candidate[2]
            mid: Node = candidate[3]

            path = [gdata.nodes[x] for x in nx.shortest_path(graph, s.id, mid.id, weight='weight')]
            attacks.extend(get_one_path_attack_sequence(path))
            path1 = [gdata.nodes[x] for x in nx.shortest_path(graph, mid.id, t1.id, weight='weight')]
            path2 = [gdata.nodes[x] for x in nx.shortest_path(graph, mid.id, t2.id, weight='weight')]
            if len(path1) > 1:
                next_node = path1[1]
                l1p = max(0, self.l1 - graph.edges[mid.id, next_node.id])
                l2p = max(0, self.l2)
                attack = AttackAction(mid.id, next_node, fraction=0,
                                      move_fraction=l1p / (l1p + l2p) if l1p + l2p > 0 else 0.5)
                attacks.append(attack)
                attacks.extend(get_one_path_attack_sequence(path1[1:]))
            attacks.extend(get_one_path_attack_sequence(path2))
        return attacks

    def move_troop(self) -> Optional[MoveTroopAction]:
        return None

    def fortify(self) -> Optional[FortAction]:
        return None

    def compute_plan(self):
        gdata = self.game.game_data

        strategic_nodes = [node for node in gdata.nodes if node.owner != gdata.player_id and node.is_strategic]

        consider_condition = self.condition
        if not consider_condition:
            return False

        for node_st1 in strategic_nodes:
            for node_st2 in strategic_nodes:
                attack_plan = get_two_way_attack(gdata, node_st1, node_st2)
                if attack_plan is None:
                    continue
                if self.candidate is None or self.candidate[0] < attack_plan[0]:
                    self.candidate = attack_plan

        consider_condition = self.candidate is not None
        if not consider_condition:
            return False

        return True
