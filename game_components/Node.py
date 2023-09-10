class Node:
    def __init__(self, idx):
        self.id = idx  # each node has an id that is unique in the game
        self.owner = None  # Player object that owns this node
        self.number_of_troops = 0  # number of troops that are placed on this node
        self.number_of_fort_troops = 0  # number of fort troops that are placed on this node
        self.adj_main_map = []  # list of Node objects that are adjacent to this node in the main map
        self.is_strategic = False  # if this node is strategic or not
        self.score_of_strategic = 0  # the score of this node if it's strategic
