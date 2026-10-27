import re
import math
from database.db import get_db_connection

class CampusChatbot:
    """Intelligent AI Campus Assistant with NLP keyword scoring, intent matching, and dynamic student data retrieval."""

    def __init__(self):
        self.common_greetings = {
            "hello": "Hello! I am your AI Smart Campus Assistant. How can I assist you with your academic activities today?",
            "hi": "Hi there! I can help you with attendance, examination timetables, notices, faculty details, and campus guidelines.",
            "hey": "Hey! Looking for exam schedules, attendance status, or campus announcements? Ask away!",
            "who are you": "I am the AI Smart Campus Assistant, an intelligent system designed to help students, faculty, and administrators find information quickly.",
            "what can you do": "I can help you check your personalized attendance, view exam schedules, look up notices, get library timings, contact faculty, and answer general campus queries.",
            "thanks": "You're welcome! Let me know if you need any more campus assistance.",
            "thank you": "Glad to help! Have a productive day at the campus!",
            "bye": "Goodbye! Best of luck with your studies and classes!"
        }

    def clean_text(self, text):
        """Clean and normalize input text."""
        return re.sub(r'[^a-zA-Z0-9\s]', '', text.lower()).strip()

    def get_user_personalized_data(self, user_id, message_lower):
        """Check for personalized queries such as user's attendance or exams."""
        if not user_id:
            return None

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check for attendance intent
        if any(w in message_lower for w in ["my attendance", "my percentage", "check attendance", "my absences"]):
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_count
                FROM attendance
                WHERE student_id = ?
            """, (user_id,))
            row = cursor.fetchone()
            
            cursor.execute("""
                SELECT c.course_code, c.course_name,
                       COUNT(a.id) as total_classes,
                       SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as attended
                FROM courses c
                LEFT JOIN attendance a ON c.id = a.course_id AND a.student_id = ?
                GROUP BY c.id
            """, (user_id,))
            courses = cursor.fetchall()
            conn.close()

            total = row['total'] if row and row['total'] else 0
            present = row['present_count'] if row and row['present_count'] else 0
            pct = round((present / total * 100), 1) if total > 0 else 0

            status_note = "🎉 Excellent! You are well above the 75% threshold." if pct >= 75 else "⚠️ Warning: Your attendance is below 75%! Please attend upcoming lectures."
            
            course_summary = "\n".join([
                f"• **{c['course_code']}** ({c['course_name']}): {round((c['attended'] or 0)/(c['total_classes'] or 1)*100, 1)}% ({c['attended'] or 0}/{c['total_classes'] or 0} sessions)"
                for c in courses
            ])

            return {
                "answer": f"📊 **Your Overall Attendance Summary:**\n\n- **Overall Percentage:** **{pct}%** ({present}/{total} sessions attended)\n- **Status:** {status_note}\n\n**Subject Breakdown:**\n{course_summary}\n\nYou can view full logs under the **Smart Attendance** tab.",
                "suggestions": ["When are my exams?", "Latest Notices", "Library Hours"]
            }

        # Check for user's exam schedule intent
        if any(w in message_lower for w in ["my exam", "exam schedule", "exam timetable", "when are my exams"]):
            cursor.execute("""
                SELECT e.exam_name, e.exam_date, e.start_time, e.end_time, e.hall, c.course_code, c.course_name
                FROM exam_schedules e
                JOIN courses c ON e.course_id = c.id
                ORDER BY e.exam_date ASC
            """)
            exams = cursor.fetchall()
            conn.close()

            if exams:
                exam_lines = "\n".join([
                    f"📅 **{e['exam_date']}** ({e['start_time']} - {e['end_time']})\n   • **Course:** {e['course_code']} - {e['exam_name']}\n   • **Location:** {e['hall']}"
                    for e in exams
                ])
                return {
                    "answer": f"📝 **Upcoming Examination Timetable:**\n\n{exam_lines}\n\nRemember to carry your Student ID Card and Hall Ticket!",
                    "suggestions": ["What is my attendance?", "Library Hours", "Placement Notices"]
                }

        # Check for notices
        if any(w in message_lower for w in ["latest notice", "announcements", "notices", "recent events"]):
            cursor.execute("SELECT title, category, priority, created_at FROM notifications ORDER BY created_at DESC LIMIT 3")
            notices = cursor.fetchall()
            conn.close()

            if notices:
                lines = "\n".join([
                    f"🔔 **[{n['category']}]** {n['title']} *(Priority: {n['priority']})*"
                    for n in notices
                ])
                return {
                    "answer": f"📢 **Recent Campus Announcements:**\n\n{lines}\n\nVisit the **Notifications** tab for complete details.",
                    "suggestions": ["My Attendance", "Exam Timetable", "Campus Wi-Fi"]
                }

        conn.close()
        return None

    def match_faq(self, query):
        """Match query against database FAQ using weighted keyword relevance and word overlap."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, question, answer, category, keywords FROM chatbot_faq")
        faqs = cursor.fetchall()
        conn.close()

        clean_query = self.clean_text(query)
        query_words = set(clean_query.split())

        best_match = None
        highest_score = 0.0

        for faq in faqs:
            q_clean = self.clean_text(faq['question'])
            q_words = set(q_clean.split())

            keyword_list = [k.strip().lower() for k in (faq['keywords'] or '').split(',') if k.strip()]
            
            score = 0.0
            # Check question overlap
            overlap = query_words.intersection(q_words)
            score += len(overlap) * 2.0

            # Check keyword match
            for kw in keyword_list:
                if kw in clean_query:
                    score += 3.0
                elif any(qw == kw for qw in query_words):
                    score += 2.5

            # Exact question match bonus
            if q_clean in clean_query or clean_query in q_clean:
                score += 5.0

            if score > highest_score:
                highest_score = score
                best_match = faq

        # Threshold for confidence
        if best_match and highest_score >= 2.0:
            return {
                "answer": best_match['answer'],
                "category": best_match['category'],
                "confidence": min(99.0, round(highest_score * 15.0, 1)),
                "suggestions": ["Check Exam Dates", "View My Attendance", "Campus Library Hours", "Placement Updates"]
            }

        return None

    def respond(self, query, user_id=None):
        """Main response pipeline: Greetings -> User-personalized -> FAQ Match -> Fallback."""
        cleaned = self.clean_text(query)

        # 1. Direct Greeting / Casual match
        if cleaned in self.common_greetings:
            return {
                "answer": self.common_greetings[cleaned],
                "confidence": 100.0,
                "suggestions": ["What is my attendance?", "When are semester exams?", "Where are placement drives?", "Library timings"]
            }

        # Check for partial greetings
        for greet, resp in self.common_greetings.items():
            if cleaned.startswith(greet + " ") or cleaned.endswith(" " + greet):
                return {
                    "answer": resp,
                    "confidence": 95.0,
                    "suggestions": ["What is my attendance?", "Exam timetable", "Campus notices"]
                }

        # 2. Personalized student query
        personalized = self.get_user_personalized_data(user_id, query.lower())
        if personalized:
            personalized["confidence"] = 98.0
            return personalized

        # 3. Knowledge base FAQ match
        faq_res = self.match_faq(query)
        if faq_res:
            return faq_res

        # 4. Fallback intelligent response
        return {
            "answer": "I don't have exact information regarding that specific query yet. 💡 You can try asking about:\n\n"
                      "• **Attendance & Criteria** (e.g. *What is my attendance percentage?*)\n"
                      "• **Examinations** (e.g. *When are semester exams?*)\n"
                      "• **Notices & Events** (e.g. *Show recent campus announcements*)\n"
                      "• **Campus Facilities** (e.g. *Library timings, Wi-Fi password, HOD contact*)\n\n"
                      "Alternatively, contact the Academic Helpdesk at **support@campus.ai** or Room 101, Administrative Block.",
            "confidence": 40.0,
            "suggestions": ["What is my attendance?", "Exam Timetable", "Placement Drives", "Library Timings"]
        }

chatbot_engine = CampusChatbot()
