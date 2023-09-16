# author: Mohamad Mahdi Reisi
import math


# this is one of the most basic components of the Risk game.

class Player:
    def __init__(self, id) -> None:
        self.nodes = []  # list of Node objects that owned by this player
        self.id = id  # each player has an id that is unique in the game
        self.number_of_troops_to_place = 0  # number of troops that the player have but not placed on the map
        self.port = ""  # the port that the player should run a server on it to listen to the requests
        self.ip = ""  # the ip of the player (it used to send requests to the player)
        self.is_ready = False  # a boolean that shows if the player is ready to get requests and play the game or not
        self.token = ''  # a token that is used to show the player that requests are from the game server
        self.use_fort = False  # a boolean that shows if the player used fortify or not

    def get_fort_troops(self):
        return sum([node.number_of_fort_troops for node in self.nodes])

    def get_normal_troops(self):
        return sum([node.number_of_troops for node in self.nodes])

    def get_normal_point(self):
        return math.floor(sum([1 for node in self.nodes if not node.is_strategic]) / 4)

    def get_strat_point(self):
        return sum([node.score_of_strategic for node in self.nodes if node.is_strategic])
