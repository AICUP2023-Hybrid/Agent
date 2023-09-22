import dataclasses
from abc import abstractmethod
from typing import List, Optional

from components.node import Node

from clients.game_client import GameClient
from online_src.game import Game

f = open(f'log0.txt', 'w')


@dataclasses.dataclass
class PutTroopsAction:
    node: Node
    number_of_troops: int


@dataclasses.dataclass
class AttackAction:
    src: Node
    dest: Node
    fraction: float
    move_fraction: float


@dataclasses.dataclass
class MoveTroopAction:
    src: Node
    dest: Node
    count: int


@dataclasses.dataclass
class FortAction:
    node: Node
    count: int


class Strategy:
    def __init__(self, game: GameClient | Game):
        self.game = game

    @abstractmethod
    def put_troops(self) -> List[PutTroopsAction]:
        pass

    @abstractmethod
    def attacks(self) -> List[AttackAction]:
        pass

    @abstractmethod
    def move_troop(self) -> Optional[MoveTroopAction]:
        pass

    @abstractmethod
    def fortify(self) -> Optional[FortAction]:
        pass

    @abstractmethod
    def compute_plan(self):
        pass

    def run_put_troops_strategy(self, go_next_state=True):
        gdata = self.game.game_data
        remaining_troops = gdata.game.get_number_of_troops_to_put()['number_of_troops']
        for put_troop in self.put_troops():
            if put_troop.number_of_troops > 0:
                self.game.put_troop(put_troop.node.id,
                                    min(remaining_troops, put_troop.number_of_troops))

        gdata.update_game_state()
        if go_next_state:
            self.game.next_state()

    def run_attack_strategy(self, go_next_state=True):
        gdata = self.game.game_data
        attack_succeeded = True
        for attack in self.attacks():
            if attack.src.owner != self.game.game_data.player_id or attack.src.number_of_troops < 2:
                print('attack chain broke', file=f)
                attack_succeeded = False
                continue
            self.game.attack(attack.src.id, attack.dest.id, attack.fraction, attack.move_fraction)
            gdata.update_game_state()

        if go_next_state:
            self.game.next_state()
        return attack_succeeded

    def run_move_troops_strategy(self, go_next_state=True):
        gdata = self.game.game_data
        move_troops = self.move_troop()
        if move_troops:
            self.game.move_troop(move_troops.src.id, move_troops.dest.id, move_troops.count)

        gdata.update_game_state()

        if go_next_state:
            self.game.next_state()

    def run_fortify_strategy(self, go_next_state=True):
        gdata = self.game.game_data
        fortify = self.fortify()
        if fortify:
            self.game.fort(fortify.node.id, fortify.count)
            gdata.done_fort = True

        gdata.update_game_state()

        if go_next_state:
            self.game.next_state()

    def run_strategy(self):
        self.run_put_troops_strategy(go_next_state=True)

        self.run_attack_strategy(go_next_state=True)

        self.run_move_troops_strategy(go_next_state=True)

        self.run_fortify_strategy(go_next_state=True)
