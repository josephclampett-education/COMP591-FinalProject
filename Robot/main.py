#!/usr/bin/env pybricks-micropython

# Before running this program, make sure the client and server EV3 bricks are
# paired using Bluetooth, but do NOT connect them. The program will take care
# of establishing the connection.

# The server must be started before the client!

from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor
from pybricks.parameters import Port
from pybricks.robotics import DriveBase
from pybricks.messaging import BluetoothMailboxServer, TextMailbox
from pybricks.tools import wait

# Initialize the EV3 Brick.
ev3 = EV3Brick()

# Initialize the motors.
left_motor = Motor(Port.A)
right_motor = Motor(Port.B)

grab_motor = Motor(Port.C)

# Initialize the drive base.
robot = DriveBase(left_motor, right_motor, wheel_diameter=54.0, axle_track=119)

server = BluetoothMailboxServer()
commandBox = TextMailbox('command', server)
# hitBox = TextMailbox('hit', server)

# The server must be started before the client!
# print('waiting for connection...')
server.wait_for_connection()
# print('connected!')

def close_grabber():
    if abs(grab_motor.angle()) < 5:
        grab_motor.run_target(45, -45, wait=False)

def open_grabber():
    if abs(grab_motor.angle()) > 3:
        grab_motor.run_target(45, 0, wait=False)


# In this program, the server waits for the client to send the first message
# and then sends a reply.
while True:
    commandBox.wait()
    command = commandBox.read()

    # print('Read')

    if command.startswith("LEFT"):
        # print('LEFT')
        close_grabber()
        robot.drive(0, -20)
    elif command.startswith("RIGHT"):
        # print('RIGHT')
        close_grabber()
        robot.drive(0, 20)
    elif command == "BEEP":
        # print('END')
        ev3.speaker.beep()
    elif command == "END":
        # print('END')
        ev3.speaker.beep(frequency=600)
        ev3.speaker.beep(frequency=700)
        ev3.speaker.beep(frequency=800)
        open_grabber()
        break
    elif command.startswith("FORWARD"):
        # print('FORWARD')
        angle = float(command.split()[1])
        open_grabber()
        robot.drive(80, angle)
    elif command == "STOP":
        robot.stop()
    elif command.startswith("WHEEL"):
        robot.stop()
        open_grabber()
        turns = float(command.split()[1])
        robot.straight(turns)
    elif command.startswith("RESET_GRABBER_ANGLE"):
        grab_motor.reset_angle(0)
    elif command == "FAIL":
        ev3.speaker.beep(frequency=600)
        ev3.speaker.beep(frequency=400)

    # print('PreSend')
    # commandBox.send('received' + command)

    # hitBox.send('hit')