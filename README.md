pip install -r requirements.txt

sudo apt install -y python3-picamera2

linux:
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
sudo apt install python3-certifi
 sudo apt install python3-paho-mqtt

sudo apt install python3-opencv


ps -aux | grep rpi4_main.py
