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
import numpy as np
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
    return abs(a - b) > math.radians(3)

def check_driving(drive_state: DriveState, robot_location: Location.RobotLocation, robot_commander):
    if not drive_state is None:
        match drive_state.stage:
            case DriveStage.START:
                robot_commander.send_command(RobotCommander.Turn(drive_state.angle))
                drive_state.stage = DriveStage.WAIT_ANGLE

            case DriveStage.WAIT_ANGLE:
                angle_diff = robot_location.angle_to(drive_state.target)
                if angle_diff == drive_state.angle:
                    robot_commander.send_command(RobotCommander.Turn(drive_state.angle))
                elif abs(angle_diff) < math.radians(4):
                    robot_commander.send_command(RobotCommander.Forward())
                    drive_state.stage = DriveStage.WAIT_DIST

            case DriveStage.WAIT_DIST:
                distance = robot_location.flat_distance(drive_state.target)
                #print(f"P: ({robot_location.x}, {robot_location.y}), D: {distance}")
                if distance < 5:
                    drive_state.stage = DriveStage.DONE
                else:
                    angle_diff = robot_location.angle_to(drive_state.target)
                    if not same_sign(drive_state.angle, angle_diff) or check_same_sign(drive_state.angle, angle_diff) or abs(angle_diff) > math.radians(5):
                        drive_state.angle = angle_diff
                        robot_commander.send_command(RobotCommander.Forward(drive_state.angle))

    return drive_state

def main():
    realsense = RealsenseServer.RealsenseServer(robotArucoId=42, courtArucoId=181, minAreaThreshold=700, maxAreaThreshold=8000)

    robot_commander = None

    # initialize Stage control enum
    stage = Stage.STARTUP_COURT
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
    score = 0
    round_num = 0
    side = None
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
                print("STARTUP_COURT: Orient court ArUco.")
                realsense.save_court_position() # this function requires a 'r' keypress to exit
                stage = Stage.STARTUP_REMOVE_COURT_ARUCO

            case Stage.STARTUP_REMOVE_COURT_ARUCO:
                # The court aruco should be gone
                if realsense.courtArucoVisible == False:
                    stage = Stage.STARTUP_ROBOT

            case Stage.STARTUP_ROBOT:
                if realsense.robot != None and realsense.robotArucoVisible == True:

                    input("STARTUP_ROBOT: Press to continue.")
                    robot_commander = RobotCommander.RobotCommander()
                    print("STARTUP_ROBOT: Confirmed.")
                    robot_commander.send_command(RobotCommander.ResetGrabberAngle())
                    setup_done = True
                    stage = Stage.STARTUP_CHATBOT

            case Stage.STARTUP_CHATBOT:
                chatbotThread = Thread(target = Chatbot.listen_and_respond, args = (point_queue, event_queue))
                chatbotThread.start()

                stage = Stage.STANDBY

            case Stage.STANDBY:
                stage = stage

            case Stage.EXPLAIN_SETUP:
                court = realsense.court
                if explain_stage == Chatbot.EventType.INSTRUCT_LEFT_SERVICE_BOUNDS:
                    explain_targets = deque([court.SBM, court.SBL, court.STL, court.STM, court.SBM])
                elif explain_stage == Chatbot.EventType.INSTRUCT_RIGHT_SERVICE_BOUNDS:
                    explain_targets = deque([court.SBM, court.SBR, court.STR, court.STM, court.SBM])
                elif explain_stage == Chatbot.EventType.INSTRUCT_FULL_COURT_BOUNDS:
                    explain_targets = deque([court.CL, court.STL, court.STR, court.CR])

                stage = Stage.EXPLAIN_ACT

            case Stage.EXPLAIN_ACT:
                if drive_state is None or drive_state.stage == DriveStage.DONE:
                    if len(explain_targets) > 0:
                        drive_state = DriveState(explain_targets.popleft(), realsense.robot)
                    else:
                        stage = Stage.STANDBY
                        drive_state = None
                        robot_commander.send_command(RobotCommander.Stop())
                        explain_event.set()
                        explain_stage = None

            case Stage.START_ROUND:
                detectedHitBirdieCount = 0
                stage = Stage.HIT_INSTRUCT
                if round_num % 2 == 0:
                    side = Court.Area.LEFT_SERVICE
                    # drive_state = DriveState(realsense.court.SBL, realsense.robot)
                else:
                    side = Court.Area.RIGHT_SERVICE
                    # drive_state = DriveState(realsense.court.SBR, realsense.robot)
                # elif drive_state.stage == DriveStage.DONE:
                #
                #     robot_commander.send_command(RobotCommander.Stop())
                #     drive_state = None
                round_num = round_num + 1

            case Stage.HIT_INSTRUCT:
                # a. Robot tells player to hit birdie
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
                birdie = realsense.tracked_hitbirdie
                dist = birdie.impact_position.flat_distance(realsense.robot)
                isInside = realsense.court.is_inside(birdie, side)
                if isInside:
                    score = score + 2 - (np.clip(dist, 100, 400) - 100) / 300 * 2
                else:
                    robot_commander.send_command(RobotCommander.Fail())

                print(f"HIT_REACT: Birdie(D: {dist}, IN: {isInside})")

                stage = Stage.HIT_AWAITSTATIC

            case Stage.HIT_AWAITSTATIC:
                realsense.detect_birdies(visualize = True)
                # b. Return to HIT_INSTRUCT
                if realsense.contours_are_static():
                    if detectedHitBirdieCount == BIRDIES_PER_ROUND:
                        stage = Stage.ROUND_END
                    else:
                        stage = Stage.HIT_INSTRUCT

            case Stage.ROUND_END:
                stage = Stage.COLLECT_EVACUATE
                drive_state = None

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
                    stage = Stage.START_ROUND

                # b. Make fixed path all the way from first to last one detected
                # c. Return robot to court
                robot_commander.send_command(RobotCommander.WheelTurn(-600))
                time.sleep(7)

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
                robot_commander.send_command(RobotCommander.End())
                quit()

        if setup_done and not event_queue.empty():
            (event, event_type) = event_queue.get()
            match event_type:
                case Chatbot.EventType.GET_SCORE:
                    point_queue.put(score)
                    event.set()
                case Chatbot.EventType.INSTRUCT_FULL_COURT_BOUNDS | Chatbot.EventType.INSTRUCT_LEFT_SERVICE_BOUNDS | Chatbot.EventType.INSTRUCT_RIGHT_SERVICE_BOUNDS:
                    stage = Stage.EXPLAIN_SETUP
                    explain_stage = event_type
                    explain_event = event
                case Chatbot.EventType.HIT_START:
                    stage = Stage.START_ROUND
                    event.set()
                case Chatbot.EventType.END:
                    stage = Stage.END



if __name__ == "__main__":
    main()