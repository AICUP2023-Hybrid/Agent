import dataclasses
from abc import abstractmethod
from typing import List, Optional

from components.node import Node


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

    @abstractmethod
    def put_troops(self) -> List[PutTroopsAction]:
        pass

    @abstractmethod
    def attack(self) -> List[AttackAction]:
        pass

    @abstractmethod
    def move_troop(self) -> Optional[MoveTroopAction]:
        pass

    @abstractmethod
    def fortify(self) -> Optional[FortAction]:
        pass
