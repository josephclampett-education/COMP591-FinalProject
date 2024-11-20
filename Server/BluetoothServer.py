from pybricks.messaging import BluetoothMailboxServer, TextMailbox

def setup()
    server = BluetoothMailboxServer()
    mbox = TextMailbox('talk', server)

    print("waiting for connection...")
    server.wait_for_connection()
    print("connected.")

    mbox.wait()
    print(mbox.read())
    mbox.send("hello back!")

    return (server,mbox)