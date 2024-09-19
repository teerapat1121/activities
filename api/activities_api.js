const express = require('express');
const mysql = require('mysql');
const cors = require('cors');
const { exec } = require('child_process');
const app = express();
const port = 7000;

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true })); // สำหรับรับข้อมูลฟอร์ม

// สร้างการเชื่อมต่อฐานข้อมูล
const db = mysql.createConnection({
  host: 'localhost',
  user: 'root',
  password: '',
  database: 'face_db'
});

// เชื่อมต่อฐานข้อมูล
db.connect(err => {
  if (err) {
    console.error('Database connection error:', err);
    return;
  }
  console.log('Database connected!');
});

// เส้นทางสำหรับดึงข้อมูล staff
app.get('/staffs', (req, res) => {
  db.query('SELECT id, displayName, dept FROM staffs', (err, results) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    res.json(results);
  });
});

// เส้นทางสำหรับอัปเดตข้อมูลพนักงาน
app.put('/update-staff/:id', (req, res) => {
  const { id } = req.params;
  const { displayName, dept } = req.body;

  if (!displayName || !dept) {
    return res.status(400).json({ error: 'Both displayName and dept are required' });
  }

  // อัปเดตข้อมูลพนักงานในตาราง staffs
  db.query('UPDATE staffs SET displayName = ?, dept = ? WHERE id = ?', [displayName, dept, id], (err, result) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }

    if (result.affectedRows === 0) {
      return res.status(404).json({ error: 'Staff not found' });
    }

    res.send({ ok: 1, message: 'Staff updated successfully' });
  });
});

// เส้นทางสำหรับลบข้อมูลพนักงาน
app.delete('/delete-staff/:id', (req, res) => {
  const { id } = req.params;

  // เริ่มต้นด้วยการลบข้อมูลในตาราง faces และ attendant ที่ staffId = id
  db.query('DELETE FROM faces WHERE staffId = ?', [id], (err) => {
    if (err) {
      return res.status(500).json({ error: 'Failed to delete faces records: ' + err.message });
    }

    db.query('DELETE FROM attendant WHERE staffId = ?', [id], (err) => {
      if (err) {
        return res.status(500).json({ error: 'Failed to delete attendant records: ' + err.message });
      }

      // ลบข้อมูลพนักงานในตาราง staffs
      db.query('DELETE FROM staffs WHERE id = ?', [id], (err, result) => {
        if (err) {
          return res.status(500).json({ error: err.message });
        }

        if (result.affectedRows === 0) {
          return res.status(404).json({ error: 'Staff not found' });
        }

        res.send({ ok: 1, message: 'Staff and related records deleted successfully' });
      });
    });
  });
});

// เส้นทางสำหรับรับ activity logs
app.get('/listactivities', (req, res) => {
  const query = `
    SELECT a.staffId, a.ts, a.Status, s.displayName, s.dept 
    FROM activity a
    JOIN staffs s ON a.staffId = s.id
  `;

  db.query(query, (err, results) => {
    if (err) {
      console.error('Query error:', err);
      res.status(500).send('Server error');
      return;
    }
    res.json({ rows: results });
  });
});

// เส้นทางสำหรับรันสคริปต์ Python เพื่อตรวจจับใบหน้า
app.post('/run-detectface', (req, res) => {
  exec('python3 python/detectface_test.py', (error, stdout, stderr) => {
    if (error) {
      console.error(`exec error: ${error}`);
      return res.status(500).send({ ok: 0, error: 'Error running Python script' });
    }
    res.send({ ok: 1, output: stdout });
  });
});

// เส้นทางสำหรับลงทะเบียนพนักงานและบันทึกข้อมูลใบหน้า
app.post('/register', (req, res) => {
  const { displayName, dept } = req.body;

  // ตรวจสอบค่าที่ได้รับจากคำขอ
  if (!displayName || !dept) {
    return res.status(400).json({ error: 'Both displayName and dept are required' });
  }

  // เพิ่มข้อมูลพนักงานในตาราง staffs
  db.query('INSERT INTO staffs (displayName, dept) VALUES (?, ?)', [displayName, dept], (err, result) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }

    // ตรวจสอบว่าการเพิ่มข้อมูลสำเร็จ
    if (result && result.insertId) {
      const staffId = result.insertId;  // ใช้ insertId ที่ได้จากการเพิ่มข้อมูล

      // รันสคริปต์ Python เพื่อตรวจจับใบหน้าและบันทึกข้อมูลใบหน้า
      exec(`python3 python/register_face.py ${staffId}`, (error, stdout, stderr) => {
        if (error) {
          console.error(`exec error: ${error}`);
          return res.status(500).json({ error: 'Error running Python script' });
        }

        // เพิ่มข้อมูลในตาราง attendant
        const ts = new Date(); // สร้างตัวแปร ts สำหรับเวลา
        db.query('INSERT INTO attendant (staffId, ts) VALUES (?, ?)', [staffId, ts], (err) => {
          if (err) {
            return res.status(500).json({ error: 'Error inserting into attendant: ' + err.message });
          }

          // สมมุติว่า stdout ของสคริปต์ Python ส่งคืนผลลัพธ์ที่ระบุว่าใบหน้าถูกบันทึกแล้ว
          console.log(`Python script output: ${stdout}`);

          // ส่งการตอบกลับเมื่อทุกอย่างสำเร็จ
          res.send({ ok: 1, message: 'Staff registered successfully and face data processed by Python script2' });
        });
      });
    } else {
      return res.status(500).json({ error: 'Failed to insert staff' });
    }
  });
});




app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});