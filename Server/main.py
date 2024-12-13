import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

import time
from collections import deque
import Server.Vision.RealsenseServer as RealsenseServer
import Server.textToSpeech as textToSpeech
import Server.Location as Location
import Server.Regiment as Regiment
import math
import asyncio
from queue import Queue
from threading import Event, Thread
from enum import Enum, auto
import Server.RobotCommander as RobotCommander
import Path
from Server.Lesson import make_lesson


class Stage(Enum):
    STARTUP_COURT = auto() #1
    STARTUP_REMOVE_COURT_ARUCO = auto() #2
    STARTUP_ROBOT = auto() #3
    STARTGAME = auto() #4
    HIT_INSTRUCT = auto() #5
    HIT_PLAYER = auto() #6
    HIT_REACT = auto() #7
    ROUND_END = auto() #8
    COLLECT_EVACUATE = auto() #9
    COLLECT_PLAN = auto() #10
    COLLECT_ACT = auto() #11


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
            else:
                robot_commander.send_command(RobotCommander.Turn(turn_direction))
        case DriveStage.WAIT_DIST:
            distance = robot_location.flat_distance(drive_target)
            print(distance)
            if distance < 0.02:
                robot_commander.send_command(RobotCommander.Stop())
                drive_target = None
                drive_stage = DriveStage.DONE
            else:
                robot_commander.send_command(RobotCommander.Forward())
                turn_direction = robot_location.angle_to(drive_target)
                if abs(turn_direction) > 0.01:
                    robot_commander.send_command(RobotCommander.Turn(turn_direction))

    return (drive_stage, turn_direction, drive_target)

def main():

    robot_commander = RobotCommander.RobotCommander()

    realsense = RealsenseServer.RealsenseServer(robotArucoId=180, courtArucoId=181)

    event_queue = Queue()
    point_queue = Queue()
    # textToSpeechThread = Thread(target=textToSpeech.listen_and_respond, args=(point_queue, event_queue, robot_commander))
    # textToSpeechThread.start()

    # lesson = make_lesson(realsense.court)
    # lesson = deque()
    # lesson.append(Regiment.Regiment(Regiment.Collection()))
    # regiment: Regiment.Regiment = lesson.popleft()
    # current_step = regiment.get_next_step(realsense.robot)
    # print(current_step)

    input("Press to continue")
    print("c")


    points = 0



    # initialize Stage controll enum
    stage = Stage.STARTUP_COURT
    drive_stage = None
    drive_target = None
    turn_direction = None
    BIRDIES_PER_ROUND = 1
    num_birdies_landed = 0
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
            case Stage.STARTUP_COURT:
                print("found court")
                print("Now orient court aruco to match the perfect position:")
                realsense.save_court_position() # this function requires a 'r' keypress to exit
                stage = stage.next_stage()
            case Stage.STARTUP_REMOVE_COURT_ARUCO:
            
                # The court aruco should be removed
                if realsense.courtArucoVisible == False:
                    stage = stage.next_stage()
            case Stage.STARTUP_ROBOT:
                if realsense.robot != None and realsense.robotArucoVisible == True:
                    stage = stage.next_stage()
            case Stage.STARTGAME:
                # TODO Do we need this stage?
                pass
            case Stage.HIT_INSTRUCT:
                # a. Robot tells player to hit birdie
                # TODO
                # b. Capture background frame of court (includes robot, other birdies, etc.)
                time.sleep(1)
                realsense.reset_birdies()
                realsense.capture_hit_background() # This is the background with the static robot inside of it
                stage = stage.next_stage()
                pass
            case Stage.HIT_PLAYER:
                # a. Player hits a birdie as instructed
                # b. Camera is live, tracking position of court
                realsense.detect_birdies(visualize=True)
                # c. Look for impact
                if realsense.get_num_birdies_landed() == 1: # We delete birdies after detection, so 1 equals new birdie landed
                    print("Birdie Detected: Proceed to Stage HIT_REACT")
                    # go to next stage after a birdie has been detected as landed
                    num_birdies_landed += 1
                    # d. Robot reacts to hit
                    # TODO Robot reacts to  a hit
                    stage = stage.next_stage()

            case Stage.HIT_REACT:
                # a. Give details on the specific hit
                # TODO

                # b. Return to HIT_INSTRUCT
                if num_birdies_landed == BIRDIES_PER_ROUND:
                    stage = stage.next_stage()
                else:
                    stage = Stage.HIT_INSTRUCT

            case Stage.ROUND_END:
                # Robot tells the player to stop, gives stats, etc.
                # TODO
                print("Game over")
                raise Exception("Game Over") # TODO remove
                # Answers questions
                pass
            case Stage.COLLECT_EVACUATE:
                # Robot drives off court in a controlled way (we need to get it back on the court again)
                if drive_stage is None:
                    drive_stage = DriveStage.START
                    drive_target = Location.Position(0, 0, 0)
                if drive_stage == DriveStage.DONE:
                    robot_commander.send_command(RobotCommander.WheelTurn(2))
                    drive_stage = DriveStage.DONE
                    stage = stage.next_stage()
                pass
            case Stage.COLLECT_PLAN:
                # a. Take image
                collectBirdies = realsense.detect_collection_birdies()
                path = Path.make_path(realsense.robot, collectBirdies)
                # b. Make fixed path all the way from first to last one detected
                # c. Return robot to court
                robot_commander.send_command(RobotCommander.WheelTurn(-2))
                pass
            case Stage.COLLECT_ACT:
                # a. Drive from point to point, grabbing at each stop
                # b. Don’t worry about if some weren’t collected
                # c. Return to COLLECT_EVACUATE
                if drive_stage is None or drive_stage == DriveStage.DONE:
                    if len(path) > 0:
                        drive_stage = DriveStage.START
                        drive_target, turn_direction = path.popleft()
                pass

        # if not textToSpeechThread.is_alive():
        #     shutdown()
        #     break

        # if not event_queue.empty():
        #     event: Event = event_queue.get()
        #     point_queue.put(points)
        #     event.set()

def test():

    robot_commander = RobotCommander.RobotCommander()

    realsense = RealsenseServer.RealsenseServer(robotArucoId=180, courtArucoId=181)
    drive_stage = DriveStage.START
    drive_target = Location.Position(0, 0, 0)
    turn_direction = None

    while True:
        realsense.detect_arucos()
        if realsense.robot is None:
            print("no robot")
            continue
        drive_stage, turn_direction, drive_target = check_driving(
            drive_stage=drive_stage,
            robot_location=realsense.robot,
            turn_direction=turn_direction,
            drive_target=drive_target,
            robot_commander=robot_commander,
            )

if __name__ == "__main__":
    main()


