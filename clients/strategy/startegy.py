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

    def run_strategy(self):
        gdata = self.game.game_data
        for put_troop in self.put_troops():
            self.game.put_troop(put_troop.node.id, put_troop.number_of_troops)

        gdata.update_game_state()
        self.game.next_state()

        for attack in self.attacks():
            if attack.src.owner != self.game.game_data.player_id or attack.src.number_of_troops < 2:
                print('attack chain broke', file=f)
                continue
            self.game.attack(attack.src.id, attack.dest.id, attack.fraction, attack.move_fraction)
            gdata.update_game_state()

        self.game.next_state()

        move_troops = self.move_troop()
        if move_troops:
            self.game.move_troop(move_troops.src.id, move_troops.dest.id, move_troops.count)

        gdata.update_game_state()
        self.game.next_state()

        fortify = self.fortify()
        if fortify:
            self.game.fort(fortify.node.id, fortify.count)

        gdata.update_game_state()
        self.game.next_state()
