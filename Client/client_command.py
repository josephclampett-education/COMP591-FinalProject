from pybricks.messaging import BluetoothMailboxClient, TextMailbox

client = BluetoothMailboxClient()
mbox = TextMailbox('talk', client)

print("Connecting to EV3...")
while client.connect('00:17:E9:F8:C1:77') == 'None':
    print("Failed to connect. Retrying...")

print("Connected!")

commands = ["FORWARD", "LEFT", "MOVE 100 100", "STOP"]
for cmd in commands:
    print(f"Sending: {cmd}")
    mbox.send(cmd)
    mbox.wait()  # Wait for EV3's confirmation
    print("Response:", mbox.read())
