import time
from queue import Queue
from tank_server import *
import logging
import argparse
import random
from tanks import GameObject, Player

# Parse command line args
parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
parser.add_argument('-H', '--hostname', default='127.0.0.1', help='Hostname to connect to')
parser.add_argument('-p', '--port', default=8052, type=int, help='Port to connect to')
parser.add_argument('-n', '--name', default='TrackingBot', help='Name of bot')
args = parser.parse_args()

# Set up console logging
if args.debug:
    logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.DEBUG)
else:
    logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.INFO)

# Connect to game server
GameServer = ServerComms(args.hostname, args.port)

# Spawn our tank
logging.info("Creating tank with name '{}'".format(args.name))
GameServer.sendMessage(ServerMessageTypes.CREATETANK, {'Name': args.name})

my_tank = Player(server=GameServer)

def check_state():
    last_seen_health = None
    last_seen_ammo = None
    while True:
        msg_type, msg = GameServer.readMessage()#Read messages until my_tank can be updated
        try:
            if args.name == msg.get("Name", "?"):
                my_tank.update(msg)
                break
        except:
            continue
    if my_tank.health <= 2:
    #Execute code to go to last seen health from movement
        print("Low health!")
    if my_tank.ammo == 0:
    #Execute code to go to last seen ammo from movement
        print("No ammo!")


