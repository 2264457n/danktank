#!/usr/bin/python
import time

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

def need(msg=""):
    print("Hit detected fjdoiregj")
    health_pickup = find_close_obj("HealthPickup")
    GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING,{'Amount': my_tank.target_heading(health_pickup)})
    GameServer.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE,{'Amount': my_tank.distance_to_object(health_pickup)})
    GameServer.sendMessage(ServerMessageTypes.STOPALL)
    return

def find_close_obj(type):
    goal_obj = GameObject(X=1000, Y=1000)
    while True:
        GameServer.sendMessage(ServerMessageTypes.TOGGLETURRETLEFT)
        for i in range(10):
            message_type, message = GameServer.readMessage()
            print(message)
            if message_type == ServerMessageTypes.OBJECTUPDATE and message.get("Type") == type:
                current_obj = GameObject(X=message.get('X'), Y=message.get('Y'))
                if my_tank.distance_to_object(current_obj)<my_tank.distance_to_object(goal_obj):
                    goal_obj = current_obj
                    print("found closer item", goal_obj.position[0])
        GameServer.sendMessage(ServerMessageTypes.STOPTURRET)
        if goal_obj.position[0] != 1000:
            break
    return goal_obj


def handle_object_update(msg):
    if message_type == ServerMessageTypes.OBJECTUPDATE:
        if args.name == msg.get("Name", "?"):
            my_tank.update(msg)
            GameServer.sendMessage(ServerMessageTypes.STOPTURN)

            if my_tank.health <= 2:
                GameServer.sendMessage(ServerMessageTypes.STOPALL)
                health_pickup = find_close_obj("HealthPickup")
                print(health_pickup.position)
                GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {"Amount": my_tank.target_heading(health_pickup)})
                time.sleep(2)
                GameServer.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE, {"Amount": my_tank.distance_to_object(health_pickup)/1.9})
            if my_tank.ammo == 0:
                GameServer.sendMessage(ServerMessageTypes.STOPALL)
                ammo_pickup = find_close_obj("AmmoPickup")
                # print(ammo_pickup.position)
                # GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING,
                #                        {"Amount": my_tank.target_heading(ammo_pickup)})
                # time.sleep(2)
                # GameServer.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE,
                #                        {"Amount": my_tank.distance_to_object(ammo_pickup) / 1.9})
                go_to(ammo_pickup)
        elif msg.get("Type", "") == "Tank":
            target = GameObject(X=msg.get("X"), Y=msg.get("Y"), Id=msg.get("Id"))
            print(my_tank.target_heading(target))
            GameServer.sendMessage(ServerMessageTypes.TURNTURRETTOHEADING, {"Amount": my_tank.target_heading(target)})
            GameServer.sendMessage(ServerMessageTypes.FIRE)
            print("FIRE!")
    else:
        print(message_type)


def handle_kill(msg=""):
    bank()


def go_to(x,y):
    goto_object = GameObject(X = x, Y = y)
    GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING,{'Amount': my_tank.target_heading(goto_object)})
    time.sleep(0.02)
    GameServer.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE, {'Amount': my_tank.distance_to_object(goto_object)})
    return

def go_to_object(obj):
    GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {'Amount': my_tank.target_heading(obj)})
    time.sleep(0.02)
    GameServer.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE, {'Amount': my_tank.distance_to_object(obj)})
    return


def bank():
    blue_goal = GameObject(X=0, Y=120)
    red_goal = GameObject(X=0, Y=-120)
    blue_goal_dist = my_tank.distance_to_object(blue_goal)
    red_goal_dist = my_tank.distance_to_object(red_goal)
    print("Blue goal dist", blue_goal_dist)
    print("Red goal dist", red_goal_dist)
    if blue_goal_dist > red_goal_dist:
        print("We go to the red goal")
        turn_move(my_tank.target_heading(red_goal), red_goal_dist)
        go_to(0,0)

    else:
        print("We go to the blue goal")
        turn_move(my_tank.target_heading(blue_goal), blue_goal_dist)
        go_to(0,0)

def turn_move(heading, distance):
    print("Heading", heading )
    GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {'Amount': heading})
    GameServer.sendMessage(ServerMessageTypes.TURNTURRETTOHEADING, {'Amount': heading})
    GameServer.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE, {'Amount': distance})

def entered_goal(msg=""):
    print("a GOAAAAAL!!!!")
    GameServer.sendMessage(ServerMessageTypes.TOGGLEREVERSE)
    turn_move(180, 30)
    pass

def move(msg=""):
    go_to(20,20)
    go_to(70,-40)
    go_to(70,-20)
    go_to(-40,-50)
    if my_tank.position[1] > 60:
        GameServer.sendMessage(ServerMessageTypes.TOGGLEREVERSE)
    if my_tank.position[1] < -60:
        GameServer.sendMessage(ServerMessageTypes.TOGGLEREVERSE)

    return

def snitch_app(msg=""):
    if message.get('Name') == args.name:
        bank()
    return

def snitch_pickup(msg=""):
    if message_type == ServerMessageTypes.OBJECTUPDATE:
        bank()
    return




# Main loop - read game messages and point at other tanks
# Event loop takes over the minimum time to complete, so no need to rate limit
my_tank = Player(server=GameServer)
handler_map = {ServerMessageTypes.OBJECTUPDATE: handle_object_update,
               ServerMessageTypes.KILL: handle_kill,
               ServerMessageTypes.ENTEREDGOAL: entered_goal,
               ServerMessageTypes.HITDETECTED: need,
               ServerMessageTypes.GAMETIMEUPDATE: move,
               ServerMessageTypes.SNITCHAPPEARED: snitch_app,
               ServerMessageTypes.SNITCHPICKUP: snitch_pickup,
               }
while True:
    message_type, message = GameServer.readMessage()
    try:
        handler_map.get(message_type)(message)
    except TypeError:  # I don't have a function to deal with these events yet, so errors happen
        print(ServerMessageTypes().to_string(message_type))
