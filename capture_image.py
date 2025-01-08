from picamera2 import Picamera2, Preview
import time

picam2 = Picamera2()
# Use full resolution from the camera sensor
config = picam2.create_preview_configuration(main={"size": picam2.sensor_resolution})
picam2.configure(config)

picam2.start_preview(Preview.QTGL)
picam2.start()

time.sleep(200)

picam2.stop()
