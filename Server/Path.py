import Server.Location as Location
import math

def modN(x, N):
    return (x + N) % N

def distance(first, second):
    return math.sqrt((first.x - second.x) ** 2 + (first.y - second.y) ** 2)

def within_circle(pos, center, radius):
    return (pos.x - center.x) ** 2 + (pos.y - center.y) ** 2 <= radius ** 2

def turning_left_possible(left_turning_angle, left_closest_angle):
    return left_turning_angle < modN(left_closest_angle - Location.RobotLocation.grabber_angle, 2 * math.pi)

def turning_right_possible(right_turning_angle, right_closest_angle):
    return right_turning_angle > modN(right_closest_angle + Location.RobotLocation.grabber_angle, -2 * math.pi)

# birdie could be between wheel and grabber
# don't run over birdie with wheel
# avoid pushing birdie away with grabber
def next_collection_taget(robot_location: Location.RobotLocation, birdie_positions: list):
    distance_sorted = sorted(birdie_positions, key=lambda birdie: distance(robot_location, birdie))
    # All birdies that will be hit by the grabber if the robot turns
    too_close = [
        (birdie, robot_location.angle_between(birdie) - robot_location.angle)
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

    if left_closest == None and right_closest == None:
        next_birdie = distance_sorted[0]
        next_turning_angle = robot_location.angle_between(next_birdie)
    elif len(too_close) < len(birdie_positions):
        for birdie in distance_sorted:
            angle_relative_to_robot = robot_location.angle_between(birdie) - robot_location.angle
            left_turning_angle = modN(angle_relative_to_robot, 2 * math.pi)
            right_turning_angle = modN(angle_relative_to_robot, -2* math.pi)
            # check if turning the robot to the desired angle is possible without hitting other birdies
            if turning_left_possible(left_turning_angle, left_closest_angle) and turning_right_possible(right_turning_angle, right_closest_angle):
                next_birdie = birdie
                next_turning_angle = min(left_turning_angle, right_turning_angle, key=abs)
                break
            # check if turning the robot left to the desired angle is possible without hitting other birdies
            elif turning_left_possible(left_turning_angle, left_closest_angle):
                next_birdie = birdie
                next_turning_angle = left_turning_angle
            # check if turning the robot right to the desired angle is possible without hitting other birdies
            elif turning_right_possible(right_turning_angle, right_closest_angle):
                next_birdie = birdie
                next_turning_angle = right_turning_angle

    # If all birdies are blocked, we drive straight and will try again
    if next_birdie == None:
        next_birdie = Location.Position(
            robot_location.x + 2 * robot_location.center_to_grabber_tip * math.cos(robot_location.angle),
            robot_location.y +  2 * robot_location.center_to_grabber_tip * math.sin(robot_location.angle),
            robot_location.z
            )
        next_turning_angle = 0

    return (next_birdie, next_turning_angle)
