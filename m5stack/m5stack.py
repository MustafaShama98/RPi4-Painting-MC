
import os
import json
import time
import base64
import asyncio
import ssl
import certifi
import cv2
import paho.mqtt.client as mqtt


# Global variables
mqtt_client = None
sys_id = None
waiting_for_sys_id = False
file_name = "system_data.json"



# MQTT Setup
def mqtt_setup():
    global mqtt_client
    print('MQTT setup!')
        # Configure the LWT (Last Will and Testament)

    mqtt_client = mqtt.Client(client_id=f"m5stack{hex(int(time.time() * 1000))[2:]}", protocol=mqtt.MQTTv311)
    mqtt_client.username_pw_set("art", "art123")
    context = ssl.create_default_context(cafile=certifi.where())
    mqtt_client.tls_set_context(context=context)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.on_disconnect = on_disconnect

    mqtt_client.connect("j81f31b4.ala.eu-central-1.emqxsl.com", port=8883)
    mqtt_client.loop_forever()

    # Subscribe to topics if sys_id is already set
    if sys_id:
        subscribe_to_sys_id_topics()



# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("\nConnected to MQTT broker")
        payload = read_data()
        if not payload or not payload.get("sys_id"):
            client.subscribe("install", qos=2)
            print("Subscribed to /install topic")
        else: 
            subscribe_to_sys_id_topics()

    else:
        print(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    print(f"\nReceived message on topic: {msg.topic}: {msg.payload.decode()}")
    try:
        payload = json.loads(msg.payload.decode())
        
        # Check for specific topic patterns
        if "install" in msg.topic:
            handle_installation(payload)
        elif "height" in msg.topic:
            handle_height(payload)
        else:
            print(f"Unhandled topic: {msg.topic}")
    except Exception as e:
        print(f"Error processing message: {e}")

def on_disconnect(client, userdata, rc):
    print("Disconnected from MQTT broker with result code:", rc)
    print("Unexpected disconnection. Publishing 'Inactive' status.")
    client.publish(f"m5stack/{sys_id}/active", json.dumps({"status": False}), qos=1, retain=True)
    print("published inactive status")


def read_data():
    """Read data synchronously from JSON file."""
    # file_name = os.path.join(os.getcwd(), "system_data.json")
    return asyncio.run(read_from_json_file_async())

def subscribe_to_sys_id_topics():
    """Subscribe to topics for the current sys_id."""
    if sys_id:
        mqtt_client.subscribe(f"m5stack/{sys_id}/delete", qos=2)
        mqtt_client.subscribe(f"m5stack/{sys_id}/height", qos=2)
        print(f"Subscribed to height, delete, height topics")


# Handlers
def handle_installation(payload):
    global sys_id
    sys_id = payload.get("sys_id")
    print(f"System installed with sys_id: {sys_id}")
    mqtt_client.publish(f"m5stack/{sys_id}/install", json.dumps({"device": "esp32", "success": True}), qos=2)
    asyncio.run(write_to_json_file_async(payload))
    mqtt_client.unsubscribe("install")
    subscribe_to_sys_id_topics()

def handle_height(payload):
    global sys_id
    height = payload
    print(f"height adjustment needed: ",height)
    mqtt_client.publish(f"m5stack/{sys_id}/height_done", json.dumps({"device": "m5stack", "success": True}), qos=2)

def handle_deletion():
    global sys_id
    sys_id = None
    try:
        os.remove(file_name)
        print("System deleted and file removed.")
        mqtt_client.subscribe("install", qos=2)
        print("Subscribed to /install topic")
    except FileNotFoundError:
        print("File not found. No system data to delete.")

async def write_to_json_file_async(data):
    """Asynchronously write data to a JSON file."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: json.dump(data, open(file_name, "w"), indent=4))

async def read_from_json_file_async():
    """Asynchronously read data from a JSON file."""
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, lambda: json.load(open(file_name, "r")))
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def initialize_sys_id():
    """Initialize sys_id from the JSON file if it exists."""
    global sys_id
    # file_name = os.path.join(os.getcwd(), file_name)
    try:
        payload = asyncio.run(read_from_json_file_async())
        if payload and "sys_id" in payload:
            sys_id = payload["sys_id"]
            print(f"Loaded sys_id from file: {sys_id}")
        else:
            print("No sys_id found in JSON file.")
    except Exception as e:
        print(f"Error initializing sys_id: {e}")


def main():
    initialize_sys_id()  # Load sys_id from file
    mqtt_setup()
    

if __name__ == "__main__":
    main()