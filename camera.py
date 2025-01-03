import base64
import numpy as np
from picamera2 import Picamera2

def capture_frame():
    """Capture a frame from the Raspberry Pi Camera Module and return as base64."""
    # Initialize Picamera2
    picam2 = Picamera2()
    config = picam2.create_still_configuration()
    picam2.configure(config)

    # Start the camera and capture a frame
    picam2.start()
    frame = picam2.capture_array()
    picam2.stop()

    # Encode the frame as JPEG
    _, buffer = cv2.imencode(".jpg", frame)

    # Return the frame as a base64 string
    return base64.b64encode(buffer).decode("utf-8")

if __name__ == "__main__":
    encoded_image = capture_frame()
    print(encoded_image)
