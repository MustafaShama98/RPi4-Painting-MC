import board
import busio
import adafruit_vl53l0x

# Initialize I2C and the sensor
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_vl53l0x.VL53L0X(i2c)


def get_distance_cm():
    """Read distance from the VL53L0X sensor and return it in cm."""
    return sensor.range // 10  # Convert mm to cm
    