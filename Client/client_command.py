from pybricks.messaging import BluetoothMailboxClient, TextMailbox

client = BluetoothMailboxClient()
mbox = TextMailbox('talk', client)

print("Connecting to EV3...")
client.connect('ev3_name')  # Replace 'ev3_name' with your EV3 Bluetooth name
print("Connected!")

commands = ["FORWARD", "LEFT", "MOVE 100 100", "STOP"]
for cmd in commands:
    print(f"Sending: {cmd}")
    mbox.send(cmd)
    mbox.wait()  # Wait for EV3's confirmation
    print("Response:", mbox.read())
