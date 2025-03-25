#Coded by Dhruv Rajpurohit
import time
import cv2
import pyttsx3
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import numpy as np
import pickle
import pandas as pd
from datetime import datetime, timedelta
import face_recognition
import pyotp
import logging
import subprocess
from twilio.rest import Client

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Email and Twilio setup
EMAIL_SENDER = "your-email@gmail.com"
EMAIL_PASSWORD = "your-app-password"
EMAIL_RECEIVER = "receiver-email@gmail.com"
TWILIO_ACCOUNT_SID = "your-twilio-sid"
TWILIO_AUTH_TOKEN = "your-twilio-token"
TWILIO_PHONE_NUMBER = "your-twilio-number"
EMPLOYEE_PHONE_NUMBER = "employee-phone-number"

# File setup
EMPLOYEE_CSV = 'Data/employees.csv'
ATTENDANCE_CSV = 'Data/attendance.csv'
DAILY_REPORT_CSV = 'Data/daily_report.csv'
os.makedirs('Data', exist_ok=True)

# Employee tracking
employee_entries = {}
employee_last_action = {}
employee_daily_status = {}
employees = {}
employee_faces = {}
employee_pins = {}
employee_last_seen = {}
cap = None

# Voice setup
engine = pyttsx3.init()
def speak(text):
    try:
        engine.say(text)
        engine.runAndWait()
        logging.info(f"Spoke: {text}")
    except Exception as e:
        logging.error(f"Speech error: {e}")

def enable_hotspot():
    try:
        result = subprocess.run(['netsh', 'wlan', 'show', 'hostednetwork'], capture_output=True, text=True)
        if "Not started" in result.stdout:
            subprocess.run(['netsh', 'wlan', 'set', 'hostednetwork', 'mode=allow', 'ssid=AttendanceHotspot', 'key=12345678'], check=True)
            subprocess.run(['netsh', 'wlan', 'start', 'hostednetwork'], check=True)
            logging.info("Hotspot enabled: AttendanceHotspot")
        else:
            logging.info("Hotspot already active")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to enable hotspot: {e}")
        return False

def init_camera():
    global cap
    for i in range(3):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            logging.info(f"Camera initialized on index {i}")
            return True
        cap.release()
    logging.error("Failed to initialize camera")
    return False

def send_email(subject, body, attachment=None):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg.attach(MIMEText(body, 'plain'))
    if attachment and os.path.isfile(attachment):
        with open(attachment, 'rb') as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(attachment))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment)}"'
            msg.attach(part)
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        logging.info(f"Email sent: {subject}")
    except Exception as e:
        logging.error(f"Email failed: {e}")

def send_sms_notification(employee_id, name, message):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    try:
        client.messages.create(
            body=f"Attendance: {name} - {message}",
            from_=TWILIO_PHONE_NUMBER,
            to=EMPLOYEE_PHONE_NUMBER
        )
        logging.info(f"SMS sent to {EMPLOYEE_PHONE_NUMBER}: {message}")
    except Exception as e:
        logging.error(f"Failed to send SMS: {e}")

def log_attendance_to_csv(employee_id, name, hours, success, action):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    department = employees[employee_id][2]

    record = {
        'date': date,
        'timestamp': timestamp,
        'employee_id': employee_id,
        'name': name,
        'department': department,
        'hours': hours,
        'success': success,
        'action': action
    }

    if os.path.exists(ATTENDANCE_CSV):
        df = pd.read_csv(ATTENDANCE_CSV)
    else:
        df = pd.DataFrame(columns=['date', 'timestamp', 'employee_id', 'name', 'department', 'hours', 'success', 'action'])

    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    try:
        df.to_csv(ATTENDANCE_CSV, index=False)
        logging.info(f"Attendance logged for {name}: {action}")
    except Exception as e:
        logging.error(f"Failed to log attendance: {e}")
        return

    subject = f"Attendance: {name} - {action.capitalize()}"
    body = f"Time: {timestamp}\nEmployee ID: {employee_id}\nName: {name}\nHours: {hours:.2f}\nStatus: {'Success' if success else 'Failed'}"
    send_email(subject, body)

    push_msg = f"{name} marked {action} ({hours:.2f} hrs)"
    send_sms_notification(employee_id, name, push_msg)

def generate_daily_report():
    if not os.path.exists(ATTENDANCE_CSV):
        logging.info("No attendance data for daily report")
        return
    
    try:
        df = pd.read_csv(ATTENDANCE_CSV)
        today = datetime.now().strftime("%Y-%m-%d")
        df_today = df[df['date'] == today]
        
        if df_today.empty:
            logging.info(f"No attendance data for today: {today}")
            return
        
        report_data = []
        for employee_id in df_today['employee_id'].unique():
            df_employee = df_today[df_today['employee_id'] == employee_id]
            name = df_employee['name'].iloc[0]
            department = df_employee['department'].iloc[0]
            total_hours = df_employee[df_employee['success'] == True]['hours'].sum()
            report_data.append({
                'employee_id': employee_id,
                'name': name,
                'department': department,
                'total_hours': total_hours
            })
        
        report_df = pd.DataFrame(report_data)
        report_df.to_csv(DAILY_REPORT_CSV, index=False)
        logging.info(f"Generated daily report: {DAILY_REPORT_CSV}")
        
        subject = f"Daily Attendance Report - {today}"
        body = f"Attached is the daily attendance report for {today}."
        send_email(subject, body, DAILY_REPORT_CSV)
    except Exception as e:
        logging.error(f"Daily report generation error: {e}")

def recognize_face(frame, employee_faces, employees):
    if frame is None or not isinstance(frame, np.ndarray):
        logging.error("Invalid frame received")
        return None, "Invalid Frame", [], 0
    
    try:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame, model="hog", number_of_times_to_upsample=2)
        if not face_locations:
            logging.info("No face detected in frame")
            return None, "No Face Detected", face_locations, 0
        
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        if not face_encodings:
            logging.info("No face encodings extracted")
            return None, "No Face Detected", face_locations, 0
        
        best_match_id = None
        best_confidence = 0
        tolerance = 0.6
        
        for face_encoding in face_encodings:
            for employee_id, known_encodings in employee_faces.items():
                if not known_encodings:
                    logging.warning(f"No encodings for employee {employee_id}")
                    continue
                matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=tolerance)
                distances = face_recognition.face_distance(known_encodings, face_encoding)
                if len(distances) > 0:
                    min_dist = min(distances)
                    confidence = max(0, 100 - (min_dist / tolerance) * 100)
                    logging.info(f"Employee {employee_id}: Min Distance={min_dist:.2f}, Confidence={confidence:.1f}%")
                    if any(matches) and confidence > best_confidence and confidence >= 40:
                        best_match_id = employee_id
                        best_confidence = confidence
        
        if best_match_id:
            name = employees[best_match_id][0]
            logging.info(f"Recognized {name} (ID: {best_match_id}, Confidence: {best_confidence:.1f}%)")
            return best_match_id, name, face_locations, best_confidence
        logging.info("No match found for detected face")
        return None, "Unknown Face", face_locations, 0
    except Exception as e:
        logging.error(f"Face recognition error: {e}")
        return None, "Recognition Error", [], 0

def verify_pin(employee_id):
    name = employees[employee_id][0]
    speak(f"Please enter your 4-digit PIN for {name}")
    entered_pin = input(f"Enter your 4-digit PIN for {name}: ").strip()
    stored_pin = employee_pins.get(employee_id, "")
    logging.info(f"Verifying PIN for {employee_id}: Entered '{entered_pin}' vs Stored '{stored_pin}'")
    return entered_pin == stored_pin

def verify_location(employee_id):
    try:
        secret = "JBSWY3DPEHPK3PXP"
        totp = pyotp.TOTP(secret, interval=30)
        expected_otp = totp.now()
        
        name = employees[employee_id][0]
        speak(f"Please connect to 'AttendanceHotspot' and enter your OTP for {name}")
        logging.info(f"Prompting {employee_id} to connect and enter OTP")
        
        connected_devices = get_connected_devices()
        if not connected_devices:
            speak("No devices connected to the hotspot. Please connect and try again.")
            logging.info("No devices detected on hotspot")
            return False
        
        print(f"Enter OTP for {name} (valid for 30 seconds): ", end='', flush=True)
        submitted_otp = input().strip()
        if not submitted_otp:
            logging.info(f"No OTP entered for {employee_id}")
            speak("No OTP entered. Please try again.")
            return False
        
        current_otp = totp.now()
        previous_otp = totp.at(datetime.now() - timedelta(seconds=30))
        if submitted_otp in (current_otp, previous_otp):
            logging.info(f"OTP {submitted_otp} verified for employee {employee_id}")
            return True
        else:
            logging.info(f"Invalid OTP {submitted_otp} for {employee_id}. Expected {current_otp} or {previous_otp}")
            speak(f"Invalid OTP {submitted_otp}. Please try again.")
            return False
    except Exception as e:
        logging.error(f"OTP verification error: {e}")
        speak("OTP verification failed due to an error.")
        return False

def get_connected_devices():
    try:
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
        devices = [line.split()[0] for line in result.stdout.splitlines() if "dynamic" in line.lower()]
        logging.info(f"Connected devices: {devices}")
        return devices
    except Exception as e:
        logging.error(f"Failed to get connected devices: {e}")
        return []

def monitor_hotspot():
    current_time = time.time()
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    connected_devices = get_connected_devices()

    for employee_id in list(employee_entries.keys()):
        name, _, _ = employees[employee_id]
        if connected_devices:
            employee_last_seen[employee_id] = current_time
            daily_status = employee_daily_status.get(employee_id, {'login': False, 'logout': False, 'date': today})
            if daily_status['date'] != today:
                daily_status = {'login': False, 'logout': False, 'date': today}
                employee_daily_status[employee_id] = daily_status
            
            if employee_id not in employee_entries and not daily_status['login']:
                employee_entries[employee_id] = now
                log_attendance_to_csv(employee_id, name, 0, True, "login")
                daily_status['login'] = True
                employee_daily_status[employee_id] = daily_status
                logging.info(f"{name} re-entered via hotspot")
        else:
            if employee_id in employee_last_seen and (current_time - employee_last_seen[employee_id]) > 300:
                entry_time = employee_entries.pop(employee_id)
                hours_spent = (now - entry_time).total_seconds() / 3600
                log_attendance_to_csv(employee_id, name, hours_spent, True, "logout")
                daily_status = employee_daily_status[employee_id]
                daily_status['logout'] = True
                employee_daily_status[employee_id] = daily_status
                logging.info(f"{name} logged out via hotspot absence")

def load_employees_from_csv():
    global employees, employee_faces, employee_pins
    employees = {}
    employee_faces = {}
    employee_pins = {}
    if os.path.exists(EMPLOYEE_CSV):
        df = pd.read_csv(EMPLOYEE_CSV)
        for _, row in df.iterrows():
            employee_id = str(row['id'])
            employees[employee_id] = (row['name'], row['designation'], row['department'])
            employee_pins[employee_id] = str(row['pin']).strip()
    
    if os.path.exists('Data/names.pkl') and os.path.exists('Data/faces_data.pkl'):
        with open('Data/names.pkl', 'rb') as f:
            names = pickle.load(f)
        with open('Data/faces_data.pkl', 'rb') as f:
            faces = pickle.load(f)
        for i in range(0, len(names), 10):
            name = names[i]
            matching_ids = [k for k, v in employees.items() if v[0] == name]
            if matching_ids:
                employee_faces[matching_ids[0]] = faces[i:i+10]

def main_loop():
    global cap
    if not enable_hotspot():
        speak("Failed to enable hotspot. Shutting down.")
        return
    if not init_camera():
        speak("Camera not available. Shutting down.")
        return

    cv2.namedWindow("Attendance System")
    load_employees_from_csv()

    message = ""
    message_timer = 0
    frame_skip = 0
    last_report_time = None

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logging.error("Camera error. Shutting down.")
                speak("Camera error. Shutting down.")
                break
            
            frame_skip = (frame_skip + 1) % 5
            if frame_skip != 0:
                cv2.imshow("Attendance System", frame)
                cv2.waitKey(1)
                continue

            employee_id, result, face_locations, confidence = recognize_face(frame, employee_faces, employees)
            name = employees[employee_id][0] if employee_id else result
            logging.info(f"Recognition: ID={employee_id}, Name={name}, Confidence={confidence:.1f}%")
            
            cv2.putText(frame, f"Result: {name} ({confidence:.1f}%)", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            current_time = time.time()
            today = datetime.now().strftime("%Y-%m-%d")
            now = datetime.now()

            if employee_id and result not in ("No Face Detected", "Unknown Face", "Invalid Frame"):
                last_action_time = employee_last_action.get(employee_id, 0)
                if current_time - last_action_time < 120:
                    message = f"{name}, wait 2 minutes before next action."
                    speak(message)
                    message_timer = current_time
                else:
                    daily_status = employee_daily_status.get(employee_id, {'login': False, 'logout': False, 'date': today})
                    if daily_status['date'] != today:
                        daily_status = {'login': False, 'logout': False, 'date': today}
                        employee_daily_status[employee_id] = daily_status

                    if not daily_status['login']:
                        if verify_pin(employee_id) and verify_location(employee_id):
                            employee_entries[employee_id] = now
                            message = f"Welcome {name}!"
                            speak(f"{name} logged in at {now.strftime('%I:%M %p')}")
                            log_attendance_to_csv(employee_id, name, 8, True, "login")
                            daily_status['login'] = True
                            employee_daily_status[employee_id] = daily_status
                            employee_last_action[employee_id] = current_time
                            employee_last_seen[employee_id] = current_time
                            message_timer = current_time
                        else:
                            message = f"{name}, PIN or OTP not verified!"
                            speak(message)
                            message_timer = current_time
                    else:
                        message = f"{name}, already logged in today. Monitoring via hotspot."
                        speak(message)
                        message_timer = current_time
            
            if message and (current_time - message_timer < 5):
                cv2.putText(frame, message, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            cv2.imshow("Attendance System", frame)
            k = cv2.waitKey(30) & 0xFF
            if k == ord('q'):
                break

            monitor_hotspot()

            # Generate daily report once per day (e.g., at midnight or every 24 hours)
            if last_report_time is None or (now - last_report_time).total_seconds() > 86400:  # 24 hours
                generate_daily_report()
                last_report_time = now

    except KeyboardInterrupt:
        logging.info("Program interrupted by user")
    except Exception as e:
        logging.error(f"Main loop error: {e}")
    finally:
        if cap is not None and cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()
        subprocess.run(['netsh', 'wlan', 'stop', 'hostednetwork'], check=True)
        logging.info("Hotspot stopped and program terminated")

if __name__ == "__main__":
    main_loop()