import smbus2
import time
import json
import statistics
from collections import deque


# I2C Sensor Settings
I2C_ADDRESS = 0x57
bus = smbus2.SMBus(1)

def calculate_distance(pulse_time, temperature=20, offset=5):
    """
    Calculate distance based on the pulse time, temperature, and calibration offset.
    """
    try:
        # Debugging input values

        # Validate inputs
        if pulse_time is None or pulse_time <= 0:
            raise ValueError(f"Invalid pulse_time: {pulse_time}")
        if not isinstance(temperature, (int, float)):
            raise ValueError(f"Invalid temperature: {temperature}")

        # Adjust speed of sound for temperature
        speed_of_sound = 331.3 + (0.606 * temperature)  # m/s
        speed_of_sound_cm_s = speed_of_sound * 100      # Convert to cm/s

        # Calculate distance
        raw_distance = (pulse_time * speed_of_sound_cm_s) / 2
        calibrated_distance = raw_distance + offset
        #print(f"[DEBUG] Raw distance: {raw_distance} cm, Calibrated distance: {calibrated_distance} cm")

        return calibrated_distance
    except Exception as e:
        print(f"[ERROR] Error in calculate_distance: {e}")
        return None

def read_distance_ultrasonic(temperature=20):
    """
    Read distance from the ultrasonic sensor via I2C and calculate the distance using the formula.
    """
    try:
        # Command the sensor to start measurement
        bus.write_byte(I2C_ADDRESS, 0x01)
        time.sleep(0.2)  # Allow the sensor to settle

        # Read 2 bytes of data (time in microseconds)
        data = bus.read_i2c_block_data(I2C_ADDRESS, 0x00, 2)
        time.sleep(0.1)  # Delay before processing data

        # Combine high and low byte to get the pulse time in microseconds
        pulse_time_us = (data[0] << 8) | data[1]

        # Convert pulse time to seconds
        pulse_time_s = pulse_time_us / 1_000_000

        # Calculate distance using the formula
        distance = calculate_distance(pulse_time_s, temperature)
        return distance  # Return distance in cm
    except Exception as e:
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
                #print("Error reading distance. Skipping...")
                time.sleep(0.4)
                continue

            distance_buffer.append(distance)
            print(distance)
            if len(distance_buffer) == distance_buffer.maxlen:
                smoothed_distance = statistics.median(distance_buffer)
            else:
                smoothed_distance = distance

            if 50 <= smoothed_distance <= 155:
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
#while(1):
#    print(read_distance_ultrasonic())
sensor_handle()
