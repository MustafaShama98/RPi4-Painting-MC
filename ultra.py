import smbus2
import time

# I2C address of the ultrasonic sensor (change as per your sensor's documentation)
I2C_ADDRESS = 0x57  # Example address

# Initialize I2C bus
bus = smbus2.SMBus(1)

def read_distance():
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
        return distance /100 # Convert mm to cm
    except Exception as e:
        print(f"Error reading distance: {e}")
        return None

try:
    print("Starting distance measurement...")
    while True:
        distance = read_distance()
        if distance is not None:
            dist = (distance * 2.5) + 1
            print(f"Distance: {dist:.2f} cm")
        else:
            print("Failed to read distance")
        time.sleep(0.5)  # Delay before next measurement

except KeyboardInterrupt:
    print("Measurement stopped")
