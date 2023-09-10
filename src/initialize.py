import json
import requests
from flask import Flask
import random
from src.game import Game
from flask import request
from functools import wraps
from flask import jsonify
from main import turn as player_turn
from main import initializer as player_initializer
import threading
import os
import logging

# read config file from config.json
config = json.load(open('config.json'))

server_ip = config['server_ip']
server_port = config['server_port']

# disable proxy and vpn 
os.environ['NO_PROXY'] = f'{server_ip}'

# make a login request to the server 
try:
    # generate a random password 
    password = int(random.randint(100000, 999999))

    # make a dictionary to send to the server
    login_data = {'token': password}

    # send login data as a form in a POST request
    login_response = requests.request('POST', f'http://{server_ip}:{server_port}/login', data=login_data).json()
except:
    print("the server is not running")
    exit()


try:
    id = login_response['player_id']
    token = login_response['token']
    my_port = login_response['port']
except:
    print('there is a problem in the server response')
    try :
        print(login_response['error'])
    except:
        print("there is no error message in the response")
    exit()


# generate game object
game = Game(token, server_ip, server_port)


# a function to check the password in the x-access-token header
def token_required(func):
    """
    This function is used as a decorator to check the token
    """
    # use wraps to keep the original function name
    @wraps(func)
    def decorator():
        token = None
        output_dict = dict()

        # ensure the jwt-token is passed with the headers
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token: # throw error if no token provided
            output_dict['error'] = 'Token is missing!'
            return jsonify(output_dict), 401

        token = int(token)
        # check if the token is correct
        if token != password:
            output_dict['error'] = 'Invalid token!'
            return jsonify(output_dict), 401
        


        return func()

    return decorator


# make a server to get the start of my turn
app = Flask(__name__)
turn_thread = None

app.logger.propagate = False
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/init', methods=['GET'])
@token_required
def initializer():
    global turn_thread
    game.my_turn = True
    print('initializer started')
    turn_thread = threading.Thread(target=player_initializer, args=(game,))
    turn_thread.start()
    return 'ok'

@app.route('/turn', methods=['GET'])
@token_required
def turn():
    global turn_thread
    game.my_turn = True
    print('turn started')
    turn_thread = threading.Thread(target=player_turn, args=(game,))
    turn_thread.start()
    return 'ok'

@app.route('/end', methods=['GET'])
@token_required
def end_turn():
    print('turn ended')
    game.my_turn = False
    return 'ok'

@app.route('/kill', methods=['GET'])
@token_required
def shutdown():
    print('kill')
    own_pid = os.getpid()
    os.kill(own_pid, 9)
    return 'ok'

def ready():
    resp = requests.request('GET', f'http://{server_ip}:{server_port}/ready', headers={'x-access-token': token})
    code = resp.status_code
    if 200<=code<300:
        print('ready')
    else:
        print(resp.json()['error'])
        print("can't make a ready request")
        exit()

with app.app_context():
    ready()





app.run(debug=True, port=my_port, use_reloader=False, host=config['host'])

