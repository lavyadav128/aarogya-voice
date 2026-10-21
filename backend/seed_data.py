"""
Seed script to populate initial doctors, slots, and sample call data.
"""

from datetime import datetime, timedelta
from backend.database import get_db_connection

DOCTORS = [
    ("Dr. Rajesh Sharma", "General Physician", "MBBS, MD (Medicine)", "Room 101", 300),
    ("Dr. Ananya Rao", "Pediatrician", "MBBS, MD (Pediatrics)", "Room 104", 400),
    ("Dr. Vikram Patel", "Orthopedic", "MBBS, MS (Orthopedics)", "Room 108", 450),
    ("Dr. Meera Iyer", "Gynecologist", "MBBS, MS (OB-GYN)", "Room 112", 400),
]

SLOT_TIMES = [
    "09:30 AM", "10:00 AM", "10:30 AM", "11:00 AM",
    "11:30 AM", "04:00 PM", "04:30 PM", "05:00 PM", "05:30 PM"
]

def seed_all():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if doctors already exist
    cursor.execute("SELECT COUNT(*) FROM doctors")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO doctors (name, department, qualification, room, consultation_fee)
            VALUES (?, ?, ?, ?, ?)
        """, DOCTORS)
        conn.commit()
        print("[SEED] Inserted doctors.")

    # Populate slots for today and tomorrow
    today_str = datetime.now().strftime("%Y-%m-%d")
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    cursor.execute("SELECT id FROM doctors")
    doc_ids = [row["id"] for row in cursor.fetchall()]

    for d_id in doc_ids:
        for day in [today_str, tomorrow_str]:
            for slot in SLOT_TIMES:
                cursor.execute("""
                    SELECT id FROM slots WHERE doctor_id = ? AND date = ? AND slot_time = ?
                """, (d_id, day, slot))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO slots (doctor_id, date, slot_time, is_booked)
                        VALUES (?, ?, ?, 0)
                    """, (d_id, day, slot))
    conn.commit()

    # Seed sample appointments if none exist
    cursor.execute("SELECT COUNT(*) FROM appointments")
    if cursor.fetchone()[0] == 0:
        sample_appointments = [
            (101, "Suresh Kumar", "+919845012345", "Dr. Rajesh Sharma", "General Physician", today_str, "10:00 AM", "Viral fever with chills for 3 days", "URGENT", "CONFIRMED", datetime.now().isoformat()),
            (102, "Sunita Devi", "+919731234567", "Dr. Meera Iyer", "Gynecologist", today_str, "11:30 AM", "Routine prenatal checkup", "ROUTINE", "CONFIRMED", datetime.now().isoformat()),
            (103, "Master Aarav (Age 5)", "+919886098765", "Dr. Ananya Rao", "Pediatrician", today_str, "04:30 PM", "Dry cough and ear pain", "ROUTINE", "CONFIRMED", datetime.now().isoformat())
        ]
        cursor.executemany("""
            INSERT INTO appointments (token_number, patient_name, phone, doctor_name, department, date, slot_time, chief_complaint, urgency_level, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_appointments)
        conn.commit()

    # Seed sample call logs
    cursor.execute("SELECT COUNT(*) FROM call_logs")
    if cursor.fetchone()[0] == 0:
        sample_calls = [
            ("call_bln_9812", "+919845012345", 84, "Hinglish", "URGENT", "Patient reported 103F fever for 3 days. Booked slot with Dr. Rajesh Sharma.", "Patient: Hello, doctor se milna hai... Agent: नमस्ते, संजीवनी क्लिनिक...", "https://assets.bolna.ai/sample_call_1.mp3", datetime.now().isoformat()),
            ("call_bln_9813", "+919876543210", 35, "Hindi", "EMERGENCY", "Caller reported father with sudden left-sided chest pain and sweating. Agent triaged as RED EMERGENCY and advised immediate 108 ambulance dispatch.", "Patient: Pitaji ki chhati me bahut dard ho raha hai... Agent: यह इमरजेंसी है! तुरंत 108 पर कॉल करें...", "https://assets.bolna.ai/sample_call_2.mp3", datetime.now().isoformat()),
        ]
        cursor.executemany("""
            INSERT INTO call_logs (call_id, caller_phone, duration_seconds, language_detected, triage_rating, summary, full_transcript, audio_url, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_calls)
        conn.commit()

    conn.close()
    print("[SEED] Database initialized with realistic clinic records.")

if __name__ == "__main__":
    seed_all()
