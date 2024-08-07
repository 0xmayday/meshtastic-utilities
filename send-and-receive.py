import meshtastic.serial_interface
import meshtastic.util as mesh_utils
import sys
from pubsub import pub
from collections import deque

interface = meshtastic.serial_interface.SerialInterface()
id_to_name_mappings = {}
nodes = interface.nodesByNum

# Define a limit for the number of messages to keep in memory
MESSAGE_LIMIT = 100
message_history = deque(maxlen=MESSAGE_LIMIT)

for node in nodes.values():
    # Use get() method to safely access the 'user' dictionary
    user_info = node.get('user', {})
    node_canonical_id = user_info.get('id', 'unknown_id')
    long_name = user_info.get('longName', 'unknown_name')

    # Add to the dictionary if both values are found
    if node_canonical_id != 'unknown_id' and long_name != 'unknown_name':
        id_to_name_mappings[node_canonical_id] = long_name

def onReceive(packet, interface):
    try:
        if 'decoded' in packet and packet['decoded']['portnum'] == 'TEXT_MESSAGE_APP':
            channel_name = interface.localNode.channels[packet.get('channel', 0)].settings.name
            from_id = packet['fromId']
            long_name = id_to_name_mappings.get(from_id, from_id)
            message_bytes = packet['decoded']['payload']
            message_string = message_bytes.decode('utf-8')
            message = f"<< [{channel_name}//{long_name}] - {message_string}"
            
            # Add the message to history and print it
            message_history.append(message)
            print(f"\n{message} \n> ", end="", flush=True)
    except KeyError as e:
        print(f"Error processing packet: {e}")

pub.subscribe(onReceive, 'meshtastic.receive')

def send_message(message, channel_id):
    interface.sendText(message, channelIndex=channel_id)

def show_channels():
    print("Available channels:")
    for idx, channel in enumerate(interface.localNode.channels):
        channel_name = channel.settings.name
        if channel_name:
            print(f"Index: {idx}, Name: {channel_name}")

def show_nodes():
    for node in interface.nodes.values():
        user_info = node.get('user', {})
        print("Node ID:", user_info.get('id', 'UNSET'))
        print("Long Name:", user_info.get('longName', 'UNSET'))
        print("Short Name:", user_info.get('shortName', 'UNSET'))
        print("MAC Address:", user_info.get('macaddr', 'UNSET'))
        print("Hardware Model:", user_info.get('hwModel', 'UNSET'))

        if "snr" in node:
            print("SNR:", node["snr"])
        if "lastHeard" in node:
            print("Last Heard:", node["lastHeard"])
        if "hopsAway" in node:
            print("Hops Away:", node["hopsAway"])

        if "position" in node:
            if "latitude" in node["position"]:
                print("Latitude:", node["position"]["latitude"])
            if "longitude" in node["position"]:
                print("Longitude:", node["position"]["longitude"])
            if "altitude" in node["position"]:
                print("Altitude:", node["position"]["altitude"])
            if "time" in node["position"]:
                print("Time:", node["position"]["time"])

        if "deviceMetrics" in node:
            if "batteryLevel" in node["deviceMetrics"]:
                print("Battery Level:", node["deviceMetrics"]["batteryLevel"])
            if "voltage" in node["deviceMetrics"]:
                print("Voltage:", node["deviceMetrics"]["voltage"])
            if "channelUtilization" in node["deviceMetrics"]:
                print("Channel Utilization:", node["deviceMetrics"]["channelUtilization"])
            if "airUtilTx" in node["deviceMetrics"]:
                print("Air Util Tx:", node["deviceMetrics"]["airUtilTx"])

        print("\n")

def show_help():
    print("Available commands:")
    print("show channels        - Display available channels")
    print("change channel <index> - Change to the specified channel")
    print("show nodes           - Display information about all nodes")
    print("help                 - Show this help message")

# Initial message
print("Meshtastic Radio Interface: Type 'help' to see the list of commands.")

# Set default channel to channel 0
channel_id = 0

# Display the default channel name
default_channel_name = interface.localNode.channels[channel_id].settings.name
print(f"Default channel is set to [0: {default_channel_name}]")

while True:
    current_channel_name = interface.localNode.channels[channel_id].settings.name
    text = input(f"[{current_channel_name}]> ")
    if text.startswith("show channels"):
        show_channels()
    elif text.startswith("change channel"):
        try:
            _, _, new_channel_id = text.split()
            new_channel_id = int(new_channel_id)
            if 0 <= new_channel_id < len(interface.localNode.channels):
                channel_id = new_channel_id
                new_channel_name = interface.localNode.channels[channel_id].settings.name
                print(f"Changed to channel [{channel_id}: {new_channel_name}]")
            else:
                print(f"Invalid channel index. Please enter a number between 0 and {len(interface.localNode.channels) - 1}.")
        except ValueError:
            print("Invalid command format. Use 'change channel <index>'.")
    elif text.startswith("show nodes"):
        show_nodes()
    elif text.startswith("help"):
        show_help()
    else:
        send_message(text, channel_id)
