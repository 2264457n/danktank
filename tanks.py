import math


class GameObject(object):
    position = 0, 0
    id = 1
    heading = 0

    def distance_to_object(self, other) -> float:
        return math.sqrt(math.pow((self.position[0]-other.position[0]), 2) + math.pow((self.position[1]-other.position[1]), 2))

    def target_heading(self, other) -> float:
        heading = math.atan2(other.position[1]-self.position[1],
                             other.position[0]-self.position[0]) *\
                  (180/math.pi)  # Radians to degrees
        return math.fabs(math.fmod((heading - 360), 360))

    def __init__(self, **kwargs):
        self.position = kwargs.get("X"), kwargs.get("Y")
        self.id = kwargs.get("Id")

    def __hash__(self):
        return self.id

    def get_obj_class(self) -> type:
        return self.__class__


class Pickup(GameObject):
    pickup_type = ""

    def __init__(self, **kwargs):
        super().__init__()


class Tank(GameObject):
    name = ""
    health = 5
    ammo = 5

    def __init__(self, **kwargs):
        super().__init__()
        self.name = kwargs.get("name")
        self.health = kwargs.get("Health")
        self.ammo = kwargs.get("Ammo")

    def update(self, message):
        self.position = message["X"], message["Y"]
        self.heading = message["Heading"]
        self.health = message["Health"]
        self.ammo = message["Ammo"]


class Player(Tank):
    message_pipeline = None
    heading = 0

    def __init__(self, server, **kwargs):
        super().__init__()
        self.message_pipeline = server
