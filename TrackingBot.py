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


def find_close_obj(obj_type):  # Only handles turret movement, not tracks
    goal_obj = GameObject(X=1000, Y=1000)
    while True:
        time.sleep(0.05)
        ServerComms.sendMessage(message_type=ServerMessageTypes.TOGGLETURRETLEFT)
        time.sleep(3)  # Scan for 3 seconds
        seen_items = []
        while True:
            message_type, message = GameServer.readMessage()
            if message_type == ServerMessageTypes.OBJECTUPDATE and message.get("Type") == obj_type:
                current_obj = GameObject(X=message.get('X'), Y=message.get('Y'), Id=message.get("Id"))
                if current_obj not in seen_items:
                    seen_items.append(current_obj)
                else:
                    break

                if my_tank.distance_to_object(current_obj) < my_tank.distance_to_object(goal_obj):
                    goal_obj = current_obj
                    print("found closer item", goal_obj.position[0])
            elif message_type != ServerMessageTypes.OBJECTUPDATE:
                # Redirect caught message
                print("redirecting ", message_type)
                handle_incoming_message(message_type, message)
        GameServer.sendMessage(message_type=ServerMessageTypes.STOPTURRET)  # Stop scanning for items
        if goal_obj.position[0] != 1000:
            break
    return goal_obj


def handle_object_update(msg):  # Main tick decider
    if args.name == msg.get("Name", "?"):
        my_tank.update(msg)
        GameServer.sendMessage(ServerMessageTypes.STOPMOVE)
        if my_tank.health <= 2:
            health_pickup = find_close_obj("HealthPickup")  # reads a lot more messages
            print("health location", health_pickup.position)
            GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING,
                                   {"Amount": my_tank.target_heading(health_pickup)})
            time.sleep(2)
            GameServer.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE,
                                   {"Amount": my_tank.distance_to_object(health_pickup)/1.9})
        if my_tank.ammo == 0:
            GameServer.sendMessage(ServerMessageTypes.STOPALL)
            ammo_pickup = find_close_obj("AmmoPickup")
            print("ammo location", ammo_pickup.position)
            GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING,
                                   {"Amount": my_tank.target_heading(ammo_pickup)})
            time.sleep(2)
            GameServer.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE,
                                   {"Amount": my_tank.distance_to_object(ammo_pickup) / 1.9})
    elif msg.get("Type", "") == "Tank":
        target = GameObject(X=msg.get("X"), Y=msg.get("Y"), Id=msg.get("Id"))
        print("target heading", my_tank.target_heading(target))
        GameServer.sendMessage(ServerMessageTypes.TURNTURRETTOHEADING, {"Amount": my_tank.target_heading(target)})
        GameServer.sendMessage(ServerMessageTypes.FIRE)
        print("FIRE!")


def handle_kill(msg=""):
    bank()


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

    else:
        print("We go to the blue goal")
        turn_move(my_tank.target_heading(blue_goal), blue_goal_dist)


def turn_move(m_type, msg, heading, distance):
    print("Heading", heading)
    ServerComms.sendMessage(ServerMessageTypes.TURNTOHEADING, {'Amount': heading})
    ServerComms.sendMessage(ServerMessageTypes.TURNTURRETTOHEADING, {'Amount': heading})
    ServerComms.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE, {'Amount': distance})


def entered_goal(msg=""):
    print("a GOAAAAAL!!!!")
    ServerComms.sendMessage(message_type=ServerMessageTypes.STOPMOVE)
    ServerComms.sendMessage(message_type=ServerMessageTypes.TOGGLEREVERSE)
    turn_move(180, 30)


def snake():
    move = True
    while move is True:
        msg_type, msg = GameServer.readMessage()
        handle_incoming_message(msg_type, msg)
        GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {'Amount': random.randint(0,360)})
        GameServer.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE, {'Amount': random.randint(4,20)})
        if my_tank.position[0] > 70 or my_tank.position[0] < -70:
            GameServer.sendMessage(ServerMessageTypes.STOPALL)
            GameServer.sendMessage(ServerMessageTypes.TOGGLEREVERSE)
            if 60 < my_tank.position[0] < 70:
                GameServer.sendMessage(ServerMessageTypes.MOVEBACKWARSDISTANCE, {'Amount':10})
                GameServer.sendMessage(ServerMessageTypes.STOPALL)
                move = False


def handle_incoming_message(m_type, msg):
    try:
        handler_map.get(m_type)(msg)
    except TypeError:  # I don't have a function to deal with these events yet, so errors happen
        print(ServerMessageTypes().to_string(m_type))


# Main loop - read game messages and point at other tanks
# Event loop takes over the minimum time to complete, so no need to rate limit
my_tank = Player(server=GameServer)
handler_map = {ServerMessageTypes.OBJECTUPDATE: handle_object_update,
               ServerMessageTypes.KILL: handle_kill,
               ServerMessageTypes.ENTEREDGOAL: entered_goal,
               }
while True:
    time.sleep(0.05)
    message_type, message = GameServer.readMessage()  # Main tick read
    handle_incoming_message(message_type, message)
    # If there are no items in buffer, decide what to do next, else call buffer
    snake()
