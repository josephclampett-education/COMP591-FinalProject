import sys
import os
import time

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)
import Server.RobotCommander as RobotCommander

robot = RobotCommander.RobotCommander()
robot.send_command(RobotCommander.ResetGrabberAngle())
for i in range(5):
    if i % 2 == 0:
        robot.send_command("RIGHT")
    else:
        robot.send_command("LEFT")
    time.sleep(3)
    robot.send_command("FORWARD 1")
    time.sleep(1)
robot.send_command("END")