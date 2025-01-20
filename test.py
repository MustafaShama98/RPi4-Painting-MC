import smbus2
import time
import json
import statistics
from collections import deque


# I2C Sensor Settings
I2C_ADDRESS = 0x57
bus = smbus2.SMBus(1)



# Global variable for system ID

def read_distance_ultrasonic():
    """Read distance from the ultrasonic sensor via I2C."""
    try:
        bus.write_byte(I2C_ADDRESS, 0x01)  # Command to start measurement
        time.sleep(0.2)  # Allow the sensor to settle
        data = bus.read_i2c_block_data(I2C_ADDRESS, 0x00, 2)
        time.sleep(0.1)  # Delay before processing data
        distance = (data[0] << 8) | data[1]  # Combine high and low byte
        return distance / 10  # Convert mm to cm
    except Exception as e:
        print(f"Error reading sensor: {e}")
        return None

def calculate_painting_viewing_distance():
    """Stub function to calculate optimal viewing distance for a painting."""
    return 200  # Replace with actual calculation logic

def sensor_handle():
    """Simulate or read distance sensor data and publish to MQTT."""



    distance_buffer = deque(maxlen=5)
    in_range_flag = False
    consecutive_in_range = 0
    consecutive_out_of_range = 0
    REQUIRED_CONSECUTIVE = 3
    start_time_in_range = None
    first_trigger_done = False

    try:
        while True:
            distance = read_distance_ultrasonic()
            if distance is None:
                print("Error reading distance. Skipping...")
                time.sleep(0.5)
                continue

            distance_buffer.append(distance)
            if len(distance_buffer) == distance_buffer.maxlen:
                smoothed_distance = statistics.median(distance_buffer)
            else:
                smoothed_distance = distance

            if 50 <= smoothed_distance <= 150:
                consecutive_in_range += 1
                consecutive_out_of_range = 0

                if not in_range_flag and consecutive_in_range >= REQUIRED_CONSECUTIVE:
                    in_range_flag = True
                    start_time_in_range = time.time()
                    first_trigger_done = False
                    print(f"Person entered range. Distance ~{smoothed_distance} cm.")

                if in_range_flag and not first_trigger_done:
                    if time.time() - start_time_in_range >= 5:
                        payload = {
                            "status": "person_detected",
                            "distance": smoothed_distance,
                        }
                        print(f"Person confirmed in range (~{smoothed_distance} cm). Published to MQTT.")
                        first_trigger_done = True
                elif in_range_flag and first_trigger_done:
                    print(f"Person still in range (~{smoothed_distance} cm). No additional wait.")
            else:
                consecutive_out_of_range += 1
                consecutive_in_range = 0

                if in_range_flag and consecutive_out_of_range >= REQUIRED_CONSECUTIVE:
                    print(f"Person left range (~{smoothed_distance} cm). Resetting session state.")
                    in_range_flag = False
                    start_time_in_range = None
                    first_trigger_done = False

            time.sleep(1.2)

    except KeyboardInterrupt:
        print("Stopped distance sensor simulation.")

# Start the sensor handler
sensor_handle()
