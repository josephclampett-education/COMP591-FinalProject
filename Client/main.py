#!/usr/bin/env pybricks-micropython

# The server must be started before the client!

from pybricks.messaging import BluetoothMailboxClient, TextMailbox

def connect(server_address):
    # This is the name of the remote PC we are connecting to.
    SERVER = server_address

    client = BluetoothMailboxClient()
    mbox = TextMailbox("greeting", client)

    print("establishing connection...")
    client.connect(SERVER)
    print("connected!")

    mbox.send("hello!")
    mbox.wait()
    print(mbox.read())

    return mbox
