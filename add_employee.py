#Coded by Dhruv Rajpurohit
import cv2
import numpy as np
import pickle
import os
import pandas as pd
import pyttsx3
import logging
import time
import face_recognition
import subprocess

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# CSV setup
EMPLOYEE_CSV = 'Data/employees.csv'
os.makedirs('Data', exist_ok=True)

# Voice setup
engine = pyttsx3.init()
def speak(text):
    try:
        engine.say(text)
        engine.runAndWait()
        logging.info(f"Spoke: {text}")
    except Exception as e:
        logging.error(f"Speech error: {e}")

def init_camera():
    for i in range(3):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            logging.info(f"Camera initialized on index {i}")
            return cap
    logging.error("Failed to initialize camera")
    return None

def check_hotspot_connectivity():
    try:
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
        devices = [line.split()[0] for line in result.stdout.splitlines() if "dynamic" in line.lower()]
        if devices:
            logging.info(f"Hotspot connectivity verified. Connected devices: {devices}")
            return True
        else:
            logging.info("No devices connected to hotspot")
            return False
    except Exception as e:
        logging.error(f"Failed to check hotspot connectivity: {e}")
        return False

def add_employee(name, cap):
    face_encodings = []
    start_time = time.time()
    speak("Please look at the camera and slightly move your head for 10 samples.")
    
    while time.time() - start_time < 20 and len(face_encodings) < 10:
        ret, frame = cap.read()
        if not ret:
            speak("Camera read failed. Employee not added.")
            logging.error("Camera read failed")
            return None
        
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame, model="hog", number_of_times_to_upsample=2)
            if face_locations:
                encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                if encodings:
                    face_encodings.append(encodings[0])
                    logging.info(f"Captured encoding {len(face_encodings)} for {name}")
            cv2.putText(frame, f"Capturing: {len(face_encodings)}/10", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        except Exception as e:
            logging.warning(f"Face detection failed: {e}")
            cv2.putText(frame, "No face detected", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        cv2.imshow("Add Employee", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    if len(face_encodings) < 5:
        speak("Insufficient face data captured. Employee not added.")
        logging.error(f"Only {len(face_encodings)} encodings captured for {name}")
        return None

    pin = input(f"Set a 4-digit PIN for {name}: ").strip()
    if not (pin.isdigit() and len(pin) == 4):
        speak("Invalid PIN. Employee not added.")
        logging.error(f"Invalid PIN: {pin}")
        return None
    designation = input(f"Enter {name}'s designation (e.g., Software Engineer): ").strip()
    department = input(f"Enter {name}'s department (e.g., IT): ").strip()

    # Optional hotspot connectivity check
    speak("Please connect a device to 'AttendanceHotspot' to verify connectivity (optional). Press Enter to skip or wait 10 seconds.")
    connectivity_verified = False
    start_wait = time.time()
    while time.time() - start_wait < 10:
        if check_hotspot_connectivity():
            connectivity_verified = True
            speak("Hotspot connectivity verified.")
            break
        if cv2.waitKey(1) & 0xFF == 13:  # Enter key
            break
    if not connectivity_verified:
        speak("Hotspot check skipped or failed. Continuing with employee addition.")

    # Load or create CSV
    if os.path.exists(EMPLOYEE_CSV):
        try:
            df = pd.read_csv(EMPLOYEE_CSV)
            employee_id = df['id'].max() + 1 if not df.empty else 1
        except Exception as e:
            logging.error(f"Failed to read CSV: {e}")
            df = pd.DataFrame(columns=['id', 'name', 'pin', 'designation', 'department'])
            employee_id = 1
    else:
        df = pd.DataFrame(columns=['id', 'name', 'pin', 'designation', 'department'])
        employee_id = 1

    new_employee = pd.DataFrame([{
        'id': employee_id,
        'name': name,
        'pin': pin,
        'designation': designation,
        'department': department
    }])
    df = pd.concat([df, new_employee], ignore_index=True)
    try:
        df.to_csv(EMPLOYEE_CSV, index=False)
        logging.info(f"Employee data saved to CSV: ID {employee_id}")
    except Exception as e:
        speak("Failed to save employee data to CSV. Employee not added.")
        logging.error(f"CSV save error: {e}")
        return None

    # Save face encodings
    names = pickle.load(open('Data/names.pkl', 'rb')) if os.path.exists('Data/names.pkl') else []
    faces = pickle.load(open('Data/faces_data.pkl', 'rb')) if os.path.exists('Data/faces_data.pkl') else []
    names.extend([name] * len(face_encodings))
    faces.extend(face_encodings)

    try:
        with open('Data/names.pkl', 'wb') as f:
            pickle.dump(names, f)
        with open('Data/faces_data.pkl', 'wb') as f:
            pickle.dump(faces, f)
        logging.info(f"Face encodings saved for {name} with ID {employee_id}")
    except Exception as e:
        speak("Failed to save face data. Employee not fully added.")
        logging.error(f"Face data save error: {e}")
        return None

    return employee_id

def main():
    cap = init_camera()
    if not cap:
        speak("Camera not available. Shutting down.")
        return

    cv2.namedWindow("Add Employee")
    speak("Please ensure 'AttendanceHotspot' is active on your laptop.")
    speak("Enter the new employee's name in the console")
    name = input("Enter employee name: ").strip()
    if name:
        new_id = add_employee(name, cap)
        if new_id:
            speak(f"Employee {name} added successfully with ID {new_id}")
        else:
            speak("Failed to add employee")
    
    if cap.isOpened():
        cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()