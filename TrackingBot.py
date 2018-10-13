#!/usr/bin/python
import time

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


def find_close_obj(type):
    goal_obj = GameObject(X = 300, Y=300)
    while True:
        for i in range(4):
            GameServer.sendMessage(ServerMessageTypes.TURNTURRETTOHEADING, {'Amount': (i*90)})
            for i in range(5):
                message_type, message = GameServer.readMessage()
                print(message)
                if message_type == ServerMessageTypes.OBJECTUPDATE and message.get("Type") == type:
                    current_obj = GameObject(X=message.get("X"), Y=message.get("Y"))
                    if my_tank.distance_to_object(current_obj)<my_tank.distance_to_object(goal_obj):
                        goal_obj = current_obj
                        print("found closer item", goal_obj)
        if goal_obj.position[0] != 300:
            break
        return goal_obj


def handle_object_update(msg):
    if message_type == ServerMessageTypes.OBJECTUPDATE:
        if args.name == msg.get("Name", "?"):
            my_tank.update(msg)
            if my_tank.health <=2:
                health_pickup = find_close_obj("HealthPickup")
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
