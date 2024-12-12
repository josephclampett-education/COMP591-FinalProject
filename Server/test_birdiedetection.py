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
from Server.Path import next_collection_target
from Server.Lesson import make_lesson

def main():

    realsense = RealsenseServer.RealsenseServer(robotArucoId=180, courtArucoId=181)
    
    collectionBirdies = []
    while True:
        # Here perform actions that should be executed all the time
        realsense.detect_arucos()
        
        collectionBirdies = realsense.detect_collection_birdies(visualize = True)

if __name__ == "__main__":
    main()