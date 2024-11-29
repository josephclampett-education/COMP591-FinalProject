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
robot = DriveBase(left_motor, right_motor, wheel_diameter=55.5, axle_track=104)

server = BluetoothMailboxServer()
mbox = TextMailbox('talk', server)

# The server must be started before the client!
print('waiting for connection...')
server.wait_for_connection()
print('connected!')

# In this program, the server waits for the client to send the first message
# and then sends a reply.
while True:
    mbox.wait()
    command = mbox.read()
        
    print('Read')

    if command == "LEFT":
        print('LEFT')
        robot.turn(-360)
    elif command == "RIGHT":
        print('RIGHT')
        robot.turn(360)
    elif command == "END":
        print('END')
        ev3.speaker.beep()
        break
    elif command == "GRAB":
        print('GRAB')
        grab_motor.run(-20)
        wait(100)
    else:
        print('STRAIGHT')
        robot.straight(100)

    print('PreSend')
    mbox.send('received' + command)