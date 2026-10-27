import os
import io
import csv
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, Response, send_file
)
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_db_connection, init_db
from ai_chatbot import chatbot_engine
from face_attendance import face_attendance_system

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ai_smart_campus_super_secret_key_2026')

# Initialize DB upon starting
with app.app_context():
    init_db()

# ----------------- Decorators & Helpers ----------------- #

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if session.get('role') not in allowed_roles:
                flash("You do not have permission to view that page.", "danger")
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    if 'user_id' not in session:
        return None
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    conn.close()
    return user

@app.context_processor
def inject_user():
    return dict(current_user=get_current_user(), now=datetime.now())

# ----------------- Authentication Routes ----------------- #

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '').strip()

        if not identifier or not password:
            flash("Please enter both roll number/email and password.", "danger")
            return render_template('login.html')

        conn = get_db_connection()
        # Find user by either email or roll_number
        user = conn.execute("""
            SELECT * FROM users WHERE lower(email) = lower(?) OR lower(roll_number) = lower(?)
        """, (identifier, identifier)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['role'] = user['role']
            session['email'] = user['email']
            session['roll_number'] = user['roll_number']
            session['department'] = user['department']

            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid roll number/email or password. Please try again.", "danger")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        roll_number = request.form.get('roll_number', '').strip().upper() or None
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'student').lower()
        department = request.form.get('department', 'Computer Science & Engineering')
        semester = request.form.get('semester', 1)
        phone = request.form.get('phone', '')

        if not name or not email or not password:
            flash("Name, email, and password are required.", "danger")
            return render_template('register.html')

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html')

        conn = get_db_connection()
        # Check if email or roll number exists
        existing = conn.execute("SELECT id FROM users WHERE lower(email) = lower(?)", (email,)).fetchone()
        if existing:
            conn.close()
            flash("An account with this email address already exists.", "danger")
            return render_template('register.html')

        if roll_number:
            existing_roll = conn.execute("SELECT id FROM users WHERE roll_number = ?", (roll_number,)).fetchone()
            if existing_roll:
                conn.close()
                flash("An account with this roll number already exists.", "danger")
                return render_template('register.html')

        pw_hash = generate_password_hash(password)
        conn.execute("""
            INSERT INTO users (roll_number, name, email, password_hash, role, department, semester, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (roll_number, name, email, pw_hash, role, department, semester, phone))
        conn.commit()
        conn.close()

        flash("Account created successfully! Please log in with your credentials.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not email or not new_password:
            flash("Email and new password are required.", "danger")
            return render_template('reset_password.html')

        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('reset_password.html')

        conn = get_db_connection()
        user = conn.execute("SELECT id FROM users WHERE lower(email) = lower(?)", (email,)).fetchone()
        if not user:
            conn.close()
            flash("No account registered with that email address.", "danger")
            return render_template('reset_password.html')

        pw_hash = generate_password_hash(new_password)
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (pw_hash, user['id']))
        conn.commit()
        conn.close()

        flash("Your password has been successfully reset. Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('reset_password.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for('login'))

# ----------------- Main Module Views ----------------- #

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    conn = get_db_connection()

    # Get recent notifications
    notifications = conn.execute("""
        SELECT n.*, u.name as author_name 
        FROM notifications n
        LEFT JOIN users u ON n.author_id = u.id
        ORDER BY n.created_at DESC LIMIT 4
    """).fetchall()

    # Get courses
    courses = conn.execute("SELECT * FROM courses").fetchall()

    data = {
        "notifications": notifications,
        "courses": courses
    }

    if user['role'] == 'student':
        # Student-specific stats
        # Overall Attendance
        att_row = conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_count
            FROM attendance
            WHERE student_id = ?
        """, (user['id'],)).fetchone()

        total = att_row['total'] if att_row and att_row['total'] else 0
        present = att_row['present_count'] if att_row and att_row['present_count'] else 0
        pct = round((present / total * 100), 1) if total > 0 else 0

        # Course-wise breakdown
        course_attendance = conn.execute("""
            SELECT c.id, c.course_code, c.course_name, c.credits,
                   COUNT(a.id) as total_sessions,
                   SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as attended
            FROM courses c
            LEFT JOIN attendance a ON c.id = a.course_id AND a.student_id = ?
            GROUP BY c.id
        """, (user['id'],)).fetchall()

        # Upcoming Exams
        exams = conn.execute("""
            SELECT e.*, c.course_code, c.course_name
            FROM exam_schedules e
            JOIN courses c ON e.course_id = c.id
            ORDER BY e.exam_date ASC
            LIMIT 5
        """).fetchall()

        data.update({
            "overall_attendance": pct,
            "total_sessions": total,
            "attended_sessions": present,
            "course_attendance": course_attendance,
            "exams": exams
        })

    elif user['role'] in ['faculty', 'admin']:
        # Faculty & Admin stats
        total_students = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'student'").fetchone()[0]
        total_faculty = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'faculty'").fetchone()[0]
        total_courses = conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        
        # Overall attendance rate across campus
        camp_att = conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_cnt
            FROM attendance
        """).fetchone()
        camp_pct = round((camp_att['present_cnt'] / camp_att['total'] * 100), 1) if camp_att['total'] else 0

        # Today's attendance logs
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_logs = conn.execute("""
            SELECT a.*, u.name as student_name, u.roll_number, c.course_code, c.course_name
            FROM attendance a
            JOIN users u ON a.student_id = u.id
            JOIN courses c ON a.course_id = c.id
            WHERE a.date = ?
            ORDER BY a.timestamp DESC
            LIMIT 6
        """, (today_str,)).fetchall()

        data.update({
            "total_students": total_students,
            "total_faculty": total_faculty,
            "total_courses": total_courses,
            "campus_attendance_rate": camp_pct,
            "today_logs": today_logs
        })

    conn.close()
    return render_template('dashboard.html', data=data)

@app.route('/attendance')
@login_required
def attendance():
    user = get_current_user()
    conn = get_db_connection()

    courses = conn.execute("SELECT * FROM courses").fetchall()
    students = conn.execute("SELECT id, roll_number, name, department FROM users WHERE role = 'student' ORDER BY roll_number").fetchall()

    # Query attendance records
    if user['role'] == 'student':
        records = conn.execute("""
            SELECT a.*, c.course_code, c.course_name, u.name as student_name, u.roll_number
            FROM attendance a
            JOIN courses c ON a.course_id = c.id
            JOIN users u ON a.student_id = u.id
            WHERE a.student_id = ?
            ORDER BY a.date DESC, a.timestamp DESC
        """, (user['id'],)).fetchall()
    else:
        records = conn.execute("""
            SELECT a.*, c.course_code, c.course_name, u.name as student_name, u.roll_number
            FROM attendance a
            JOIN courses c ON a.course_id = c.id
            JOIN users u ON a.student_id = u.id
            ORDER BY a.date DESC, a.timestamp DESC
            LIMIT 100
        """).fetchall()

    conn.close()
    return render_template('attendance.html', courses=courses, students=students, records=records)

@app.route('/chatbot')
@login_required
def chatbot():
    return render_template('chatbot.html')

@app.route('/analytics')
@login_required
def analytics():
    conn = get_db_connection()
    total_students = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'student'").fetchone()[0]
    total_faculty = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'faculty'").fetchone()[0]
    total_courses = conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    
    # Campus attendance calculation
    camp_att = conn.execute("""
        SELECT COUNT(*) as total, SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_cnt
        FROM attendance
    """).fetchone()
    camp_pct = round((camp_att['present_cnt'] / camp_att['total'] * 100), 1) if camp_att['total'] else 0

    stats = {
        "total_students": total_students,
        "total_faculty": total_faculty,
        "total_courses": total_courses,
        "campus_attendance_rate": camp_pct
    }
    conn.close()
    return render_template('analytics.html', stats=stats)

@app.route('/notifications')
@login_required
def notifications():
    conn = get_db_connection()
    notices = conn.execute("""
        SELECT n.*, u.name as author_name, u.role as author_role
        FROM notifications n
        LEFT JOIN users u ON n.author_id = u.id
        ORDER BY n.created_at DESC
    """).fetchall()
    conn.close()
    return render_template('notifications.html', notices=notices)

@app.route('/profile')
@login_required
def profile():
    user = get_current_user()
    return render_template('profile.html', user=user)

# ----------------- API Endpoints ----------------- #

@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    if not message:
        return jsonify({"success": False, "answer": "Please ask a question."})

    user_id = session.get('user_id')
    response = chatbot_engine.respond(message, user_id=user_id)
    return jsonify({
        "success": True,
        "answer": response["answer"],
        "confidence": response.get("confidence", 90.0),
        "suggestions": response.get("suggestions", [])
    })

@app.route('/api/attendance/face-scan', methods=['POST'])
@login_required
def api_face_scan():
    data = request.get_json() or {}
    image_base64 = data.get('image', '')
    course_id = data.get('course_id')
    
    # If student, student_id is logged-in user; if faculty, student_id can be passed or selected
    user = get_current_user()
    if user['role'] == 'student':
        student_id = user['id']
    else:
        student_id = data.get('student_id', user['id'])

    if not image_base64 or not course_id:
        return jsonify({"success": False, "message": "Missing image capture or course selection."})

    result = face_attendance_system.process_attendance_scan(image_base64, student_id, course_id)
    return jsonify(result)

@app.route('/api/attendance/manual-mark', methods=['POST'])
@login_required
@role_required(['faculty', 'admin'])
def api_manual_mark():
    student_id = request.form.get('student_id')
    course_id = request.form.get('course_id')
    status = request.form.get('status', 'Present')
    date_str = request.form.get('date', datetime.now().strftime("%Y-%m-%d"))

    if not student_id or not course_id:
        flash("Student and course are required.", "danger")
        return redirect(url_for('attendance'))

    conn = get_db_connection()
    # Check if record exists for this date
    existing = conn.execute("""
        SELECT id FROM attendance WHERE student_id = ? AND course_id = ? AND date = ?
    """, (student_id, course_id, date_str)).fetchone()

    if existing:
        conn.execute("UPDATE attendance SET status = ?, method = 'Manual' WHERE id = ?", (status, existing['id']))
        flash("Attendance updated successfully.", "info")
    else:
        conn.execute("""
            INSERT INTO attendance (student_id, course_id, date, status, method, confidence)
            VALUES (?, ?, ?, ?, 'Manual', 100.0)
        """, (student_id, course_id, date_str, status))
        flash("Attendance marked successfully.", "success")

    conn.commit()
    conn.close()
    return redirect(url_for('attendance'))

@app.route('/api/attendance/export')
@login_required
def api_export_attendance():
    conn = get_db_connection()
    user = get_current_user()

    if user['role'] == 'student':
        records = conn.execute("""
            SELECT u.roll_number, u.name as student_name, c.course_code, c.course_name, a.date, a.status, a.method, a.confidence, a.timestamp
            FROM attendance a
            JOIN users u ON a.student_id = u.id
            JOIN courses c ON a.course_id = c.id
            WHERE a.student_id = ?
            ORDER BY a.date DESC
        """, (user['id'],)).fetchall()
    else:
        records = conn.execute("""
            SELECT u.roll_number, u.name as student_name, c.course_code, c.course_name, a.date, a.status, a.method, a.confidence, a.timestamp
            FROM attendance a
            JOIN users u ON a.student_id = u.id
            JOIN courses c ON a.course_id = c.id
            ORDER BY a.date DESC
        """).fetchall()

    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Roll Number", "Student Name", "Course Code", "Course Name", "Date", "Status", "Method", "Confidence (%)", "Timestamp"])

    for r in records:
        writer.writerow([r["roll_number"], r["student_name"], r["course_code"], r["course_name"], r["date"], r["status"], r["method"], r["confidence"], r["timestamp"]])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=campus_attendance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

@app.route('/api/analytics-data')
@login_required
def api_analytics_data():
    conn = get_db_connection()

    # 1. Attendance trend over last 7 days
    dates = []
    present_counts = []
    absent_counts = []
    
    rows = conn.execute("""
        SELECT date, 
               SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as p_count,
               SUM(CASE WHEN status != 'Present' THEN 1 ELSE 0 END) as a_count
        FROM attendance
        GROUP BY date
        ORDER BY date DESC
        LIMIT 7
    """).fetchall()

    for r in reversed(rows):
        dates.append(r['date'])
        present_counts.append(r['p_count'])
        absent_counts.append(r['a_count'])

    # 2. Department-wise student distribution
    dept_rows = conn.execute("""
        SELECT department, COUNT(*) as count 
        FROM users 
        WHERE role = 'student' 
        GROUP BY department
    """).fetchall()
    dept_labels = [d['department'] for d in dept_rows]
    dept_values = [d['count'] for d in dept_rows]

    # 3. CGPA distribution
    cgpa_rows = conn.execute("""
        SELECT 
            CASE 
                WHEN cgpa >= 9.0 THEN '9.0 - 10.0 (Outstanding)'
                WHEN cgpa >= 8.0 THEN '8.0 - 8.9 (Excellent)'
                WHEN cgpa >= 7.0 THEN '7.0 - 7.9 (Good)'
                ELSE 'Below 7.0 (Needs Improvement)'
            END as cgpa_band,
            COUNT(*) as count
        FROM users
        WHERE role = 'student' AND cgpa IS NOT NULL
        GROUP BY cgpa_band
    """).fetchall()
    cgpa_labels = [c['cgpa_band'] for c in cgpa_rows]
    cgpa_values = [c['count'] for c in cgpa_rows]

    # 4. Course Attendance Rates
    course_att_rows = conn.execute("""
        SELECT c.course_code, 
               COUNT(a.id) as total,
               SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_cnt
        FROM courses c
        LEFT JOIN attendance a ON c.id = a.course_id
        GROUP BY c.id
    """).fetchall()
    course_codes = [c['course_code'] for c in course_att_rows]
    course_rates = [
        round((c['present_cnt'] / c['total'] * 100), 1) if c['total'] > 0 else 0
        for c in course_att_rows
    ]

    conn.close()

    return jsonify({
        "trend": {
            "dates": dates,
            "present": present_counts,
            "absent": absent_counts
        },
        "departments": {
            "labels": dept_labels,
            "values": dept_values
        },
        "cgpa": {
            "labels": cgpa_labels,
            "values": cgpa_values
        },
        "courses": {
            "labels": course_codes,
            "values": course_rates
        }
    })

@app.route('/api/notifications/create', methods=['POST'])
@login_required
@role_required(['faculty', 'admin'])
def api_create_notification():
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    category = request.form.get('category', 'General')
    priority = request.form.get('priority', 'Normal')
    target_role = request.form.get('target_role', 'all')

    if not title or not content:
        flash("Notice title and content cannot be empty.", "danger")
        return redirect(url_for('notifications'))

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO notifications (title, content, category, priority, author_id, target_role)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (title, content, category, priority, session['user_id'], target_role))
    conn.commit()
    conn.close()

    flash("Notification published successfully!", "success")
    return redirect(url_for('notifications'))

@app.route('/api/notifications/delete/<int:notice_id>', methods=['POST'])
@login_required
@role_required(['faculty', 'admin'])
def api_delete_notification(notice_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM notifications WHERE id = ?", (notice_id,))
    conn.commit()
    conn.close()

    flash("Notification deleted.", "info")
    return redirect(url_for('notifications'))

if __name__ == '__main__':
    # Start the server on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
