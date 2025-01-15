import adafruit_vl53l0x
import busio
import board

# Initialize I2C and the sensor
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_vl53l0x.VL53L0X(i2c)

def get_distance_cm():
    """Read distance from the VL53L0X sensor, print and return it in cm."""
    distance = sensor.range // 10  # Convert mm to cm
    print(f"Distance: {distance} cm")
    return distance

while(True):
    get_distance_cm()
