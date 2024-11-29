class Position:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class Orientation:
    def __init__(self, angle):
        self.angle = angle

class BirdiePosition(Position):
    def __init__(self, x, y, z, hit_ground):
        Position.__init__(x,y,z)
        self.hit_ground = hit_ground

class RobotLocation(Position, Orientation):
    _gripper_length = 3 # TODO

    def __init__(self, x, y, z):
        Position.__init__(x,y,z)

    def get_gripper_position(self):
        return Position(0, 0, z) # TODO: calculate using orientation
