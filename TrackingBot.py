#!/usr/bin/python
from tank_server import *
import logging
import argparse
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


def handle_object_update(msg):
    if message_type == ServerMessageTypes.OBJECTUPDATE:
        if args.name == msg.get("Name", "?"):
            my_tank.update(msg)
        elif msg.get("Type", "") == "Tank":
            target = GameObject(X=msg.get("X"), Y=msg.get("Y"), Id=msg.get("Id"))
            print(my_tank.target_heading(target))
            GameServer.sendMessage(ServerMessageTypes.TURNTURRETTOHEADING, {"Amount": my_tank.target_heading(target)})
            GameServer.sendMessage(ServerMessageTypes.FIRE)
            print("FIRE!")
    else:
        print(message_type)


def handle_kill(msg=""):
    pass


# Main loop - read game messages and point at other tanks
# Event loop takes over the minimum time to complete, so no need to rate limit
my_tank = Player(server=GameServer)
handler_map = {ServerMessageTypes.OBJECTUPDATE: handle_object_update,
               ServerMessageTypes.KILL: handle_kill,
               }
while True:
    message_type, message = GameServer.readMessage()
    try:
        handler_map.get(message_type)(message)
    except TypeError:  # I don't have a function to deal with these events yet, so errors happen
        print(ServerMessageTypes().to_string(message_type))
