import cv2
import face_recognition
import mysql.connector
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import threading

def run_face_detection():
    video_capture = cv2.VideoCapture(1)
    register = False
    start_time = None

    while True:
        ok, frame = video_capture.read()
        if not ok:
            print("Failed to capture image from camera")
            break

        small_frame = cv2.resize(frame, (0, 0), fx=1 / 4, fy=1 / 4)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_small_frame)

        if face_locations:
            if not register:
                start_time = datetime.now()
                register = True

            elapsed_time = (datetime.now() - start_time).seconds
            if elapsed_time >= 3:
                # ปิดหน้าต่างหลังจากตรวจจับใบหน้าเป็นเวลา 3 วินาที
                video_capture.release()
                cv2.destroyAllWindows()
                save_to_database(face_locations, rgb_small_frame)
                break

            for (top, right, bottom, left) in face_locations:
                cv2.rectangle(frame, (left * 4, top * 4), (right * 4, bottom * 4), (0, 255, 0), 2)

        # แปลงเฟรมเป็นรูปภาพสำหรับแสดงบน Canvas ใน Tkinter
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        imgtk = ImageTk.PhotoImage(image=img)
        video_label.imgtk = imgtk
        video_label.configure(image=imgtk)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()

def save_to_database(face_locations, rgb_small_frame):
    # เข้ารหัสใบหน้าและบันทึกลงฐานข้อมูล
    try:
        conn = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="",
            database="face_db"
        )
        cursor = conn.cursor()

        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        if face_encodings:
            face_data = face_encodings[0].tobytes()

            sql_staffs = "INSERT INTO staffs (displayName, dept) VALUES (%s, %s)"
            cursor.execute(sql_staffs, (display_name.get(), department.get()))
            insert_id = cursor.lastrowid
            conn.commit()

            sql_faces = "INSERT INTO faces (staffId, faceData) VALUES(%s, %s)"
            cursor.execute(sql_faces, (insert_id, face_data))
            conn.commit()

            current_time = datetime.now()
            sql_attendant = "INSERT INTO attendant (staffId, ts) VALUES (%s, %s)"
            cursor.execute(sql_attendant, (insert_id, current_time))
            conn.commit()

            messagebox.showinfo("Success", "Data saved successfully!")
            root.quit()  # ปิดหน้าต่าง Tkinter หลังจากบันทึกข้อมูลเสร็จ

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error: {err}")
        conn.rollback()
    finally:
        conn.close()

def start_detection():
    threading.Thread(target=run_face_detection).start()

# สร้างหน้าต่างหลักด้วย Tkinter
root = tk.Tk()
root.title("Face Registration")
root.geometry("800x600")
root.configure(bg="#f0f0f0")

# ส่วนของการรับข้อมูล displayName และ department
tk.Label(root, text="Enter your details", font=("Helvetica", 16), bg="#f0f0f0").pack(pady=10)

tk.Label(root, text="Display Name", font=("Helvetica", 12), bg="#f0f0f0").pack()
display_name = tk.Entry(root, font=("Helvetica", 12), width=30)
display_name.pack(pady=5)

tk.Label(root, text="Department", font=("Helvetica", 12), bg="#f0f0f0").pack()
department = tk.Entry(root, font=("Helvetica", 12), width=30)
department.pack(pady=5)

# ปุ่มเริ่มการตรวจจับใบหน้า
start_button = tk.Button(root, text="Submit", font=("Helvetica", 14), bg="#4CAF50", fg="white", command=start_detection)
start_button.pack(pady=20)

# แสดงภาพจากกล้อง
video_label = tk.Label(root)
video_label.pack(pady=10)

root.mainloop()
