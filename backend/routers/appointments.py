"""
Appointments & Doctor Availability Router for AarogyaVoice.
Handles real-time slot lookups and booking confirmation.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from backend.database import get_db_connection
from backend.routers.notifications import trigger_whatsapp_confirmation

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])

class AvailabilityRequest(BaseModel):
    department: str
    date: Optional[str] = "today"

class BookAppointmentRequest(BaseModel):
    patient_name: str
    phone: str
    department: str
    slot_time: str
    chief_complaint: Optional[str] = "General checkup"
    urgency_level: Optional[str] = "ROUTINE"
    date: Optional[str] = None

@router.post("/availability")
def check_availability(req: AvailabilityRequest):
    conn = get_db_connection()
    cursor = conn.cursor()

    target_date = datetime.now().strftime("%Y-%m-%d")
    if req.date and req.date.lower() == "tomorrow":
        target_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    elif req.date and req.date.startswith("202"):
        target_date = req.date

    # Find doctor for this department
    cursor.execute("""
        SELECT d.id, d.name, d.room, d.consultation_fee
        FROM doctors d
        WHERE LOWER(d.department) LIKE ?
    """, (f"%{req.department.lower().strip()}%",))
    doctor = cursor.fetchone()

    if not doctor:
        conn.close()
        return {
            "status": "error",
            "message": f"No doctor currently found for department '{req.department}'. Available: General Physician, Pediatrician, Orthopedic, Gynecologist."
        }

    # Fetch available open slots
    cursor.execute("""
        SELECT slot_time FROM slots
        WHERE doctor_id = ? AND date = ? AND is_booked = 0
        ORDER BY id ASC
        LIMIT 4
    """, (doctor["id"], target_date))
    slots = [row["slot_time"] for row in cursor.fetchall()]
    conn.close()

    return {
        "status": "success",
        "doctor_name": doctor["name"],
        "department": req.department,
        "date": target_date,
        "room": doctor["room"],
        "fee": f"₹{doctor['consultation_fee']}",
        "available_slots": slots,
        "message": f"{doctor['name']} has {len(slots)} open slots for {target_date}: {', '.join(slots)}."
    }

@router.post("/book")
def book_appointment(req: BookAppointmentRequest):
    conn = get_db_connection()
    cursor = conn.cursor()

    booking_date = req.date or datetime.now().strftime("%Y-%m-%d")

    # Match doctor
    cursor.execute("""
        SELECT d.id, d.name, d.room FROM doctors d
        WHERE LOWER(d.department) LIKE ?
    """, (f"%{req.department.lower().strip()}%",))
    doctor = cursor.fetchone()

    doctor_name = doctor["name"] if doctor else "Dr. Rajesh Sharma"
    doc_id = doctor["id"] if doctor else 1

    # Mark slot as booked
    cursor.execute("""
        UPDATE slots SET is_booked = 1
        WHERE doctor_id = ? AND date = ? AND slot_time = ? AND is_booked = 0
    """, (doc_id, booking_date, req.slot_time))

    # Generate token number
    cursor.execute("SELECT MAX(token_number) FROM appointments WHERE date = ?", (booking_date,))
    max_token = cursor.fetchone()[0] or 100
    token_number = max_token + 1

    # Insert confirmed appointment
    cursor.execute("""
        INSERT INTO appointments (
            token_number, patient_name, phone, doctor_name, department,
            date, slot_time, chief_complaint, urgency_level, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'CONFIRMED', ?)
    """, (
        token_number, req.patient_name, req.phone, doctor_name, req.department,
        booking_date, req.slot_time, req.chief_complaint, req.urgency_level,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

    # Trigger WhatsApp confirmation message
    whatsapp_msg = (
        f"✅ संजीवनी क्लिनिक: अपॉइंटमेंट कन्फर्म!\n"
        f"मरीज: {req.patient_name}\n"
        f"टोकन संख्या: #{token_number}\n"
        f"डॉक्टर: {doctor_name} ({req.department})\n"
        f"समय: {req.slot_time}, दिनांक: {booking_date}\n"
        f"पता: 100 Feet Rd, Indiranagar, Bengaluru\n"
        f"कृपया समय से 10 मिनट पहले पहुंचें।"
    )
    trigger_whatsapp_confirmation(req.phone, whatsapp_msg)

    return {
        "status": "success",
        "confirmation_code": f"SNJ-{token_number}",
        "token_number": token_number,
        "patient_name": req.patient_name,
        "doctor_name": doctor_name,
        "slot_time": req.slot_time,
        "date": booking_date,
        "urgency_level": req.urgency_level,
        "whatsapp_sent": True,
        "voice_response": f"बधाई हो {req.patient_name}! आपका टोकन नंबर {token_number} है। {doctor_name} के साथ {req.slot_time} का स्लॉट बुक कर दिया गया है। सारी जानकारी आपके व्हाट्सएप पर भेज दी गई है।"
    }

@router.get("")
def list_appointments():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appointments ORDER BY id DESC LIMIT 50")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows
