import cv2
import numpy as np
import face_recognition
from ultralytics import YOLO
import mysql.connector
from datetime import datetime, time

# Initialize YOLO model
model = YOLO("yolov8n.pt")

# Initialize MySQL connection
conn = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="",
    database="face_db"
)
cursor = conn.cursor(dictionary=True)

def fetch_faces():
    cursor.execute('''
    SELECT f.staffId, s.displayName name, s.dept, f.id faceId, f.faceData 
    FROM staffs s
      JOIN faces f ON f.staffId=s.id''')
    return cursor.fetchall()


def insert_activity(staff_id, timestamp, status):
    try:
        cursor.execute("INSERT INTO activity (staffId, ts, Status) VALUES (%s, %s, %s)", (staff_id, timestamp, status))
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error: {err}")

def has_checked_out_today(staff_id):
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("SELECT COUNT(*) FROM activity WHERE staffId = %s AND DATE(ts) = %s AND Status = 'Checked out'", (staff_id, today))
    count = cursor.fetchone()["COUNT(*)"]
    return count > 0

def has_checked_in_today(staff_id):
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("SELECT COUNT(*) FROM activity WHERE staffId = %s AND DATE(ts) = %s AND Status = 'check-in'", (staff_id, today))
    count = cursor.fetchone()["COUNT(*)"]
    return count > 0

faces = fetch_faces()

# Convert face encodings to tuples
all_faces = [tuple(np.frombuffer(face["faceData"], dtype=np.float64)) for face in faces]
face_names = {tuple(np.frombuffer(face["faceData"], dtype=np.float64)): (face["name"], face["dept"]) for face in faces}


# Initialize video capture
cap = cv2.VideoCapture(1)

while cap.isOpened():
    ret, frame = cap.read()

    if not ret:
        print("Can't receive frame (stream end?). Exiting...")
        break

    # YOLO object detection
    results = model(frame, stream=True, classes=[0], conf=0.25)
    height, width, _ = frame.shape

    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].int().tolist()
            conf = box.conf[0]
            cls = box.cls[0]
            label = f'{model.names[int(cls)]} {conf:.2f}'

            if label.startswith('person'):
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2

                # Face recognition
                small_frame = cv2.resize(frame, (0, 0), fx=1 / 4, fy=1 / 4)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

                recognized = False

                for face_encoding, face_location in zip(face_encodings, face_locations):
                    face_tuple = tuple(face_encoding)
                    face_distances = [np.linalg.norm(np.array(face_tuple) - np.array(db_face)) for db_face in all_faces]
    
                    if len(face_distances) > 0:
                        min_index = np.argmin(face_distances)
                        if face_distances[min_index] < 0.6:  # ปรับ threshold ตามที่ต้องการ
                            name, dept = face_names[tuple(all_faces[min_index])]
                            recognized = True
                            top, right, bottom, left = face_location
                                              # แสดงชื่อและแผนก
                            cv2.putText(frame, f"{name} ({dept})", (left * 4, top * 4), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                            cv2.rectangle(frame, (left * 4, top * 4), (right * 4, bottom * 4), (0, 0, 255), 2)
                            # Retrieve staff ID for logging activity
                            staff_id = faces[min_index]["staffId"]

                            now = datetime.now()
                            current_time = now.time()
                            start_time = time(8, 0)  # 08:00
                            end_time = time(9, 0)    # 09:00
                            check_out_time = time(17, 0)  # 17:00 (5 โมงเย็น)
                            
                            if start_time <= current_time <= end_time:
                                if not has_checked_in_today(staff_id):
                                    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
                                    insert_activity(staff_id, timestamp, "check-in")
                                    message = f"Checked in: {staff_id}"
                                else:
                                    message = "Already Checked In"
                            elif current_time > check_out_time:  # เงื่อนไขหลัง 17:00 น.
                                if has_checked_in_today(staff_id) and not has_checked_out_today(staff_id):
                                    insert_activity(staff_id, now.strftime('%Y-%m-%d %H:%M:%S'), "Checked out")
                                    message = "Checked out"
                                elif not has_checked_in_today(staff_id):
                                    message = "Time out"
                                else:
                                    message = "Already Checked Out"
                            else:
                                if has_checked_in_today(staff_id):
                                    message = "Not time yet"  # เงื่อนไขยังไม่ถึงเวลา Checked out
                                else:
                                    message = "Time out"
                            # Draw message on the frame (aligned to the left)
                            cv2.putText(frame, message, (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_AA)

    # Resize frame
    scale_percent = 150  # Resize to 150%
    width = int(frame.shape[1] * scale_percent / 100)
    height = int(frame.shape[0] * scale_percent / 100)
    dim = (width, height)
    resized_frame = cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)
    
    # Show resized frame
    cv2.imshow('frame', resized_frame)

    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
