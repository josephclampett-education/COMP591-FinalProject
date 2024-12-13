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
hitBox = TextMailbox('hit', server)

# The server must be started before the client!
print('waiting for connection...')
server.wait_for_connection()
print('connected!')


# In this program, the server waits for the client to send the first message
# and then sends a reply.
while True:
    commandBox.wait()
    command = commandBox.read()

    print('Read')

    if command.startswith("LEFT"):
        print('LEFT')
        robot.drive(0, -10)
    elif command.startswith("RIGHT"):
        print('RIGHT')
        robot.drive(0, 10)
    elif command == "END":
        print('END')
        ev3.speaker.beep()
        grab_motor.run_angle(90, 90) #TODO
        break
    elif command == "GRAB":
        print('GRAB')
        grab_motor.run_angle(90, 90)
        wait(100)
    elif command.startswith("FORWARD"):
        print('FORWARD')
        angle = float(command.split()[1])
        robot.drive(50, angle)
    elif command == "STOP":
        robot.stop()
    elif command.startswith("WHEEL"):
        turns = float(command.split()[1])
        robot.straight(turns)

    print('PreSend')
    # commandBox.send('received' + command)

    # hitBox.send('hit')