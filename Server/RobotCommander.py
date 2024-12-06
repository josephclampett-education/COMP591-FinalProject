from pybricks.messaging import BluetoothMailboxClient, TextMailbox
from enum import StrEnum
import math
from Server.Location import Position

class Direction(StrEnum):
    RIGHT = "RIGHT"
    LEFT = "LEFT"

class Turn:
    def __init__(self, radians):
        self.direction = Direction.LEFT if radians > 0 else Direction.RIGHT
        self.radians = math.abs(radians)

    def __str__(self):
        return f"{self.direction} {math.degrees(self.radians)}"

class Forward:
    def __init__(self, robot_location: Position, target: Position):
        self.distance = robot_location.flat_distance(target)

    def __str__(self):
        return f"FORWARD {self.distance}"

class Stop:
    def __str__(self):
        return "STOP"

class Move:
    def __init__(self, position: Position):
        self.position = position

    def __str__(self):
        return f"MOVE {self.position.x} {self.position.y}"

class RobotCommander:
    def __init__(self):
        self.client = BluetoothMailboxClient()
        self.commandBox = TextMailbox('command', self.client)
        self.hitBox = TextMailbox('hit', self.client)

        print("Connecting to EV3...")
        try:
            self.client.connect('00:17:E9:F8:C1:77')
            print("Connected successfully!")
        except OSError as e:
            print(f"Connection failed: {e}")

    def send_command(self, cmd):
        # commands = ["FORWARD", "LEFT", "MOVE 100 100", "STOP"]
        # for cmd in commands:
        self.commandBox.send(cmd.__str__())
        print(f"Sending: {cmd}")
        self.commandBox.wait()  # Wait for EV3's confirmation
        self.hitBox.wait()
        print("CResponse:", self.commandBox.read())
        print("HResponse:", self.hitBox.read())
