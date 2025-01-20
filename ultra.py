import smbus2
import time

I2C_ADDRESS = 0x57  

# Initialize I2C bus
bus = smbus2.SMBus(1)

def read_distance_ultrasonic():
    """Read distance from the ultrasonic sensor via I2C."""
    try:
        # Request measurement from the sensor
        bus.write_byte(I2C_ADDRESS, 0x01)  # Command to start measurement
        time.sleep(0.2)  # Allow the sensor to settle after issuing command
        
        # Read 2 bytes of data (distance in mm)
        data = bus.read_i2c_block_data(I2C_ADDRESS, 0x00, 2)
        time.sleep(0.1)  # Delay before processing data
        
        # Convert to distance
        distance = (data[0] << 8) | data[1]  # Combine high and low byte
        return distance / 100  # Convert mm to cm
    except Exception as e:
        return None

def measure_distance():
    while True:
        distance = read_distance_ultrasonic()  # Calling the read_distance function
        if distance is not None:
            dist = (distance * 2.5) + 1  # Calculate the distance based on the sensor's data
            print(f"Distance: {dist:.2f} cm")  # Print the calculated distance
            return dist  # Return the calculated distance if needed
        
        time.sleep(0.5)  # Delay before next measurement

# Main loop
# while(1):
#     try:
#         measured_distance = measure_distance()  # Call the function to start measuring
#     except KeyboardInterrupt:
#         print("Measurement stopped")

