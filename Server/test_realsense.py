import sys
import os
from enum import Enum, auto
import time
# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

import Server.Vision.RealsenseServer as RealsenseServer


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
        print("Stage changed to: ", stage[(self.value - 1 + 1) % len(stage)])
        return stage[(self.value - 1 + 1) % len(stage)]


def main():
    realsense = RealsenseServer.RealsenseServer(robotArucoId=42, courtArucoId=44)
    
    
    # initialize Stage controll enum
    stage = Stage.STARTUP
    BIRDIES_PER_ROUND = 5
    num_birdies_landed = 0
    print("Start!!!")
    while True:

        # Here perform actions that should be executed all the time
        realsense.detect_arucos()



        # Here perform actions that should be executed depending on the stage
        match stage:
            case Stage.STARTUP:
                # Initialize all components
                # a. Realsense camera should detect court and robot
                if realsense.found_arucos(): # TODO add other conditions here that are needed to process to next stage
                    print("found arucos")
                    stage = stage.next_stage()
                pass
            case Stage.STARTGAME:
                # TODO Do we need this stage?
                stage = stage.next_stage()
                pass
            case Stage.HIT_INSTRUCT:
                # a. Robot tells player to hit birdie   
                # TODO
                # b. Capture background frame of court (includes robot, other birdies, etc.)
                time.sleep(1)
                realsense.reset_birdies()
                realsense.capture_background() # This is the background with the static robot inside of it
                stage = stage.next_stage()
                pass
            case Stage.HIT_PLAYER:
                # a. Player hits a birdie as instructed
                # b. Camera is live, tracking position of court
                realsense.detect_birdies(visualize=True)
                # c. Look for impact
                #print("birdies landed:", realsense.get_num_birdies_landed(), num_birdies_landed)
                if realsense.get_num_birdies_landed() == 1:
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
                print("GAME OVER :F")
                # Answers questions
                pass
            case Stage.COLLECT_EVACUATE:
                # Robot drives off court in a controlled way (we need to get it back on the court again)
                pass
            case Stage.COLLECT_PLAN:
                # a. Take image
                realsense.capture_background()
                # b. Make fixed path all the way from first to last one detected
                pass
            case Stage.COLLECT_ACT:
                # a. Drive from point to point, grabbing at each stop
                # b. Don’t worry about if some weren’t collected
                # c. Return to COLLECT_EVACUATE
                pass
            


main()