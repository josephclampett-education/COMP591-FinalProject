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
from Server.Path import next_collection_taget
from Server.Lesson import make_lesson


class Stage(Enum):
    STARTUP = auto() #1
    STARTGAME = auto() #2
    HIT_INSTRUCT = auto() #3
    HIT_PLAYER = auto() #4
    HIT_REACT = auto() #5
    ROUND_END = auto() #6
    COLLECT_EVACUATE = auto() #7
    COLLECT_PLAN = auto() #8
    COLLECT_ACT = auto() #9

    def next_stage(self):
        stage = list(self.__class__)
        print(f"{self} done")
        return stage[(self.value - 1 + 1) % len(stage)]

class DriveStage(Enum):
    START = auto()
    WAIT_ANGLE = auto()
    WAIT_DIST = auto()
    DONE = auto()

def has_collected(robot_location, birdie_position):
    return robot_location.flat_distance(birdie_position) < robot_location.flat_distance(robot_location.get_grabber_position())

def check_driving(drive_stage, robot_location: Location.RobotLocation, turn_direction, drive_target, robot_commander):
    match drive_stage:
        case DriveStage.START:
            if turn_direction is None:
                turn_direction = robot_location.angle_to(drive_target)
            robot_commander.send_command(RobotCommander.Turn(turn_direction))
            drive_stage = DriveStage.WAIT_ANGLE
        case DriveStage.WAIT_ANGLE:
            angle_diff = robot_location.angle_to(drive_target)
            if abs(angle_diff) < 0.01:
                robot_commander.send_command(RobotCommander.Forward())
                turn_direction = None
                drive_stage = DriveStage.WAIT_DIST
        case DriveStage.WAIT_DIST:
            distance = robot_location.flat_distance(drive_target)
            print(f"P: ({robot_location.x}, {robot_location.y}), D: {distance}")
            if distance < 5:
                robot_commander.send_command(RobotCommander.Stop())
                drive_target = None
                drive_stage = DriveStage.DONE
            else:
                turn_direction = robot_location.angle_to(drive_target)
                if abs(turn_direction) > math.radians(1):
                    robot_commander.send_command(RobotCommander.Forward(turn_direction))
                else:
                    robot_commander.send_command(RobotCommander.Forward())

    return (drive_stage, turn_direction, drive_target)

def main():

    robot_commander = RobotCommander.RobotCommander()

    realsense = RealsenseServer.RealsenseServer(robotArucoId=180, courtArucoId=181)

    input("Press to continue")
    print("c")

    # initialize Stage controll enum
    stage = Stage.COLLECT_EVACUATE
    drive_stage = None
    drive_target = None
    turn_direction = None
    BIRDIES_PER_ROUND = 1
    collectionBirdies = []
    while True:

        # Here perform actions that should be executed all the time
        realsense.detect_arucos()

        drive_stage, turn_direction, drive_target = check_driving(
            drive_stage=drive_stage,
            robot_location=realsense.robot,
            turn_direction=turn_direction,
            drive_target=drive_target,
            robot_commander=robot_commander,
            )

        # Here perform actions that should be executed depending on the stage
        match stage:
            case Stage.COLLECT_EVACUATE:
                # Robot drives off court in a controlled way (we need to get it back on the court again)
                if drive_stage is None:
                    drive_stage = DriveStage.START
                    drive_target = Location.Position(110, 110, 0)
                if drive_stage == DriveStage.DONE:
                    robot_commander.send_command(RobotCommander.WheelTurn(500))
                    drive_stage = None
                    stage = Stage.COLLECT_PLAN

            case Stage.COLLECT_PLAN:
                # a. Take image
                collectionBirdies = realsense.detect_collection_birdies()

                time.sleep(7)

                # b. Make fixed path all the way from first to last one detected
                # c. Return robot to court
                robot_commander.send_command(RobotCommander.WheelTurn(-500))
                time.sleep(7)
                
                stage = Stage.COLLECT_ACT

            case Stage.COLLECT_ACT:
                # Get birdie
                if drive_stage is None:
                    drive_stage = DriveStage.START
                    drive_target = collectionBirdies[0]
                if drive_stage == DriveStage.DONE:
                    stage = Stage.COLLECT_EVACUATE

if __name__ == "__main__":
    main()


