"""
Webhooks Router for Bolna Voice AI integration.
Receives post-call summaries, transcripts, audio recordings, and analytics.
"""

from fastapi import APIRouter, Request
from datetime import datetime
from backend.database import get_db_connection

router = APIRouter(prefix="/api", tags=["Bolna Webhooks"])

@router.post("/webhooks/call-ended")
async def handle_call_ended(request: Request):
    """
    Receives post-call data from Bolna when a voice conversation concludes.
    Extracts audio recording URL, bilingual transcript, and call duration.
    """
    try:
        data = await request.json()
    except Exception:
        data = {}

    call_id = data.get("call_id") or data.get("id") or f"call_{int(datetime.now().timestamp())}"
    caller_phone = data.get("caller_phone") or data.get("recipient_phone_number") or "+91-Incoming"
    duration = data.get("duration") or data.get("duration_seconds") or 45
    transcript = data.get("transcript") or data.get("conversation_history") or "Voice call completed."
    summary = data.get("summary") or "Patient called regarding clinic inquiry and slot reservation."
    audio_url = data.get("audio_url") or data.get("recording_url") or "https://assets.bolna.ai/sample_call.mp3"

    # Assess triage from transcript
    triage_rating = "ROUTINE"
    trans_lower = str(transcript).lower()
    if any(k in trans_lower for k in ["chest pain", "heart", "chhati", "108", "emergency"]):
        triage_rating = "EMERGENCY"
    elif any(k in trans_lower for k in ["fever", "bukhar", "pain", "dard", "vomit"]):
        triage_rating = "URGENT"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO call_logs (
            call_id, caller_phone, duration_seconds, language_detected,
            triage_rating, summary, full_transcript, audio_url, timestamp
        ) VALUES (?, ?, ?, 'Hindi/Hinglish', ?, ?, ?, ?, ?)
    """, (
        call_id, caller_phone, duration, triage_rating, summary,
        str(transcript), audio_url, datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

    print(f"[BOLNA WEBHOOK] Processed call {call_id} from {caller_phone}. Triage: {triage_rating}")
    return {"status": "received", "call_id": call_id}

@router.get("/call-logs")
def get_call_logs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM call_logs ORDER BY id DESC LIMIT 50")
    calls = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return calls

@router.get("/clinic/info")
def get_clinic_info(topic: str = "general"):
    info_map = {
        "timing": "Sanjeevani Clinic is open Monday to Saturday from 08:30 AM to 08:00 PM. Sunday emergency casualty open 24/7.",
        "address": "100 Feet Road, HAL 2nd Stage, Indiranagar, Bengaluru, Karnataka 560038. Nearest Metro: Indiranagar Metro Station.",
        "fees": "General OPD consultation fee is ₹300. Pediatric and Specialist consultations are ₹400-₹450.",
        "facilities": "Digital X-Ray, Blood & Pathology Lab, Minor OT, Pharmacy, and 24/7 Oxygen & Ambulance Triage."
    }
    return {
        "status": "success",
        "topic": topic,
        "details": info_map.get(topic.lower(), "Sanjeevani Community Health Clinic provides comprehensive primary care and emergency triage.")
    }
