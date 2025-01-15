# **Project Setup and Management Guide**

This guide provides step-by-step instructions to set up, manage, and troubleshoot the project.

---

## ** Install Project Dependencies**

### **Python Requirements**
Install all required Python libraries on **Windows**:
```bash
pip install -r requirements.txt
```
Install all required Python libraries on **RPI linux OS**:
```bash
sudo apt install python3-opencv
sudo apt install python3-paho-mqtt
sudo apt install python3-certifi
sudo apt install python3-picamera2

```

---


## ** Installing via pip on linux**
using --break-system-packages, for example:
pip3 install adafruit-circuitpython-vl53l0x --break-system-packages
pip3 install adafruit-blinka --break-system-packages

