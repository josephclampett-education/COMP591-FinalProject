#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor
from pybricks.parameters import Port, Stop
from pybricks.tools import wait
from pybricks.messaging import BluetoothMailboxServer, TextMailbox

from math import atan2

ev3 = EV3Brick()

class Robot_Car:
    def __init__(self):
        self.motor_left = Motor(Port.A)
        self.motor_right = Motor(Port.B)
        self.speed = 200 
        self.location = [0, 0]
        self.orientation = 0  # [0, 2π]

    def relocate(self, x, y):
        self.location = [x, y]

    def move_forward(self, length):
        self.motor_left.run(self.speed)
        self.motor_right.run(self.speed)
        duration = length / (0.3 * self.speed)
        wait(duration * 1000)  # Convert to ms
        self.stop()

    def move_backward(self, length):
        self.motor_left.run(-self.speed)
        self.motor_right.run(-self.speed)
        duration = length / (0.3 * self.speed)
        wait(duration * 1000)  # Convert to ms
        self.stop()

    def turn_left(self, angle):
        self.motor_left.run(-self.speed)
        self.motor_right.run(self.speed)
        duration = angle / (0.47 * self.speed)
        wait(duration * 1000)  # Convert to ms
        self.stop()

    def turn_right(self, angle):
        self.motor_left.run(self.speed)
        self.motor_right.run(-self.speed)
        duration = angle / (0.47 * self.speed)
        wait(duration * 1000)  # Convert to ms
        self.stop()

    def stop(self):
        self.motor_left.stop(Stop.COAST)
        self.motor_right.stop(Stop.COAST)

    def move_to(self, x, y):
        robot_x = self.location[0]
        robot_y = self.location[1]
        robot_orientation = self.orientation

        dx = x - robot_x
        dy = y - robot_y
        angle = atan2(dy, dx) - robot_orientation
        distance = (dx**2 + dy**2)**0.5

        self.turn_left(angle)
        self.move_forward(distance)
        self.location = [x, y]
        self.orientation = atan2(dy, dx)

# if __name__ == "__main__":
#     car = Robot_Car()
#     ev3.speaker.beep()
#     car.move_to(0, 100)
#     car.move_to(100, 100)
#     car.move_to(100, 0)
#     car.move_to(0, 0)
#     car.turn_left(3.14)
#     ev3.speaker.beep()

def setup_bluetooth():
    # Setup Bluetooth mailbox server
    server = BluetoothMailboxServer()
    mbox = TextMailbox('talk', server)

    print("Waiting for Bluetooth connection...")
    ev3.screen.print("Waiting for connection...")
    server.wait_for_connection()
    print("Connected.")
    ev3.screen.print("Connected!")
    return mbox

def process_command(car, command):
    try:
        if command.startswith("MOVE"):
            _, x, y = map(int, command.split())
            car.move_to(x, y)
        elif command == "FORWARD":
            car.move_forward(50)  # Example: Move 50 units forward
        elif command == "BACKWARD":
            car.move_backward(50)
        elif command == "LEFT":
            car.turn_left(1.57)  # Example: 90 degrees (1.57 radians)
        elif command == "RIGHT":
            car.turn_right(1.57)
        elif command == "STOP":
            car.stop()
        else:
            print("Invalid command.")
            ev3.speaker.beep()
    except Exception as e:
        print("Error processing command:", e)
        ev3.speaker.beep()


if __name__ == "__main__":
    car = Robot_Car()
    mbox = setup_bluetooth()

    while True:
        command = mbox.read()
        print("Received command:", command)
        ev3.screen.clear()
        ev3.screen.print(command)
        process_command(car, command)
        mbox.send("Command executed: " + command)
