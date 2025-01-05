# **Project Setup and Management Guide**

This guide provides step-by-step instructions to set up, manage, and troubleshoot the project.

---

## **1. Install Project Dependencies**

### **Python Requirements**
Install all required Python libraries:
```bash
pip install -r requirements.txt
```

### **Install Node.js and npm**
Install Node.js and npm, required for PM2:
```bash
sudo apt install -y nodejs npm
```

---

## **2. Process Management with PM2**

### **Install PM2**
Install PM2 globally to manage the Python script:
```bash
sudo npm install -g pm2
```

### **Start Python Script with PM2**
Run the Python script using PM2:
```bash
pm2 start python3 -- /home/braude/Desktop/mqtt/rpi4_main.py
```

### **List Running Processes**
View all processes managed by PM2:
```bash
pm2 list
```

### **Save PM2 Process List**
Ensure the processes are saved for automatic restart after reboot:
```bash
pm2 save
```

### **Enable PM2 Startup on Boot**
Enable PM2 to start processes automatically after system reboot:
```bash
pm2 startup
```

---

## **3. Raspberry Pi-Specific Setup**

### **Install Camera Library**
Install the Picamera2 library for Raspberry Pi camera module support:
```bash
sudo apt install -y python3-picamera2
```

---

## **4. Virtual Environment Setup (Linux)**

### **Create Virtual Environment**
Create a Python virtual environment:
```bash
python3 -m venv .venv
```

### **Activate Virtual Environment**
Activate the environment to install isolated dependencies:
```bash
source .venv/bin/activate
```

### **Install Python Requirements**
Install dependencies in the virtual environment:
```bash
python3 -m pip install -r requirements.txt
```

### **Install Additional Python Libraries**
- **Certifi** for SSL certificates:
  ```bash
  sudo apt install python3-certifi
  ```
- **Paho MQTT** library for MQTT communication:
  ```bash
  sudo apt install python3-paho-mqtt
  ```

### **Install OpenCV for Computer Vision**
Install OpenCV for any image or video processing tasks:
```bash
sudo apt install python3-opencv
```

---

## **5. Debugging and Monitoring**

### **Check Running Python Processes**
Find and verify if the script is running:
```bash
ps -aux | grep rpi4_main.py
```

### **View Logs in Real-Time**
Monitor the log file for debugging:
```bash
tail -f logfile.log
```

---

## **6. Using `tmux` for Persistent Sessions**

### **Install `tmux`**
Install `tmux` to run your script in a persistent session:
```bash
sudo apt install tmux
```

### **Start a New `tmux` Session**
Create a new session and run your script:
```bash
tmux new -s myscript
python3 /home/braude/Desktop/mqtt/rpi4_main.py
```

### **Reattach to a Session**
If disconnected, reattach to the `tmux` session:
```bash
tmux attach -t myscript
```

---

## **7. Installing via pip on linux**
using --break-system-packages, for example:
pip3 install adafruit-circuitpython-vl53l0x --break-system-packages
pip3 install adafruit-blinka --break-system-packages

