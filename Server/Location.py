import math

class Position:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __sub__(self, other):
        return Position(
            self.x - other.x,
            self.y - other.y,
            self.z - other.z
            )

    def __str__(self):
        return f"{self.x}, {self.y}, {self.z}"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and (self.x, self.y, self.z) == (other.x, other.y, other.z)

    # Returns the angle bewteen two Positions in radians
    def angle_between(self, other):
        temp = other - self
        return math.atan2(temp.y, temp.x)

class Orientation:
    # angle in radians
    def __init__(self, angle):
        self.angle = angle

class BirdieLocation(Position, Orientation):
    _birdie_length = 5 # TODO
    _birdie_width = 2 # TODO

    def __init__(self, x, y, z, angle, hit_ground):
        Position.__init__(self, x, y, z)
        Orientation.__init__(self, angle)
        self.hit_ground = hit_ground


class RobotLocation(Position, Orientation):
    _grabber_length = 30 # TODO
    center_to_grabber_tip = 50 # TODO
    grabber_angle = math.radians(25) # TODO

    def __init__(self, x, y, z, angle):
        Position.__init__(self, x, y, z)
        Orientation.__init__(self, angle)

    def get_grabber_position(self):
        return Position(
            self.x + self._grabber_length * math.cos(self.angle),
            self.y + self._grabber_length * math.sin(self.angle),
            self.z
            )