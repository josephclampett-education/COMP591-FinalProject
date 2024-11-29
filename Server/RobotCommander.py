from pybricks.messaging import BluetoothMailboxClient, TextMailbox

client = BluetoothMailboxClient()
mbox = TextMailbox('talk', client)

print("Connecting to EV3...")
print("Connecting to EV3...")
try:
    client.connect('00:17:E9:F8:C1:77')
    print("Connected successfully!")
except OSError as e:
    print(f"Connection failed: {e}")
print("Connected!")

commands = ["FORWARD", "LEFT", "MOVE 100 100", "STOP"]
for cmd in commands:
    print(f"Sending: {cmd}")
    mbox.send(cmd)
    mbox.wait()  # Wait for EV3's confirmation
    print("Response:", mbox.read())
