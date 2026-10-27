import os
import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'smart_campus.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')

def get_db_connection():
    """Get a connection to the SQLite database with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables and seed sample data if newly created."""
    conn = get_db_connection()
    cursor = conn.cursor()

    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema = f.read()
        cursor.executescript(schema)

    # Check if users already exist
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    if user_count == 0:
        seed_sample_data(conn)

    conn.commit()
    conn.close()

def seed_sample_data(conn):
    """Seed comprehensive initial demo data for students, faculty, admin, courses, and notices."""
    cursor = conn.cursor()

    # Passwords hashed for security
    pw_admin = generate_password_hash("admin123")
    pw_faculty = generate_password_hash("faculty123")
    pw_student = generate_password_hash("student123")

    users_data = [
        # Admin
        (None, "Dr. Rajesh Sharma", "admin@campus.ai", pw_admin, "admin", "Campus Administration", None, "+91 98111 22233", "admin_avatar.png", None),
        # Faculty
        ("FAC101", "Prof. Ananya Sen", "faculty@campus.ai", pw_faculty, "faculty", "Computer Science & Engineering", None, "+91 98222 33344", "faculty_avatar.png", None),
        ("FAC102", "Dr. Vikram Sethi", "vikram.sethi@campus.ai", pw_faculty, "faculty", "Electronics & Communication", None, "+91 98333 44455", "faculty_avatar.png", None),
        ("FAC103", "Prof. Neha Gupta", "neha.gupta@campus.ai", pw_faculty, "faculty", "Artificial Intelligence & Data Science", None, "+91 98444 55566", "faculty_avatar.png", None),
        # Students
        ("CS2026001", "Aarav Patel", "student@campus.ai", pw_student, "student", "Computer Science & Engineering", 6, "+91 98765 43210", "aarav.png", 8.85),
        ("CS2026002", "Priya Nair", "priya.nair@campus.ai", pw_student, "student", "Computer Science & Engineering", 6, "+91 98765 43211", "priya.png", 9.12),
        ("AI2026015", "Rohan Verma", "rohan.verma@campus.ai", pw_student, "student", "Artificial Intelligence & Data Science", 6, "+91 98765 43212", "rohan.png", 8.40),
        ("EC2026022", "Sneha Iyer", "sneha.iyer@campus.ai", pw_student, "student", "Electronics & Communication", 6, "+91 98765 43213", "sneha.png", 7.95),
        ("CS2026045", "Kunal Kapoor", "kunal.kapoor@campus.ai", pw_student, "student", "Computer Science & Engineering", 6, "+91 98765 43214", "kunal.png", 8.60)
    ]

    for u in users_data:
        cursor.execute("""
            INSERT INTO users (roll_number, name, email, password_hash, role, department, semester, phone, face_image, cgpa)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, u)

    # Courses
    courses_data = [
        ("CS601", "Artificial Intelligence & Deep Learning", "Computer Science & Engineering", 6, 4, 2),
        ("CS602", "Cloud Computing & DevOps", "Computer Science & Engineering", 6, 4, 2),
        ("CS603", "Distributed Systems & Networks", "Computer Science & Engineering", 6, 3, 2),
        ("CS604", "Full Stack Web Development", "Computer Science & Engineering", 6, 3, 4),
        ("CS605", "Cyber Security & Cryptography", "Computer Science & Engineering", 6, 4, 3)
    ]

    for c in courses_data:
        cursor.execute("""
            INSERT INTO courses (course_code, course_name, department, semester, credits, faculty_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, c)

    # Attendance logs for students over recent dates
    today = datetime.now().date()
    statuses = ["Present", "Present", "Present", "Present", "Absent", "Late"]
    
    # Aarav (student@campus.ai) has id 5
    for days_ago in range(14, -1, -1):
        log_date = today - timedelta(days=days_ago)
        if log_date.weekday() < 5:  # Monday to Friday
            for c_id in range(1, 6):
                # Ensure high attendance around 88%
                status = "Present" if (days_ago % 5 != 0 or c_id != 2) else "Absent"
                method = "Face Recognition" if status == "Present" else "Manual"
                confidence = 96.4 if status == "Present" else 0.0
                cursor.execute("""
                    INSERT INTO attendance (student_id, course_id, date, status, method, confidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (5, c_id, log_date.strftime("%Y-%m-%d"), status, method, confidence))

    # Exam Schedules
    exam_data = [
        (1, "Mid-Semester Theory Exam", "2026-11-10", "10:00 AM", "01:00 PM", "Hall A - Tech Block", 6),
        (2, "Practical Lab Assessment", "2026-11-12", "02:00 PM", "05:00 PM", "AI Lab 302", 6),
        (3, "Written Examination", "2026-11-15", "10:00 AM", "01:00 PM", "Hall C - Main Campus", 6),
        (4, "Mini-Project Evaluation", "2026-11-18", "09:30 AM", "12:30 PM", "Innovation Hub 2", 6),
        (5, "End-Semester Examination", "2026-11-22", "10:00 AM", "01:00 PM", "Auditorium Hall", 6)
    ]
    for e in exam_data:
        cursor.execute("""
            INSERT INTO exam_schedules (course_id, exam_name, exam_date, start_time, end_time, hall, semester)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, e)

    # Notifications & Notices
    notices_data = [
        ("Final Semester Examination Schedule Released", "The timetable for November 2026 Semester Examinations has been finalized. Download your hall tickets from the student portal before Nov 5th.", "Exams", "Urgent", 1, "all"),
        ("Smart Campus AI Hackathon 2026", "Registrations are now open for the annual 36-hour Innovation Hackathon! Prize pool worth INR 1,50,000. Form teams of 3-4 and submit abstracts by Nov 12.", "Events", "High", 2, "all"),
        ("Library Weekend Hours & Digital Kiosk Access", "The Central Digital Library will remain open 24/7 during exam weeks with high-speed Wi-Fi and quiet study pods available upon reservation.", "Academic", "Normal", 1, "student"),
        ("Campus Placement Drive: Top Tech Giants", "Mega recruitment drive for 2026-2027 batch starting next week. Eligible branches: CSE, AI/DS, ECE. Ensure your resumes and GitHub portfolios are updated.", "Placement", "Urgent", 2, "student"),
        ("Smart Face Attendance System Deployed", "Please ensure your student profile photo is clear and updated in the system for automated contactless biometric attendance logging.", "General", "High", 1, "all")
    ]
    for n in notices_data:
        cursor.execute("""
            INSERT INTO notifications (title, content, category, priority, author_id, target_role)
            VALUES (?, ?, ?, ?, ?, ?)
        """, n)

    # Chatbot Knowledge Base
    faq_data = [
        ("When are the semester exams scheduled?", "Semester examinations begin on November 10th, 2026. You can view the complete schedule under your Student Dashboard -> Examination Schedules.", "Exams", "exam,schedule,timetable,date,dates,semester"),
        ("How do I check my attendance percentage?", "You can check your overall and subject-wise attendance in the Student Dashboard or the Smart Attendance section. A minimum of 75% attendance is required to appear for final exams.", "Attendance", "attendance,percentage,absent,present,shortage,criteria"),
        ("How does the Smart Face Attendance work?", "Our system utilizes computer vision to automatically detect and verify registered student faces via the classroom webcam or kiosk, recording timestamps with high accuracy.", "Attendance", "face,camera,biometric,recognition,smart attendance,kiosk"),
        ("Where can I find placement drive updates?", "Upcoming placement drives and company criteria are posted under the Notifications tab with the 'Placement' tag. The Training & Placement Cell also shares weekly drive links.", "Placement", "placement,job,internship,company,drive,tpo,recruit"),
        ("What are the Central Library timings?", "The Central Library is open Monday to Saturday from 8:00 AM to 10:00 PM. During examination months, the 24/7 reading rooms are accessible with student ID cards.", "Academic", "library,timings,books,open,hours,borrow"),
        ("How can I apply for fee concession or scholarships?", "Scholarship applications and fee payment receipts can be submitted via the Administration office or the Academic Accounts portal before the 15th of every semester.", "General", "fee,fees,scholarship,concession,payment,dues"),
        ("What is the Wi-Fi password for students?", "Connect to 'Campus-Student-5G' and authenticate using your Roll Number and your portal password. For technical assistance, visit IT Helpdesk in Room 104.", "General", "wifi,internet,network,password,connect,it support"),
        ("Who is the Head of Department for CSE?", "The Head of the Computer Science & Engineering Department is Prof. Ananya Sen (Cabin: CS-Block 201, Email: ananya.sen@campus.ai).", "Academic", "hod,faculty,department,head,ananya,cse,contact"),
        ("What clubs and extracurricular activities are active?", "We have active student chapters including AI & Robotics Club, Google Developer Groups, CyberSec Club, Cultural Dance & Music Guild, and Sports Society.", "Events", "club,events,activities,hackathon,cultural,sports"),
        ("What happens if my attendance falls below 75%?", "If your attendance is between 65% and 74%, you must submit medical or authorized documentation to your HOD for condonation. Below 65% requires repeating the course.", "Attendance", "low attendance,condonation,detained,below 75,shortage")
    ]
    for f in faq_data:
        cursor.execute("""
            INSERT INTO chatbot_faq (question, answer, category, keywords)
            VALUES (?, ?, ?, ?)
        """, f)

    conn.commit()
