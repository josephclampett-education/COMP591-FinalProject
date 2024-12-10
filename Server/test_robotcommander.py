import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

import RobotCommander

def main():
    commander = RobotCommander.RobotCommander()
    
    commander.send_command(RobotCommander.Stop())

main()