
import os
import json
import time
import base64
import asyncio
import ssl
import certifi
import cv2
import paho.mqtt.client as mqtt
import math
import numpy as np
import socket
import time
import statistics
import logging
from collections import deque
# from picamera2 import Picamera2
import sys
import signal
#from sensor import get_distance_tof
from sensor_logic import read_distance_ultrasonic
# Global variables
mqtt_client = None
sys_id = None
waiting_for_sys_id = False
script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the script
file_name = os.path.join(script_dir, "system_data.json")  # Build the absolute path



# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set the logging level
    format='%(asctime)s - %(message)s',  # Include the timestamp
    datefmt='%Y-%m-%d %H:%M:%S'  # Timestamp format
)

def handle_exit(signum, frame):
    """Handle system shutdown or script termination."""
    global mqtt_client, sys_id
    logging.info("Caught termination signal. Sending inactive MQTT message...")
    if mqtt_client and sys_id:
        mqtt_client.publish(f"m5stack/{sys_id}/active", json.dumps({"status": False}), qos=1, retain=True)
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    logging.info("Cleanup complete. Exiting...")
    sys.exit(0)




def wait_for_network(timeout=30):
    """Wait until the network is ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            socket.create_connection(("j81f31b4.ala.eu-central-1.emqxsl.com", 8883), timeout=5)
            logging.info("Network is ready!")
            return True
        except (socket.timeout, socket.gaierror):
            logging.info("Waiting for network...")
            time.sleep(5)
    logging.info("Network not ready within timeout.")
    return False


def calculate_painting_viewing_distance():
    """

    Calculate the optimal viewing distance for a painting.

    Parameters:
        diagonal (float): Diagonal size of the painting in cm.

    Returns:
        float: Optimal viewing distance in the same unit as the diagonal.
    """
    # Optimal distance is 2 times the diagonal size
    payload =  read_data()
    if payload:
        width =payload.get("width")
        height = payload.get("height")
        logging.info(type(width))
        diagonal = math.sqrt(width**2 + height**2)
        logging.info(f"distance {diagonal * 1.5}")
        return 1.6 * diagonal
    return None





def sensor_handle():
    """Simulate or read distance sensor data and publish to MQTT."""
    global sys_id
    if not sys_id:
        logging.info("No system ID set. Cannot publish sensor data.")
        return

    optimal_distance = calculate_painting_viewing_distance()
    logging.info(f"The range is 50 to {optimal_distance} to detect.")

    # Rolling buffer for smoothing (median of last 5 readings)
    distance_buffer = deque(maxlen=5)

    # Hysteresis/counters
    in_range_flag = False
    consecutive_in_range = 0
    consecutive_out_of_range = 0
    REQUIRED_CONSECUTIVE = 4  # Number of consecutive stable readings needed

    # Timing for 5-second confirm
    start_time_in_range = None
    first_trigger_done = False

    try:
        while True:
            distance = read_distance_ultrasonic()
            distance_buffer.append(distance)
            logging.info(distance)
            # Only proceed if buffer is filled (for stable median)
            if len(distance_buffer) == distance_buffer.maxlen:
                smoothed_distance = statistics.median(distance_buffer)
            else:
                smoothed_distance = distance

            if 50 <= smoothed_distance <= 155:
                # Count in-range
                consecutive_in_range += 1
                consecutive_out_of_range = 0

                # Switch to in-range if stable
                if not in_range_flag and consecutive_in_range >= REQUIRED_CONSECUTIVE:
                    in_range_flag = True
                    start_time_in_range = time.time()
                    first_trigger_done = False
                    logging.info(f"Person entered range. Distance ~{smoothed_distance} cm.")

                # If in range and not triggered yet, check 5-second confirmation
                if in_range_flag and not first_trigger_done:
                    if time.time() - start_time_in_range >= 5:
                        payload = {
                            "status": "person_detected",
                            "distance": smoothed_distance,
                        }
                        mqtt_client.publish(f"m5stack/{sys_id}/sensor", json.dumps({"status" : "in"}), qos=2)
                        logging.info(f"Person confirmed in range (~{smoothed_distance} cm). Published to MQTT.")
                        first_trigger_done = True
                elif in_range_flag and first_trigger_done:
                    logging.info(f"Person still in range (~{smoothed_distance} cm). No additional wait.")
            else:
                # Count out-of-range
                consecutive_out_of_range += 1
                consecutive_in_range = 0

                # Switch to out-of-range if stable
                if in_range_flag and consecutive_out_of_range >= REQUIRED_CONSECUTIVE:
                    logging.info(f"Person left range (~{smoothed_distance} cm). Resetting session state.")
                    mqtt_client.publish(f"m5stack/{sys_id}/sensor", json.dumps({"status" : "left"}), qos=2)
                    in_range_flag = False
                    start_time_in_range = None
                    first_trigger_done = False

            time.sleep(1.2)

    except KeyboardInterrupt:
        logging.info("Stopped distance sensor simulation.")



# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("\nConnected to MQTT broker")
        payload = read_data()
        if not payload or not payload.get("sys_id"):
            client.subscribe("install", qos=2)
            logging.info("Subscribed to /install topic")
        else:
            client.subscribe("status", qos=2)
            logging.info("Subscribed to /status topic")
            handle_status_request()

    else:
        logging.info(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    logging.info(f"\nReceived message on topic: {msg.topic}: {msg.payload.decode()}")
    try:
        payload = json.loads(msg.payload.decode())
        
        # Check for specific topic patterns
        if "get_frame" in msg.topic:
            handle_frame_request(msg.topic)
        elif "delete" in msg.topic:
            handle_deletion()
        elif "reset" in msg.topic:
            handle_reset()
        elif "status" in msg.topic:
            handle_status_request()
        elif "install" in msg.topic:
            handle_installation(payload)
        else:
            logging.info(f"Unhandled topic: {msg.topic}")
    except Exception as e:
        logging.info(f"Error processing message: {e}")

def on_disconnect(client, userdata, rc):
    logging.info("Disconnected from MQTT broker with result code:", rc)
    logging.info("Unexpected disconnection. Publishing 'Inactive' status.")
    client.publish(f"m5stack/{sys_id}/active", json.dumps({"status": False}), qos=1, retain=True)
    logging.info("published inactive status")


#capture frame when using windows for dev and testing
def capture_frame():
    """Capture a frame from the default camera and return as base64."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Failed to open camera")

    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise RuntimeError("Failed to capture frame")

    _, buffer = cv2.imencode(".jpg", frame)
    return base64.b64encode(buffer).decode("utf-8")

#capture frame when using rpi camera module v2
def capture_frame_rpi():
    from picamera2 import Picamera2

    picam2 = Picamera2()
    config = picam2.create_still_configuration(main={"format": "RGB888","size": picam2.sensor_resolution})  # Smaller resolution
    picam2.configure(config)

    picam2.start()
    frame = picam2.capture_array()
    picam2.stop()
    picam2.close()  # Ensure the camera is properly released

    # Resize the frame
    frame = cv2.resize(frame, (1280, 720))  # Adjust to smaller size

    # Encode the frame as JPEG
    _, buffer = cv2.imencode(".jpg", frame)
    return base64.b64encode(buffer).decode("utf-8")

async def write_to_json_file_async(data):
    """Asynchronously write data to a JSON file."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: json.dump(data, open(file_name, "w"), indent=4))

def read_from_json_file():
    """Read data from a JSON file synchronously."""
    try:
        with open(file_name, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def read_data():
    """Read data synchronously from JSON file."""
    try:
        with open(file_name, "r") as f:
            data = json.load(f)
            logging.info("Data read from file:", data)  # Debugging
            return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.info(f"Error reading JSON file: {e}")
        return None



def subscribe_to_sys_id_topics():
    """Subscribe to topics for the current sys_id."""
    if sys_id:
        mqtt_client.subscribe(f"m5stack/{sys_id}/delete", qos=2)
        mqtt_client.subscribe(f"m5stack/{sys_id}/get_frame", qos=2)
        mqtt_client.subscribe(f"status", qos=2)

        logging.info(f"Subscribed to delete, getframe, height, status")


# Handlers
def handle_installation(payload):
    global sys_id
    sys_id = payload.get("sys_id")
    logging.info(f"System installed with sys_id: {sys_id}")
    mqtt_client.publish(f"m5stack/{sys_id}/install", json.dumps({"device": "esp32", "success": True}), qos=2)
    asyncio.run(write_to_json_file_async(payload))
    mqtt_client.unsubscribe("install")
    subscribe_to_sys_id_topics()

def handle_frame_request(topic):
    """Handle frame requests."""
    global sys_id
    _, sys_id, _ = topic.split("/")
    # Determine the operating system
    if os.name == "posix":
        base64_image = capture_frame_rpi()
    else:
        base64_image = capture_frame()
    logging.info(f"Payload size: {len(base64_image)} bytes")
    payload = {"frameData": base64_image, "timestamp": time.time()}
    response_topic = f"m5stack/{sys_id}/frame_response"
    mqtt_client.publish(response_topic, json.dumps(payload), qos=2)
    logging.info(f"Published frame data to {response_topic}")

def handle_deletion():
    global sys_id
    sys_id = None
    try:
        os.remove(file_name)
        logging.info("System deleted and file removed.")
        mqtt_client.subscribe("install", qos=2)
        logging.info("Subscribed to /install topic")
    except FileNotFoundError:
        logging.info("File not found. No system data to delete.")

def handle_reset():
    global sys_id
    sys_id = None
    logging.info("System reset.")

def handle_status_request():
    logging.info(f"System {'is active' if sys_id else 'is not installed'} with sys_id: {sys_id or 'N/A'}")
    mqtt_client.publish(f"m5stack/{sys_id}/active", json.dumps({"status" : True}), qos=2)
    logging.info("sent status active")

def publish_status_inactive():
    logging.info(f"System {'is active' if sys_id else 'is not installed'} with sys_id: {sys_id or 'N/A'}")
    mqtt_client.publish(f"m5stack/{sys_id}/active", json.dumps({"status" : False}), qos=2)
    logging.info("sent status inactive")


def initialize_sys_id():
    """Initialize sys_id from the JSON file if it exists."""
    global sys_id
    # file_name = os.path.join(os.getcwd(), file_name)
    try:
        payload = read_from_json_file()
        if payload and "sys_id" in payload:
            sys_id = payload["sys_id"]
            logging.info(f"Loaded sys_id from file: {sys_id}")
        else:
            logging.info("No sys_id found in JSON file.")
    except Exception as e:
        logging.info(f"Error initializing sys_id: {e}")




# MQTT Setup
def mqtt_setup():
    global mqtt_client
    logging.info('MQTT setup!')
        # Configure the LWT (Last Will and Testament)
    try:
        mqtt_client = mqtt.Client(client_id=f"esp32_{hex(int(time.time() * 1000))[2:]}", protocol=mqtt.MQTTv311)
        mqtt_client.username_pw_set("art", "art123")
        context = ssl.create_default_context(cafile=certifi.where())
        mqtt_client.tls_set_context(context=context)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.on_disconnect = on_disconnect

        mqtt_client.will_set(
            topic=f"m5stack/{sys_id}/active",
            payload=json.dumps({"status": False}),
            qos=2,
            retain=True
        )

        for attempt in range(5):  # Retry up to 5 times
            try:
                logging.info(f"Attempt {attempt + 1}: Connecting to MQTT broker...")
                mqtt_client.connect("j81f31b4.ala.eu-central-1.emqxsl.com", port=8883)
                mqtt_client.loop_start()
                logging.info("MQTT connected successfully.")
                break
            except Exception as e:
                logging.info(f"MQTT connection attempt {attempt + 1} failed: {e}")
                time.sleep(10)
        else:
            logging.info("Failed to connect to MQTT broker after 5 attempts.")

        # Subscribe to topics if sys_id is already set
        if sys_id:
            subscribe_to_sys_id_topics()
    except Exception as e:
     logging.info(f"MQTT connection failed: {e}")

# Command Interface
def command_interface():
    global sys_id, waiting_for_sys_id
    if not sys.stdin.isatty():
        logging.info("Running in non-interactive mode. Skipping command interface.")
        return
    commands = {
        "status": lambda: handle_status_request(),
        "reset": lambda: handle_reset(),
        "delete": lambda: handle_deletion(),
        "help": lambda: logging.info("Available commands: status, reset, delete, set_id, sensor, exit"),
        "sensor": lambda: publish_sensor_data() if sys_id else logging.info("No system ID set."),
        "simulate": lambda: sensor_handle() if sys_id else logging.info("No system ID set."),
        "set_id": lambda: set_system_id(),
        "exit": lambda: exit_simulation(),
    }

    def set_system_id():
        global waiting_for_sys_id
        waiting_for_sys_id = True
        logging.info("Enter the system ID:")

    def publish_sensor_data():
        payload = {"value": "50", "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), "device": "esp32"}
        mqtt_client.publish(f"m5stack/{sys_id}/sensor", json.dumps(payload), qos=2)
        logging.info("Sensor data published.")

    def exit_simulation():
        logging.info("Exiting...")
        mqtt_client.publish(f"m5stack/{sys_id}/active", json.dumps({"status": False}), qos=1, retain=True)
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        exit(0)

    while True:
        try:
            time.sleep(1)  # Sleep to reduce CPU usage
            user_input = input("\nEnter command: ").strip().lower()
            if waiting_for_sys_id:
                sys_id = user_input
                logging.info(f"System ID manually set to: {sys_id}")
                waiting_for_sys_id = False
                subscribe_to_sys_id_topics()
                continue
            commands.get(user_input, lambda: logging.info("Unknown command. Type 'help' for commands."))()
        except KeyboardInterrupt:
            exit_simulation()

def main():
    calculate_painting_viewing_distance()
    initialize_sys_id()  # Load sys_id from file
    if wait_for_network():
        mqtt_setup()
        # Register signal handlers
        signal.signal(signal.SIGTERM, handle_exit)  # Handle termination (e.g., `kill` or shutdown)
        signal.signal(signal.SIGINT, handle_exit)   # Handle interrupt (e.g., Ctrl+C)
    else:
        logging.info("Network not ready. Exiting.")
        return
    logging.info(os.name)
    # Check if running in interactive mode
    if sys.stdin.isatty():
        logging.info("Running in interactive mode. Starting command interface...")
        command_interface()
    else:
        logging.info("Running in non-interactive mode. Keeping the script alive for MQTT...")
        try:
            while True:
                time.sleep(1)  # Prevent CPU overuse
        except KeyboardInterrupt:
            logging.info("Exiting...")
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
    

if __name__ == "__main__":
    main()


