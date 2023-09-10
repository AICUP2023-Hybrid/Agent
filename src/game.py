import requests

class Game:
    def __init__(self, token, server_ip, server_port) -> None:
        self.token = token
        self.server_ip = server_ip
        self.server_port = server_port
        self.my_turn = False
    
    def handel_output(self, response):
        code = response.status_code
        if 200<=code<300:
            return eval(response.text)
        if 'error' in response.json():
            print(response.json()['error'])
            raise Exception(response.json()['error'])
        else:
            print("unknown error")
            raise Exception("unknown error")
        
    def get_owners(self):
        """
            returns a dictionary of node_id: owner_id
            node_id: str
            owner_id: int
        """
        try:
            resp = requests.request('GET', f'http://{self.server_ip}:{self.server_port}/get_owners', headers={'x-access-token': self.token})
        except:
            print("can't make request")
            return
        return self.handel_output(resp)
    
    def get_number_of_troops(self):
        """
            returns a dictionary of node_id: number_of_troops
            node_id: str
            number_of_troops: int
        """
        try:
            resp = requests.request('GET', f'http://{self.server_ip}:{self.server_port}/get_troops_count', headers={'x-access-token': self.token})
        except:
            print("can't make request")
            return
        return self.handel_output(resp)
    
    def get_state(self):
        """
            returns a dictionary containing the state of the game 
            1: put_troop
            2: attack
            3: move_troop
            4: fort 
            {'state': number_of_state}
        """
        try:
            resp = requests.request('GET', f'http://{self.server_ip}:{self.server_port}/get_state', headers={'x-access-token': self.token})
        except:
            print("can't make request")
            return

        return self.handel_output(resp)

    def get_turn_number(self):
        """
            returns a dictionary containing the turn number
            {'turn_number': number_of_turn}
        """
        try:
            resp = requests.request('GET', f'http://{self.server_ip}:{self.server_port}/get_turn_number', headers={'x-access-token': self.token})
        except:
            print("can't make request")
            return
        return self.handel_output(resp)

    def get_adj(self):
        """
            return the adjacent nodes of each node
            returns a dictionary of node_id: [adjacent_nodes]
            node_id: str
            adjacent_nodes: list of int
        """
        try:
            resp = requests.request('GET', f'http://{self.server_ip}:{self.server_port}/get_adj', headers={'x-access-token': self.token})
        except:
            print("can't make request")
            return
        return self.handel_output(resp)
    
    def next_state(self):
        """
            changes the state of the turn to the next state
        """
        try:
            resp = requests.request('GET', f'http://{self.server_ip}:{self.server_port}/next_state', headers={'x-access-token': self.token})
        except:
            print("can't make request")
            return
        return self.handel_output(resp)
    
    def put_one_troop(self, node_id):
        """
            puts one troop in the node with the given id 
            this function can only be used in the put_troop state in the initialize function
        """
        body = {
            'node_id': node_id
        }
        try:
            resp = requests.request('POST', f'http://{self.server_ip}:{self.server_port}/put_one_troop', headers={'x-access-token': self.token}, data=body)
        except:
            print("can't make request")
            return {}
        return self.handel_output(resp)
    
    def put_troop(self, node_id, num):
        """
            puts num troops in the node with the given id
            this function can only be used in the put_troop state in the turn function
        """
        body = {
            'node_id': node_id,
            'number_of_troops': num
        }
        try:
            resp = requests.request('POST', f'http://{self.server_ip}:{self.server_port}/put_troop', headers={'x-access-token': self.token}, data=body)
        except:
            print("can't make request")
            return {}
        return self.handel_output(resp)

    def get_player_id(self):
        """
            returns the id of the player
        """
        try:
            resp = requests.request('GET', f'http://{self.server_ip}:{self.server_port}/get_player_id', headers={'x-access-token': self.token})
        except:
            print("can't make request")
            return
        return self.handel_output(resp)
    
    def attack(self, attacking_id, target_id, fraction, move_fraction):
        """
            attacks the target node with the given fraction of troops
        """
        body = {
            'attacking_id': attacking_id,
            'target_id': target_id,
            'fraction': fraction,
            'move_fraction': move_fraction
        }
        try:
            resp = requests.request('POST', f'http://{self.server_ip}:{self.server_port}/attack', headers={'x-access-token': self.token}, data=body)
        except:
            print("can't make request")
            return {}
        return self.handel_output(resp)
    
    def move_troop(self, source, destination, troop_count):
        """
            moves the given number of troops from the source node to the destination node
        """
        body = {
            'source': source,
            'destination': destination,
            'troop_count': troop_count
        }
        try:
            resp = requests.request('POST', f'http://{self.server_ip}:{self.server_port}/move_troop', headers={'x-access-token': self.token}, data=body)
        except:
            print("can't make request")
            return {}
        return self.handel_output(resp)
    
    def get_strategic_nodes(self):
        """
            returns a list of strategic nodes and their score
            {"strategic_nodes": [node_id, ...], "score": [score, ...]}
        """
        try:
            resp = requests.request('GET', f'http://{self.server_ip}:{self.server_port}/get_strategic_nodes', headers={'x-access-token': self.token})
        except:
            print("can't make request")
            return
        return self.handel_output(resp)
    
    def get_number_of_troops_to_put(self):
        """
            returns the number of troops that the player can put in the put_troop state
            {"number_of_troops": number_of_troops}
        """
        try:
            resp = requests.request('GET', f'http://{self.server_ip}:{self.server_port}/get_number_of_troops_to_put', headers={'x-access-token': self.token})
        except:
            print("can't make request")
            return
        return self.handel_output(resp)
    
    def get_reachable(self, node_id):
        """
            returns a dictionary of "reachable" key and a list of reachable nodes
            {"reachable": [node_id, ...]}
        """
        body = {
            'node_id': node_id
        }
        try:
            resp = requests.request('POST', f'http://{self.server_ip}:{self.server_port}/get_reachable', headers={'x-access-token': self.token}, data=body)
        except:
            print("can't make request")
            return {}
        return self.handel_output(resp)
    
    def get_number_of_fort_troops(self):
        """
            returns the number of troops that used to defend the node
            {node_id: number_of_troops, ...}
            node_id: str
            number_of_troops: int
        """
        try:
            resp = requests.request('GET', f'http://{self.server_ip}:{self.server_port}/get_number_of_fort_troops', headers={'x-access-token': self.token})
        except:
            print("can't make request")
            return
        return self.handel_output(resp)

    def fort(self, node_id, troop_count):
        """
            fortifies the node with the given number of troops
        """
        body = {
            'node_id': node_id,
            'troop_count': troop_count
        }
        try:
            resp = requests.request('POST', f'http://{self.server_ip}:{self.server_port}/fort', headers={'x-access-token': self.token}, data=body)
        except:
            print("can't make request")
            return {}
        return self.handel_output(resp)