import Server.Location as Location
import math
from operator import itemgetter
from collections import deque
import numpy as np

def modN(x, N):
    return (x + N) % N

def within_circle(pos, center, radius):
    return (pos.x - center.x) ** 2 + (pos.y - center.y) ** 2 <= radius ** 2

def turning_left_possible(left_turning_angle, left_closest_angle):
    return left_turning_angle < modN(left_closest_angle - Location.RobotLocation.grabber_angle, 2 * math.pi)

def turning_right_possible(right_turning_angle, right_closest_angle):
    return right_turning_angle > modN(right_closest_angle + Location.RobotLocation.grabber_angle, -2 * math.pi)

def check_border(next_birdie, vision_border):
    lowx, lowy, highx, highy = vision_border
    next_pos = Location.Position(np.clip(next_birdie.x, lowx, highx), np.clip(next_birdie.y, lowy, highy), next_birdie.z)
    return next_pos

# Returns the best next collection target and which angle the robot has to turn in radians
def next_collection_taget(robot_location: Location.RobotLocation, birdie_positions: list, vision_border = (-1000, -1000, 1000, 1000)):
    # birdie could be between wheel and grabber
    # don't run over birdie with wheel
    # avoid pushing birdie away with grabber
    # All birdies that will be hit by the grabber if the robot turns
    too_close = [
        (birdie, robot_location.angle_to(birdie))
        for birdie in filter(
            lambda birdie: within_circle(birdie, robot_location, robot_location.center_to_grabber_tip),
            birdie_positions
            )
        ]

    # the birdie that would be first hit by the grippers if the robot turns left
    (left_closest, left_closest_angle) = min(too_close, key=lambda pair: modN(pair[1], 2 * math.pi), default=(None, None))
    # the birdie that would be first hit by the grippers if the robot turns right
    (right_closest, right_closest_angle) = max(too_close, key=lambda pair: modN(pair[1], -2 * math.pi), default=(None, None))

    next_birdie = None
    next_turning_angle = None
    next_dist = None

    if left_closest == None and right_closest == None:
        # will not hit any birdie while turning so we can just pick closest one
        birdies_dist_angle = [(birdie, robot_location.flat_distance(birdie), abs(robot_location.angle_to(birdie))) for birdie in birdie_positions]
        next_birdie, _, _ = min(birdies_dist_angle, key=itemgetter(1,2))
        next_turning_angle = robot_location.angle_to(next_birdie)
    elif len(too_close) < len(birdie_positions):
        for birdie in birdie_positions:
            angle_relative_to_robot = robot_location.angle_to(birdie)
            dist = robot_location.flat_distance(birdie)
            left_turning_angle = modN(angle_relative_to_robot, 2 * math.pi)
            right_turning_angle = modN(angle_relative_to_robot, -2* math.pi)
            if next_birdie is None or dist <= next_dist:
                # check if turning the robot to the desired angle is possible without hitting other birdies
                if turning_left_possible(left_turning_angle, left_closest_angle) and turning_right_possible(right_turning_angle, right_closest_angle):
                    angle = min(left_turning_angle, right_turning_angle, key=abs)
                # check if turning the robot left to the desired angle is possible without hitting other birdies
                elif turning_left_possible(left_turning_angle, left_closest_angle):
                    angle = left_turning_angle
                # check if turning the robot right to the desired angle is possible without hitting other birdies
                elif turning_right_possible(right_turning_angle, right_closest_angle):
                    angle = right_turning_angle
                else:
                    continue
                if next_birdie is None or abs(angle) < abs(next_turning_angle):
                    next_birdie = birdie
                    next_turning_angle = angle
                    next_dist = dist


    # If all birdies are blocked, we drive straight and will try again
    if next_birdie == None:
        next_birdie = Location.Position(
            robot_location.x + 2 * robot_location.center_to_grabber_tip * math.cos(robot_location.angle),
            robot_location.y +  2 * robot_location.center_to_grabber_tip * math.sin(robot_location.angle),
            robot_location.z
            )
        next_turning_angle = 0

    next_pos = check_border(next_birdie, vision_border)

    return (next_birdie, next_turning_angle)

def make_path(robot_location: Location.RobotLocation, birdie_positions: list, vision_border):
    path = deque()
    current_robot = robot_location
    worklist = birdie_positions.copy()
    while len(worklist) > 0:
        next_pos, next_angle = next_collection_taget(current_robot, worklist, vision_border)
        path.append((next_pos, next_angle))
        try:
            worklist.remove(next_pos)
        except ValueError:
            # the next position might be going straight, which is not in the list
            pass
        current_robot = Location.RobotLocation(next_pos.x, next_pos.y, next_pos.z, next_angle)
    return path

def main():
    robot = Location.RobotLocation(0,0,0,0)
    birdies = [Location.Position(0,0.1,0),
               Location.Position(0,-1,0),
               Location.Position(-1,0,0),
               Location.Position(300, 0,0)]
    next, angle = next_collection_target(robot, birdies)
    print(next)
    print(angle)

if __name__ == "__main__":
    main()