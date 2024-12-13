import sys
import os
from enum import Enum, auto
import time
# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

import Server.Vision.RealsenseServer as RealsenseServer


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
        print("Stage changed to: ", stage[(self.value - 1 + 1) % len(stage)])
        return stage[(self.value - 1 + 1) % len(stage)]


def main():
    realsense = RealsenseServer.RealsenseServer(robotArucoId=180, courtArucoId=181)
    
    
    # initialize Stage controll enum
    stage = Stage.STARTUP_COURT
    BIRDIES_PER_ROUND = 5
    num_birdies_landed = 0
    print("Start!!!")
    while True:

        # Here perform actions that should be executed all the time
        realsense.detect_arucos()



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
                realsense.capture_hit_background()
                # b. Make fixed path all the way from first to last one detected
                pass
            case Stage.COLLECT_ACT:
                # a. Drive from point to point, grabbing at each stop
                # b. Don’t worry about if some weren’t collected
                # c. Return to COLLECT_EVACUATE
                pass
            


main()