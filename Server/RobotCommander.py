from pybricks.messaging import BluetoothMailboxClient, TextMailbox

class RobotCommander:
    def __init__(self):
        self.client = BluetoothMailboxClient()
        self.mbox = TextMailbox('talk', self.client)

        print("Connecting to EV3...")
        try:
            self.client.connect('00:17:E9:F8:C1:77')
            print("Connected successfully!")
        except OSError as e:
            print(f"Connection failed: {e}")
        print("Connected!")

    def send_command(self, command):
        # commands = ["FORWARD", "LEFT", "MOVE 100 100", "STOP"]
        # for cmd in commands:
        print(f"Sending: {cmd}")
        self.mbox.send(cmd)
        self.mbox.wait()  # Wait for EV3's confirmation
        print("Response:", self.mbox.read())
