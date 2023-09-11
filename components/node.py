# author: Mohamad Mahdi Reisi
import copy
from typing import List


# this is the most basic component of the Map
# each region is a node, and each node has a list of adjacent nodes in the main map
# each node has an owner, which is a player object.


class Node:
    def __init__(self, id) -> None:
        self.saved = None
        self.id = id # each node has an id that is unique in the game
        self.owner = None # Player object that owns this node
        self.number_of_troops = 0 # number of troops that are placed on this node
        self.number_of_fort_troops = 0 # number of fort troops that are placed on this node
        self.adj_main_map: List[Node] = [] # list of Node objects that are adjacent to this node in the main map
        self.is_strategic = False # if this node is strategic or not
        self.score_of_strategic = 0 # the score of this node if it's strategic

    def save_version(self):
        self.saved = [self.owner, self.number_of_troops, self.number_of_fort_troops]

    def restore_version(self):
        if self.saved is not None:
            self.owner, self.number_of_troops, self.number_of_fort_troops = self.saved
            self.saved = None
