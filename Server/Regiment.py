from collections import deque
from enum import Enum

class Regiment:
    def __init__(self):
        self.steps = deque()

    def add_step(step: Step):
        steps.append(step)

    def get_next_step():
        if len(steps) > 0:
            return steps.popleft()
        else return None

class Step(Enum):
    SERVE_RULES = 0 # explain rules for serving
    HIT_RULES = 1 # explian rules for hitting
    STATIONARY_HIT = 2 # user hitting stationary robot with one birdie
    MOVING_HIT = 3 # user hitting moving robot with one birdie
    COLLECTION = 4 # collect birdies
    STATIONARY_SERVE = 5 # user serving to stationary robot with one birdie
    MOVING_SERVE = 6 # user serving to moving robot with one birdie
