# Enhanced-Attendance-Marker

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python Version](https://img.shields.io/badge/Python-3.10+-brightgreen.svg)

The **Enhanced Attendance Marker** is a robust, open-source Python application designed to automate employee attendance tracking for small teams or organizations. By integrating facial recognition, one-time password (OTP) verification, and Wi-Fi hotspot connectivity, it ensures secure and efficient monitoring of employee presence. The system uses a designated hotspot ("AttendanceHotspot") to track attendance, logs data to CSV files, sends real-time email/SMS notifications, and generates daily reports.

---

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [File Structure](#file-structure)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)
- [Acknowledgments](#acknowledgments)

---

## Features

1. **Facial Recognition**:
   Identifies employees using the face_recognition library via webcam
2. **Secure Authentication**:
   Requires a 4-digit PIN and a 30-second OTP for daily login
3. **Hotspot Monitoring:** :
    Tracks presence via the "AttendanceHotspot" Wi-Fi network; logs login on connection and logout after 5 minutes of disconnection
4. **Attendance Logging** :
   Records data (date, time, employee ID, name, department, hours) in Data/attendance.csv
5. **Real-Time Notifications** :
   Sends email alerts (via Gmail SMTP) and SMS (via Twilio) for login/logout events
6. **Daily Reports** :
   Generates a CSV report (Data/daily_report.csv) every 24 hours and emails it to a designated recipient
7. **Voice Feedback** :
   Provides audible confirmations using pyttsx3 (e.g., "Dhruv logged in at 11:27 AM")

## Prerequistes

1. **Python 3.10+** :
   Download from https://www.python.org/downloads/
2. **Git** :
   Download from https://git-scm.com/downloads
3. **Operating System** :
   Windows (required for netsh-based hotspot functionality)
4. **Text Editor/ IDE** :
   Recommended: Visual Studio Code, PyCharm
5. **Webcam** :
   For facial recognition
6. **Wifi Adapter** :
   Must support hosted networks (check with netsh wlan show drivers)
7. **Gmail Account** :
   Enable 2-factor authentication and generate an App Password at https://support.google.com/accounts/answer/185833
8. **Twilio Account** :
   Register at https://www.twilio.com/ to obtain Account SID, Auth Token, and a Twilio phone   
   number


## Installation

1. **Clone the Repository** :
   ```bash
   git clone https://github.com/RajpurohitDhruv/Enhanced-Attendance-Marker.git
    cd Enhanced-Attendance-Marker
2. **Create a virtual Environment** :
   ```bash
   python -m venv venv
3. **Activate the Virtual Environment** :
   ```bash
   .\venv\Scripts\activate
4. **Install Dependencies** :
   ```bash
   pip install opencv-python numpy pandas pyttsx3 face_recognition pyotp twilio
5. **Verify Hotspot Support** :
   ```bash
   netsh wlan show drivers

## Configuration

1. **Open the file in your preferred text editor** :
   ```bash
   code attendance.py
2. **Set Credentials** :
   ```bash
   EMAIL_SENDER = "your-email@gmail.com"
    EMAIL_PASSWORD = "your-app-password"
    EMAIL_RECEIVER = "receiver-email@gmail.com"
    TWILIO_ACCOUNT_SID = "your-twilio-sid"
    TWILIO_AUTH_TOKEN = "your-twilio-token"
    TWILIO_PHONE_NUMBER = "your-twilio-number"
    EMPLOYEE_PHONE_NUMBER = "employee-phone-number"
3. **Save the File** :
   Save the file in your editor

## Usage

  **Registering Employees**
  1. **Run the Script** :
     ```bash
     python add_employee.py
  2. **Enter Details** :
     ```bash
     Enter name, PIN, designation, 
     Capture 10 face samples via webcam
  3. **Output** :
     ```bash
     Saved to Data/employees.csv, Data/names.pkl, Data/faces_data.pkl
     
  ## Running rhe Attendance System
  1. **Start the System** :
     ```bash
     python attendance.py
  2. **Login Process** :
     ```bash
     Face webcam, enter PIN, connect to "AttendanceHotspot", input OTP
     Success: Voice feedback and notifications
  3. **Monitor Presence** :
     ```bash
     Stay connected; disconnect for 5+ minutes to logout
   3. **Generate Reports** :
      ```bash
      Data/daily_report.csv generated every 24 hours and emailed
 3. **Stop the System** :
     ```bash
     Press q to exit

  ## Generating OTPs
  1. **Run on a Separate Device** :
     ```bash
     import pyotp
     import time
     secret = "JBSWY3DPEHPK3PXP"
     totp = pyotp.TOTP(secret, interval=30)
     while True:
       print(f"Your OTP: {totp.now()}")
       time.sleep(30)
 2. **Use OTP** :
     ```bash
     Enter during login

## File Structure
1. **Project Structure** :
   ```text
   Enhanced-Attendance-Marker/
    ├── attendance.py          # Main script for attendance tracking
    ├── add_employee.py        # Script for registering employees
    ├── requirements.txt       # List of Python dependencies
    ├── Data/                  # Directory for data files (created on first run)
    │   ├── employees.csv      # Employee details (ID, name, PIN, designation, department)
    │   ├── attendance.csv     # Attendance logs
    │   ├── daily_report.csv   # Daily attendance summary
    │   ├── names.pkl          # Names for face recognition
    │   └── faces_data.pkl     # Face encodings
    ├── README.md              # This documentation file
    └── LICENSE                # MIT License file

## Troubleshooting
1. **Hotspot Issues** :
   ```bash
   netsh wlan show drivers
2. **Webcam** :
   ```bash
   Test indices in init_camera() (0, 1, 2)
3. **Notifications** :
   ```bash
   Verify credentials and internet
4. **Recognization** :
   ```bash
   Check lighting and data files
5. **Permissions** :
   ```bash
   Move to C:\Users\YourName\ and run as admin

## Contributing
1. **Fork the Repository** :
   ```bash
   Fork the repository on GitHub
2. **Create a Branch** :
   ```bash
   git checkout -b feature/your-feature
3. **Commit Changes** :
   ```bash
   git commit -m "Add feature"
4. **Push to Fork** :
   ```bash
   Move to C:\Users\YourName\ and run as admin
5. **Submit a Pull Request** :
   ```bash
   Submit a Pull Request via GitHub

## License
**License Details** : 
This project is licensed under the MIT License - see the LICENSE file

## Contact
**Author** : Dhruv Rajpurohit

**Email** : rajpurohitdhruv27@gmail.com

**Github** : RajpurohitDhruv

**Issues** : https://github.com/RajpurohitDhruv/hotspot-Attendance-Marker/issues

## Acknowledgements
1. **Thanks** : To the creators of face_recognition, twilio and pyotp
2. **Inspired** :  By the need for efficient, secure, and automated attendance tracking solutions

