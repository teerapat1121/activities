import cv2
import face_recognition
import mysql.connector
from datetime import datetime
import sys
import time

def run_script(staffId):
    # ตั้งค่าการเชื่อมต่อกับฐานข้อมูล MySQL
    try:
        conn = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="",
            database="face_db"
        )
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        sys.exit(1)

    video_capture = cv2.VideoCapture(1)
    register = False
    face_detected_time = None  # ตัวแปรสำหรับเก็บเวลาที่ตรวจพบใบหน้า

    try:
        while True:
            ok, frame = video_capture.read()
            if not ok:
                print("Failed to capture image from camera")
                break

            small_frame = cv2.resize(frame, (0, 0), fx=1 / 4, fy=1 / 4)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_small_frame)

            if face_locations:
                # กำหนดเวลาที่ตรวจพบใบหน้า
                if face_detected_time is None:
                    face_detected_time = time.time()

                for (top, right, bottom, left) in face_locations:
                    cv2.rectangle(frame, (left * 4, top * 4), (right * 4, bottom * 4), (0, 0, 255), 2)

                # ถ้าตรวจพบใบหน้าและเวลาผ่านไปแล้ว 3 วินาที
                if time.time() - face_detected_time >= 3:
                    if not register:
                        register = True

                        # เข้ารหัสใบหน้า
                        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                        if face_encodings:
                            face_data = face_encodings[0].tobytes()

                            try:
                                cursor = conn.cursor()

                                # แทรกข้อมูลลงในตาราง faces พร้อม staffId
                                sql_faces = "INSERT INTO faces (faceData, staffId) VALUES (%s, %s)"
                                cursor.execute(sql_faces, (face_data, staffId))
                                insert_id = cursor.lastrowid
                                print(f"Inserted into faces with ID: {insert_id}")
                                conn.commit()

                            except mysql.connector.Error as err:
                                print(f"Database error: {err}")
                                conn.rollback()
                    
                    break  # หยุดโปรแกรมเมื่อครบ 3 วินาที

            else:
                # ถ้าไม่เจอใบหน้า รีเซ็ตเวลา
                face_detected_time = None

            cv2.imshow('Video', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        video_capture.release()
        cv2.destroyAllWindows()
        conn.close()
        print("Finished processing.")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python register_face.py <staffId>")
        sys.exit(1)

    staffId = int(sys.argv[1])
    run_script(staffId)
