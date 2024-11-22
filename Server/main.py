from collections import deque

import RealsenseServer
import Location
import Regiment
import math

birdie_length = 5 # TODO
robot_length = 10 # TODO center of robot to gripper tip

def make_collection_schedule(robot_location, birdie_positions):

    robot_center_to_gripper_center = robot_length - gripper_length/2

    schedule = deque()
    current = robot_location
    remaining = birdie_positions
    for _ in range(len(birdie_positions)):
        next = None
        min_distance = float('inf')
        for pos in remaining:
            # Check if robot would possibly hit birdie while turning
            if (pos.x - current.x) ** 2 + (pos.y - current.y) ** 2 < (birdie_length + robot_length) ** 2:
                continue
            distance = distance(current, pos)
            if distance < min_distance:
                min_distance = distance
                next = pos
        schedule.append(next)
        remaining.remove(next)
        current = next

def distance(first, second):
    return math.sqrt((first.x - second.x) ** 2 + (first.y - second.y) ** 2)

# TODO: use robot orientation or find center and radius of gripper "circle"
def has_collected(robot_location, birdie_position):
    return distance(robot_location, birdie_position) < distance(robot_location, robot_location.get_gripper_position)

prev_birdie_positions = None
prev_robot_location = None

regiment: Regiment.Regiment = game.get_next_regiment()
current_step = regiment.get_next_step()

while True:
    robot_location: Location.RobotLocation = RealsenseServer.detect_robot()
    birdie_positions: list[Location.BirdiePosition] = RealsenseServer.detect_birdies()

    match current_step:
        case Regiment.Rule():
            break
        case Regiment.MovingTarget():
            break
        case Regiment.StationaryTarget():
            break
        case Regiment.Collection():
            if has_collected(robot_location, current_step.current_birdie):
                remaining_birdies = filter(lambda pos: not has_collected(robot_location, pos), birdie_positions)
                current_step.current_birdie = None # TODO