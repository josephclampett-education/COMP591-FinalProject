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
import Server.Vision.Court as Court
import Server.Chatbot as Chatbot

class Stage(Enum):
    STARTUP_COURT = auto()
    STARTUP_REMOVE_COURT_ARUCO = auto()
    STARTUP_ROBOT = auto()
    STARTUP_CHATBOT = auto()

    STANDBY = auto()

    EXPLAIN_SETUP = auto()
    EXPLAIN_ACT = auto()

    START_ROUND = auto()

    HIT_INSTRUCT = auto()
    HIT_AWAITPLAYER = auto()
    HIT_REACT = auto()
    HIT_AWAITSTATIC = auto()

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
    return same_sign(a,b) and abs(a - b) > math.radians(3)

def check_driving(drive_state: DriveState, robot_location: Location.RobotLocation, robot_commander):
    if not drive_state is None:
        match drive_state.stage:
            case DriveStage.START:
                robot_commander.send_command(RobotCommander.Turn(drive_state.angle))
                drive_state.stage = DriveStage.WAIT_ANGLE

            case DriveStage.WAIT_ANGLE:
                angle_diff = robot_location.angle_to(drive_state.target)
                if abs(angle_diff) < math.radians(5):
                    robot_commander.send_command(RobotCommander.Forward())
                    drive_state.stage = DriveStage.WAIT_DIST

            case DriveStage.WAIT_DIST:
                distance = robot_location.flat_distance(drive_state.target)
                print(f"P: ({robot_location.x}, {robot_location.y}), D: {distance}")
                if distance < 5:
                    drive_state.stage = DriveStage.DONE
                else:
                    angle_diff = robot_location.angle_to(drive_state.target)
                    if check_same_sign(drive_state.angle, angle_diff) or abs(angle_diff) > math.radians(5):
                        drive_state.angle = angle_diff
                        robot_commander.send_command(RobotCommander.Forward(drive_state.angle))

    return drive_state

def main():
    # initialize Stage control enum
    stage = Stage.STARTUP_CHATBOT
    drive_state = None
    detectedHitBirdieCount = 0
    BIRDIES_PER_ROUND = 4
    collectionBirdies = []
    event_queue = Queue()
    point_queue = Queue()
    explain_stage = None
    explain_event = None
    explain_targets = None
    setup_done = False
    while True:

        # Here perform actions that should be executed depending on the stage
        match stage:

            case Stage.STARTUP_CHATBOT:
                chatbotThread = Thread(target = Chatbot.listen_and_respond, args = (point_queue, event_queue))
                chatbotThread.start()

                stage = Stage.STANDBY
            
            case Stage.STANDBY:
                stage = stage

            case Stage.END:
                quit()

        if not event_queue.empty():
            (event, event_type) = event_queue.get()
            match event_type:
                case Chatbot.EventType.GET_SCORE:
                    point_queue.put(0)
                    event.set()
                case Chatbot.EventType.INSTRUCT_FULL_COURT_BOUNDS | Chatbot.EventType.INSTRUCT_LEFT_SERVICE_BOUNDS | Chatbot.EventType.INSTRUCT_RIGHT_SERVICE_BOUNDS:
                    print("DEBUG: Instructed court")
                    event.set()
                case Chatbot.EventType.HIT_START:
                    print("DEBUG: Instructed court")
                    event.set()
                case Chatbot.EventType.END:
                    stage = Stage.END

if __name__ == "__main__":
    main()