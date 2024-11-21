from collections import deque
from enum import Enum

import Loctation

class Regiment:
    def __init__(self):
        self.steps = deque()

    def add_step(step: Step):
        steps.append(step)

    def get_next_step(robot_location: Loctation.RobotLocation):
        if len(steps) > 0:
            next = steps.popleft()
            match next:
                case Collection():
                    next.current_birdie = robot_location
            return next
        else:
            return None

class Step:
    pass

class HitType(Enum):
    HIT = 0
    SERVE = 1

class MovePattern(Enum):
    STRAIGHT = 0

# explain rules for given hit_type
class Rule(Step):
    def __init__(self, hit_type: HitType):
        self.hit_type = hit_type

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