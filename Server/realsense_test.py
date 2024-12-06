import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

import Server.Vision.RealsenseServer as RealsenseServer

def main():
    realsense = RealsenseServer.RealsenseServer(robotArucoId=42, courtArucoId=44)
    
    
    while True:
        realsense.detect(visualize=True)

main()