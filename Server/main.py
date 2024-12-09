import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)


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
        return stage[(self.value - 1 + 1) % len(stage)]



def has_collected(robot_location, birdie_position):
    return robot_location.flat_distance(birdie_position) < robot_location.flat_distance(robot_location.get_gripper_position)

def main():

    robot_commander = RobotCommander.RobotCommander()

    realsense = RealsenseServer.RealsenseServer(robotArucoId=42, courtArucoId=44)

    event_queue = Queue()
    point_queue = Queue()
    textToSpeechThread = Thread(target=textToSpeech.listen_and_respond, args=(point_queue, event_queue, robot_commander))
    textToSpeechThread.start()

    lesson = make_lesson(realsense.court)
    regiment: Regiment.Regiment = lesson.popleft()
    current_step = regiment.get_next_step()

    points = 0



    # initialize Stage controll enum
    stage = Stage.STARTUP

    while True:

        match stage:
            case Stage.STARTUP:
                # Initialize all components
                pass
            case Stage.STARTGAME:
                # TODO Do we need this stage?
                pass
            case Stage.HIT_INSTRUCT:
                # a. Robot tells player to hit birdie   
                # b. Capture background frame of court (includes robot, other birdies, etc.)
                pass
            case Stage.HIT_PLAYER:
                # a. Player hits a birdie as instructed
                # b. Camera is live, tracking position of court
                # c. Look for impact
                # d. Robot reacts to hit
                pass
            case Stage.HIT_REACT:
                # a. Give details on the specific hit
                # b. Return to HIT_INSTRUCT
                pass
            case Stage.ROUND_END:
                # Robot tells the player to stop, gives stats, etc.
                # Answers questions
                pass
            case Stage.COLLECT_EVACUATE:
                # Robot drives off court in a controlled way (we need to get it back on the court again)
                pass
            case Stage.COLLECT_PLAN:
                # a. Take image
                # b. Make fixed path all the way from first to last one detected
                pass
            case Stage.COLLECT_ACT:
                # a. Drive from point to point, grabbing at each stop
                # b. Don’t worry about if some weren’t collected
                # c. Return to COLLECT_EVACUATE
                pass
            

        if not textToSpeechThread.is_alive():
            break

        if not event_queue.empty():
            event: Event = event_queue.get()
            point_queue.put(points)
            event.set()

        realsense.detect(visualize=True)

        robot_location = realsense.robot
        birdie_positions = realsense.birdies

        match current_step:
            case Regiment.Rule():

                break
            case Regiment.MovingTarget():
                break
            case Regiment.StationaryTarget():
                if not robot_location.is_close(current_step.position):
                    robot_commander.send_command(RobotCommander.Turn(robot_location.angle_to(current_step.position)))
                    robot_commander.send_command(RobotCommander.Forward(robot_location, current_step.position))
            case Regiment.Collection():
                if len(birdie_positions) == 0:
                    current_step = regiment.get_next_step(robot_location=robot_location)
                    break
                if has_collected(robot_location, current_step.current_birdie):
                    (next_birdie, next_radians) = next_collection_taget(
                        robot_location= robot_location,
                        birdie_positions=list(birdie_positions.values())
                        )
                    current_step.current_birdie = next_birdie
                    robot_commander.send_command(RobotCommander.Turn(next_radians))
                    robot_commander.send_command(RobotCommander.Forward(robot_location, next_birdie))


main()