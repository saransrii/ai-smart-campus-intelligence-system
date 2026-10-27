# 🎓 AI Smart Campus – Intelligence System

### An AI-Powered Smart Campus Management Platform

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask%203.x-green.svg)](https://flask.palletsprojects.com/)
[![OpenCV](https://img.shields.io/badge/Computer%20Vision-OpenCV%20Haar-red.svg)](https://opencv.org/)
[![Chart.js](https://img.shields.io/badge/Analytics-Chart.js-orange.svg)](https://www.chartjs.org/)
[![License](https://img.shields.io/badge/License-Academic%20%2F%20MIT-purple.svg)]()

---

## 📌 Project Overview

**AI Smart Campus – Intelligence System** is an intelligent web-based platform designed to simplify and improve campus management using Artificial Intelligence (AI), Computer Vision, and modern web technologies.

The system provides a centralized platform for students, faculty members, and administrators to access critical academic information. It integrates features such as an **AI NLP Chatbot**, **Smart Face Biometric Attendance**, **Interactive Campus Analytics**, **Role-Adaptive Dashboards**, and **Instant Notices**.

---

## 🎯 Objectives

- **Centralized Platform:** Unify academic, attendance, examination, and administrative modules in a single portal.
- **AI Conversational Assistant:** Provide instant answers to student queries, timetables, and rules using NLP and personalized student data lookup.
- **Biometric Smart Attendance:** Automate attendance tracking via webcam face detection and verification with confidence scoring.
- **Visual Campus Analytics:** Display interactive trends, department distributions, and CGPA performance using Chart.js.
- **Timely Notifications:** Publish urgent announcements, exam schedules, and placement updates with multi-channel filtering.
- **Role-Based Collaboration:** Distinct tailored interfaces for Students, Faculty, and Administrators.

---

## ✨ Key Features & Modules

### 1. 🔐 User Authentication & Authorization
- Dual identification login via **Roll Number** (e.g. `CS2026001`) or **Campus Email**.
- Secure password hashing using `werkzeug.security` (`pbkdf2:sha256`).
- Role-based permissions guarding routes for **Student**, **Faculty**, and **Administrator**.
- Password reset and registration workflows with instant demo account quick-fill options.

### 2. 📊 Student & Faculty Dashboard
- **Student View:** Real-time overall attendance percentage with automatic alert if below 75%, subject-wise attendance breakdown, upcoming exam timetable with hall allocations, and recent campus notices.
- **Faculty / Admin View:** Total enrolled students, active faculty counts, overall campus attendance rate, live attendance verification feed, and rapid management shortcuts.

### 3. 🤖 AI Campus Chatbot
- NLP keyword scoring and intent matching engine.
- Personalized dynamic responses:
  - *"What is my attendance?"* -> Automatically computes logged-in student's subject-by-subject attendance rate and warning threshold.
  - *"When are semester exams?"* -> Fetches user's upcoming examination timetable from database.
  - *"Show recent notices"* -> Returns latest prioritized announcements.
- Integrated **Speech Recognition** (Dictation via Web Speech API) and **Text-to-Speech** read-out.
- Floating assistant available across all pages + full-page conversational interface.

### 4. 🧑🎓 Smart Biometric Attendance
- Live webcam integration using browser WebRTC (`navigator.mediaDevices.getUserMedia`).
- Computer Vision backend with **OpenCV Haar Cascade Face Detection** evaluating facial features, presence, and sharpness (anti-blur scoring).
- Automated deduplication (prevents marking attendance twice on the same day).
- One-click CSV Export of attendance records for faculty audits.
- Manual entry override tab for instructors.

### 5. 📈 Campus Analytics
- **Attendance Trajectory:** Line chart comparing present vs. absent trends.
- **Department Distribution:** Interactive doughnut chart of student enrollments.
- **Academic Performance:** Bar chart mapping CGPA distribution brackets.
- **Course Attendance Averages:** Horizontal bar chart highlighting courses falling below 75%.

### 6. 🔔 Notifications & Notice Board
- Categorized circulars: *Exams*, *Events*, *Academic*, *Placement*, and *General*.
- Priority tags: *Urgent* (high alert), *High*, *Normal*.
- Full-text search and category filtering chips.
- Faculty / Admin modal to post new notices with target audience selection.

---

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| **HTML5 & CSS3** | Modern semantic structure and glassmorphism styling |
| **JavaScript (ES6+)** | WebRTC camera streaming, Web Speech API, dynamic AJAX |
| **Python 3.10+** | Backend server runtime and AI logic |
| **Flask 3.x** | Web application framework and REST APIs |
| **OpenCV (`cv2`)** | Real-time computer vision face detection |
| **SQLite / MySQL** | Dual-compatible database engine with auto-seeding |
| **Chart.js** | Interactive campus analytics charts |
| **Bootstrap 5 & FontAwesome** | Responsive layout and UI iconography |

---

## 📂 Project Structure

```text
internship project/
│
├── app.py                     # Main Flask Application & REST API Routes
├── ai_chatbot.py              # NLP Chatbot Engine & Query Parser
├── face_attendance.py         # OpenCV Face Detection & Biometric Logic
├── requirements.txt           # Python Project Dependencies
├── README.md                  # Complete Project Documentation
│
├── database/
│   ├── schema.sql             # SQL Database Schema (MySQL & SQLite compatible)
│   ├── db.py                  # Database connection, helpers, and sample seed data
│   └── smart_campus.db        # SQLite Database (auto-generated on first run)
│
├── templates/
│   ├── base.html              # Core Layout, Navigation & Floating Assistant
│   ├── login.html             # Sign In with Quick Demo Switcher
│   ├── register.html          # User Registration with Role Select
│   ├── reset_password.html    # Password Recovery
│   ├── dashboard.html         # Role-Adaptive Student & Faculty Dashboard
│   ├── attendance.html        # Biometric Scanner, Camera Feed & Records
│   ├── chatbot.html           # Full-Page Conversational AI Assistant
│   ├── analytics.html         # Visual Campus Analytics with Chart.js
│   ├── notifications.html     # Circulars & Announcements Board
│   └── profile.html           # User Profile & Biometric Status
│
└── static/
    ├── css/
    │   └── style.css          # Glassmorphism, Theme Variables & Animation
    └── js/
        └── script.js          # Theme Toggle & Global Floating Widget
```

---

## 🔑 Pre-Configured Demo Credentials

The application comes pre-populated with realistic demo accounts for immediate testing:

| Role | Roll / Email | Password | Key Permissions |
|---|---|---|---|
| 🎓 **Student** | `student@campus.ai` *(or `CS2026001`)* | `student123` | View personal attendance, timetable, exams, take face attendance |
| 👨‍🏫 **Faculty** | `faculty@campus.ai` *(or `FAC101`)* | `faculty123` | View class records, mark manual attendance, post circulars |
| 🛡️ **Administrator** | `admin@campus.ai` | `admin123` | Campus analytics, roster oversight, administrative announcements |

---

## ⚙️ Installation and Setup

### Prerequisites
- Python 3.10 or higher
- Modern Web Browser (Google Chrome, Microsoft Edge, or Mozilla Firefox)
- Webcam (for live face attendance features)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Run the Application

```bash
python app.py
```

### Step 3: Access the Portal

Open your web browser and navigate to:
```text
http://127.0.0.1:5000
```

*Note: Database tables and sample seed records are automatically created on the first launch.*

---

## 🔒 Security Considerations

- **Password Hashing:** Passwords are never stored in plain text; salted hashes (`pbkdf2:sha256`) are verified via Werkzeug.
- **SQL Injection Prevention:** All database operations utilize parameterized queries (`?`).
- **Role Verification:** Critical endpoints enforce decorators (`@login_required`, `@role_required`).
- **Biometric Quality Control:** Computer vision enforces Laplacian variance sharpness thresholds to prevent low-quality frames.

---

## 🚀 Future Enhancements

- 📱 Progressive Web App (PWA) with push notifications for examination alerts.
- 🎙️ Full duplex voice assistant with real-time audio conversation.
- 🧠 Machine learning student performance and dropout risk prediction.
- 📍 GPS geofencing verification for classroom attendance.

---

## 👩💻 Project Information

- **Project Name:** AI Smart Campus – Intelligence System
- **Domain:** Artificial Intelligence, Computer Vision & Smart Education
- **Academic Year:** 2026–2027
- **License:** Educational / Academic Purpose
