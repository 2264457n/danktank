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
parser.add_argument('-n', '--name', default='TrackingBot2', help='Name of bot')
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


def check_state(last_seen_health, last_seen_ammo):
    for i in range (50):
        msg_type, msg = GameServer.readMessage()  # Read messages until my_tank can be updated
    while True:
        msg_type, msg = GameServer.readMessage()#Read messages until my_tank can be updated
        logging.info(msg)
        try:
            if args.name == msg.get("Name", "?"):
                my_tank.update(msg)
                print("Health:", my_tank.health)
                break
        except:
            continue
    if my_tank.health <= 2:
    #Execute code to go to last seen health from movement
        print("Low health!")
        if last_seen_health == None:
            snake()
        else:
            GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {"Amount": my_tank.target_heading(last_seen_health)})
            time.sleep(2)
            GameServer.sendMessage(ServerMessageTypes.TOGGLEFORWARD)
            time.sleep(5)
    elif my_tank.ammo == 0:
    #Execute code to go to last seen ammo from movement
        print("No ammo!")
        if last_seen_health == None:
            snake()
        else:
            GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING,
                                   {"Amount": my_tank.target_heading(last_seen_health)})
            time.sleep(2)
            GameServer.sendMessage(ServerMessageTypes.TOGGLEFORWARD)
            time.sleep(5)
    else:
        snake()

def snake():
    last_seen_ammo = None
    last_seen_health = None
    GameServer.sendMessage(ServerMessageTypes.TOGGLEFORWARD)
    GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {'Amount': random.randint(0,360)})
    GameServer.sendMessage(ServerMessageTypes.TOGGLETURRETLEFT)
    while True:
        msg_type, msg = GameServer.readMessage()  # Read messages until my_tank can be updated
        try:
            if msg_type == ServerMessageTypes.OBJECTUPDATE and msg.get("Type") == "HealthPickup":
                last_seen_health = GameObject(X=msg.get("X"), Y=msg.get("Y"), Id=msg.get("Id"))
            if msg_type == ServerMessageTypes.OBJECTUPDATE and msg.get("Type") == "AmmoPickup":
                last_seen_ammo = GameObject(X=msg.get("X"), Y=msg.get("Y"), Id=msg.get("Id"))
            if last_seen_health != None and last_seen_ammo != None:
                break
        except:
            continue
    time.sleep(4)
    GameServer.sendMessage(ServerMessageTypes.STOPALL)
    check_state(last_seen_health, last_seen_ammo)

while True:
    check_state(None, None)

