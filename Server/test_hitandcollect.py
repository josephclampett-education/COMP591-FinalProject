import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

import time
from collections import deque
import Server.Vision.RealsenseServer as RealsenseServer
import Server.Location as Location
import Server.Regiment as Regiment
import math
import asyncio
from queue import Queue
from threading import Event, Thread
from enum import Enum, auto
import Server.RobotCommander as RobotCommander
import Server.Path as Path
from Server.Lesson import make_lesson


class Stage(Enum):
    STARTUP_COURT = auto()
    STARTUP_REMOVE_COURT_ARUCO = auto()
    STARTUP_ROBOT = auto()

    STARTGAME = auto()

    HIT_INSTRUCT = auto()
    HIT_AWAITPLAYER = auto()
    HIT_REACT = auto()

    ROUND_END = auto()

    COLLECT_EVACUATE = auto()
    COLLECT_PLAN = auto()
    COLLECT_ACT = auto()

    END = auto()

class DriveStage(Enum):
    START = auto()
    WAIT_ANGLE = auto()
    WAIT_DIST = auto()
    DONE = auto()

class DriveState:
    def __init__(self, target, robot_location: Location.RobotLocation, angle=None, stage=DriveStage.START):
        self.stage = stage
        self.target = target
        if angle is None:
            angle = robot_location.angle_to(target)
        self.angle = angle

def has_collected(robot_location, birdie_position):
    return robot_location.flat_distance(birdie_position) < robot_location.flat_distance(robot_location.get_grabber_position())

def same_sign(a, b):
    return a * b > 0

def check_same_sign(a, b):
    return same_sign(a,b) and abs(a - b) > math.radians(1)

def check_driving(drive_state: DriveState, robot_location: Location.RobotLocation, robot_commander):
    if not drive_state is None:
        match drive_state.stage:
            case DriveStage.START:
                robot_commander.send_command(RobotCommander.Turn(drive_state.angle))
                drive_state.stage = DriveStage.WAIT_ANGLE

            case DriveStage.WAIT_ANGLE:
                angle_diff = robot_location.angle_to(drive_state.target)
                if abs(angle_diff) < math.radians(2):
                    robot_commander.send_command(RobotCommander.Forward())
                    drive_state.stage = DriveStage.WAIT_DIST

            case DriveStage.WAIT_DIST:
                distance = robot_location.flat_distance(drive_state.target)
                print(f"P: ({robot_location.x}, {robot_location.y}), D: {distance}")
                if distance < 5:
                    drive_state.stage = DriveStage.DONE
                else:
                    angle_diff = robot_location.angle_to(drive_state.target)
                    if check_same_sign(drive_state.angle, angle_diff) or abs(angle_diff) > math.radians(2):
                        drive_state.angle = angle_diff
                        robot_commander.send_command(RobotCommander.Forward(drive_state.angle))
                    # else:
                    #     robot_commander.send_command(RobotCommander.Forward())

    return drive_state

def main():
    realsense = RealsenseServer.RealsenseServer(robotArucoId=180, courtArucoId=181, minAreaThreshold=700, maxAreaThreshold=8000)

    robot_commander = None

    # initialize Stage control enum
    stage = Stage.STARTUP_COURT
    drive_state = None
    detectedHitBirdieCount = 0
    BIRDIES_PER_ROUND = 2
    collectionBirdies = []
    while True:
        # Here perform actions that should be executed all the time
        realsense.detect_arucos()

        drive_state = check_driving(
            drive_state=drive_state,
            robot_location=realsense.robot,
            robot_commander=robot_commander,
            )

        # Here perform actions that should be executed depending on the stage
        match stage:
            case Stage.STARTUP_COURT:
                print("Orient court ArUco to match the perfect position:")
                realsense.save_court_position() # this function requires a 'r' keypress to exit
                stage = Stage.STARTUP_REMOVE_COURT_ARUCO

            case Stage.STARTUP_REMOVE_COURT_ARUCO:
                # The court aruco should be gone
                if realsense.courtArucoVisible == False:
                    stage = Stage.STARTUP_ROBOT

            case Stage.STARTUP_ROBOT:
                if realsense.robot != None and realsense.robotArucoVisible == True:

                    robot_commander = RobotCommander.RobotCommander()
                    input("Press to continue")
                    print("STARTUP_ROBOT: Confirmed.")
                    robot_commander.send_command(RobotCommander.ResetGrabberAngle())

                    stage = Stage.STARTGAME

            case Stage.STARTGAME:
                detectedHitBirdieCount = 0
                stage = Stage.HIT_INSTRUCT

            case Stage.HIT_INSTRUCT:
                # a. Robot tells player to hit birdie
                # TODO: time.sleep(1)
                realsense.prepare_birdie_tracking()
                realsense.capture_hit_background() # This is the background with the static robot inside of it

                robot_commander.send_command(RobotCommander.Beep())
                stage = Stage.HIT_AWAITPLAYER

            case Stage.HIT_AWAITPLAYER:
                # a. Player hits a birdie as instructed
                # b. Camera is live, tracking position of court
                realsense.detect_birdies(visualize = True)

                #print("birdies landed:", realsense.get_num_birdies_landed(), num_birdies_landed)
                if realsense.tracked_hitbirdie is not None and realsense.tracked_hitbirdie.hit_ground:
                    print("HIT_AWAITPLAYER: Birdie detected. Reacting.")

                    detectedHitBirdieCount += 1
                    stage = Stage.HIT_REACT

            case Stage.HIT_REACT:
                # a. Give details on the specific hit
                # TODO

                # b. Return to HIT_INSTRUCT
                if detectedHitBirdieCount == BIRDIES_PER_ROUND:
                    stage = Stage.ROUND_END
                else:
                    stage = Stage.HIT_INSTRUCT

            case Stage.ROUND_END:
                stage = Stage.COLLECT_EVACUATE

            case Stage.COLLECT_EVACUATE:
                # Robot drives off court in a controlled way (we need to get it back on the court again)
                if drive_state is None:
                    drive_state = DriveState(target=Location.Position(150, 150, 0), robot_location=realsense.robot)
                if drive_state.stage == DriveStage.DONE:
                    robot_commander.send_command(RobotCommander.WheelTurn(500))
                    drive_state = None
                    stage = Stage.COLLECT_PLAN

            case Stage.COLLECT_PLAN:
                time.sleep(5.5)

                # a. Take image
                print("COLLECT_PLAN: Taking collect birdie image.")
                collectionBirdies = realsense.detect_collection_birdies(visualize=True)
                if len(collectionBirdies) > 0:
                    visionBorder = (150, 150, 1280 - 150, 720 - 150)
                    path = Path.make_path(realsense.robot, collectionBirdies, visionBorder)
                    stage = Stage.COLLECT_ACT
                else:
                    stage = Stage.STARTGAME

                # b. Make fixed path all the way from first to last one detected
                # c. Return robot to court
                robot_commander.send_command(RobotCommander.WheelTurn(-500))
                time.sleep(5)

            case Stage.COLLECT_ACT:
                # Get birdie
                if drive_state is None or drive_state.stage == DriveStage.DONE:
                    if len(path) > 0:
                        drive_target, turn_direction = path.popleft()
                        drive_state = DriveState(target=drive_target, robot_location=realsense.robot, angle=turn_direction)
                    else:
                        stage = Stage.COLLECT_EVACUATE
                        drive_state = None

            case Stage.END:
                robot_commander.send_command(RobotCommander.Stop())

if __name__ == "__main__":
    main()