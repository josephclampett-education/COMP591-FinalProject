#!/usr/bin/env pybricks-micropython

# Before running this program, make sure the client and server EV3 bricks are
# paired using Bluetooth, but do NOT connect them. The program will take care
# of establishing the connection.

# The server must be started before the client!

from pybricks.messaging import BluetoothMailboxServer, TextMailbox
import control

robot = control.Robot_Car()

server = BluetoothMailboxServer()
mbox = TextMailbox('greeting', server)

# The server must be started before the client!
print('waiting for connection...')
server.wait_for_connection()
print('connected!')

# In this program, the server waits for the client to send the first message
# and then sends a reply.
while True:
    mbox.wait()
    command = mbox.read()
    mbox.send(f'received {command}')
    match command:
        case "LEFT":
            robot.turn_left(90)
        case "RIGHT":
            robot.turn_right(90)
        case "END":
            robot.stop()
            break
