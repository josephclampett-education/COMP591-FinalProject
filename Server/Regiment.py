from collections import deque
from enum import Enum

from Server.Location import Position, RobotLocation

class Step:
    pass

class HitType(Enum):
    HIT = 0
    SERVE = 1

class MovePattern:
    def __init__(self, *args):
        self.points = deque()
        self.points.extend(*args)

    def add_point(self, *args):
        self.points.extend(*args)

    def next_point(self):
        next = self.points.popleft()
        self.points.append(next)
        return next

# explain rules for given hit_type
class Rule(Step):
    def __init__(self, hit_type: HitType):
        self.hit_type = hit_type
        self.steps = []

# collect all birdies on field
class Collection(Step):
    def __init__(self):
        self.current_birdie = None

# user hitting or serving robot that moves in given move_pattern
class MovingTarget(Step):
    def __init__(self, hit_type: HitType, move_pattern: MovePattern):
        self.hit_type = hit_type
        self.move_pattern = move_pattern

# user hitting or serving stationary robot at position
class StationaryTarget(Step):
    def __init__(self, hit_type: HitType, position: Position):
        self.hit_type = hit_type
        self.position = position

class Regiment:
    def __init__(self, *args):
        self.steps = deque()
        self.steps.extend(args)

    def add_step(self, *args):
        self.steps.extend(args)

    def get_next_step(self, robot_location: RobotLocation):
        if len(steps) > 0:
            next = self.steps.popleft()
            match next:
                case Collection():
                   next.current_birdie = robot_location
            return next
        else:
            return None