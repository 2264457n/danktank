#!/usr/bin/python
import random
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


def find_close_obj(type):
    goal_obj = GameObject(X=1000, Y=1000)
    while True:
        time.sleep(0.05)
        GameServer.sendMessage(ServerMessageTypes.TOGGLETURRETLEFT)
        time.sleep(3)
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
    if args.name == msg.get("Name", "?"):
        my_tank.update(msg)
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
            print(ammo_pickup.position)
            GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING,
                                   {"Amount": my_tank.target_heading(ammo_pickup)})
            time.sleep(2)
            GameServer.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE,
                                   {"Amount": my_tank.distance_to_object(ammo_pickup) / 1.9})
    elif msg.get("Type", "") == "Tank":
        target = GameObject(X=msg.get("X"), Y=msg.get("Y"), Id=msg.get("Id"))
        print(my_tank.target_heading(target))
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


def turn_move(heading, distance):
    print("Heading", heading)
    job_queue.put((ServerMessageTypes.TURNTOHEADING, {'Amount': heading}))
    job_queue.put((ServerMessageTypes.TURNTURRETTOHEADING, {'Amount': heading}))
    job_queue.put((ServerMessageTypes.MOVEFORWARDDISTANCE, {'Amount': distance}))


def entered_goal(msg=""):
    print("a GOAAAAAL!!!!")
    job_queue.put((ServerMessageTypes.TOGGLEREVERSE, None))
    job_queue.put((turn_move,(180, 30)))
    pass


def heal(msg, state):
    if state == 1:
        pass
    elif state == 2:
        pass

def snake():
    move = True
    while move is True:
         GameServer.sendMessage(ServerMessageTypes.TURNTOHEADING, {'Amount': random.randint(0,360)})
         GameServer.sendMessage(ServerMessageTypes.MOVEFORWARDDISTANCE,{'Amount': random.randint(4,20)})
         continue
         if my_tank.position[0] > 70 or my_tank.position[0] < -70:
            GameServer.sendMessage(ServerMessageTypes.STOPALL)
            GameServer.sendMessage(ServerMessageTypes.TOGGLEREVERSE)
            if 60 < my_tank.position[0] < 70:
                GameServer.sendMessage(ServerMessageTypes.MOVEBACKWARSDISTANCE, {'Amount':10})





# Main loop - read game messages and point at other tanks
# Event loop takes over the minimum time to complete, so no need to rate limit
my_tank = Player(server=GameServer)
handler_map = {ServerMessageTypes.OBJECTUPDATE: handle_object_update,
               ServerMessageTypes.KILL: handle_kill,
               ServerMessageTypes.ENTEREDGOAL: entered_goal,
               }
job_queue = Queue()
while True:
    time.sleep(0.05)
    message_type, message = GameServer.readMessage()
    try:
        handler_map.get(message_type)(message)
    except TypeError:  # I don't have a function to deal with these events yet, so errors happen
        print(ServerMessageTypes().to_string(message_type))

    # If there are no items in buffer, decide what to do next, else call buffer
    if job_queue.empty():
        # Decide-y code
        if my_tank.health < 2:
            job_queue.put((heal, 0))
    else:
        job = job_queue.get()
        print(job)
        part_a, part_b = job[0], job[1]
        if isinstance(part_a, int):  # is a message type
            GameServer.sendMessage(part_a,part_b)
        else:  # Is a callback
            part_a(message, part_b)
    # callback is responsible for adding any jobs it wants to the queue

