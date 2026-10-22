"""
AarogyaVoice Main Application
FastAPI Server powering Voice AI orchestration, clinical triage,
appointment management, and real-time dashboard.
"""

import os
import re
import requests
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict

from backend.config import settings
from backend.seed_data import seed_all
from backend.routers import triage, appointments, notifications, webhooks
from backend.routers.triage import evaluate_symptoms, TriageRequest
from backend.routers.appointments import check_availability, book_appointment, AvailabilityRequest, BookAppointmentRequest

# Initialize database seed data
seed_all()

app = FastAPI(
    title="AarogyaVoice API",
    description="Autonomous Multilingual Clinical Triage & Clinic Receptionist Agent",
    version="2.0.0"
)

# Enable CORS for local testing & web dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(triage.router)
app.include_router(appointments.router)
app.include_router(notifications.router)
app.include_router(webhooks.router)

# Mount Frontend static directory
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def serve_dashboard():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "AarogyaVoice Backend API is running. Dashboard index not found."}


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AarogyaVoice",
        "clinic": settings.CLINIC_NAME,
        "bolna_configured": bool(settings.BOLNA_API_KEY)
    }


# ==============================================================================
# Clinical Doctor & Receptionist Multi-Turn Conversational Engine
# ==============================================================================

class SimulatorMessage(BaseModel):
    message: str
    caller_phone: Optional[str] = "+919876543210"
    patient_name: Optional[str] = "Caller"
    preferred_language: Optional[str] = "en"  # "en" by default

# Persistent multi-turn session state
sim_sessions: Dict[str, Dict] = {}

def get_session(session_id: str) -> Dict:
    if session_id not in sim_sessions:
        sim_sessions[session_id] = {
            "language": "en",  # Default language is English
            "history": [],
            "department": "General Physician",
            "last_triage": "ROUTINE"
        }
    return sim_sessions[session_id]

def is_hindi_text(text: str) -> bool:
    devanagari_count = len(re.findall(r'[\u0900-\u097f]', text))
    return devanagari_count >= 2

def requests_english(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in [
        "in english", "english", "speak english", "talk in english",
        "reply in english", "response me in english", "respond in english",
        "to english", "change to english"
    ])

def requests_hindi(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in [
        "in hindi", "hindi me", "hindi", "speak hindi", "talk in hindi"
    ]) or is_hindi_text(text)


@app.post("/api/simulator/reset")
def reset_session(req: Optional[SimulatorMessage] = None):
    session_id = req.caller_phone if req and req.caller_phone else "default"
    sim_sessions[session_id] = {
        "language": "en",
        "history": [],
        "department": "General Physician",
        "last_triage": "ROUTINE"
    }
    return {"status": "reset", "session_id": session_id}


@app.post("/api/simulator/chat")
def simulate_voice_turn(msg: SimulatorMessage):
    """
    Intelligent doctor-level clinical reasoning and conversational engine.
    Supports English (default), Hindi, and Hinglish with live tool execution.
    """
    session_id = msg.caller_phone or "default"
    session = get_session(session_id)
    text = msg.message.strip()

    # 1. Dynamic Language Detection & Switching
    if requests_english(text):
        session["language"] = "en"
    elif requests_hindi(text):
        session["language"] = "hi"
    elif any(k in text.lower() for k in ["hello", "hi", "hey", "doctor", "appointment", "want", "fees", "timing", "address"]):
        # Default to English for general Latin queries unless Hindi grammar is detected
        if not any(k in text.lower() for k in ["kya", "hai", "mujhe", "chahiye", "karo", "batao", "milna"]):
            session["language"] = "en"

    lang = session["language"]

    # 2. Algorithmic Clinical Triage Check
    triage_res = evaluate_symptoms(TriageRequest(symptoms=text))
    if triage_res.severity_level != "ROUTINE":
        session["last_triage"] = triage_res.severity_level
        session["department"] = triage_res.recommended_department

    # CRITICAL: RED EMERGENCY INTERCEPT (Never delayed!)
    if triage_res.severity_level == "EMERGENCY" or session.get("last_triage") == "EMERGENCY" and any(k in text.lower() for k in ["chest", "pain", "chhati", "heart", "sweat", "dard"]):
        session["history"].append({"role": "user", "content": text})
        if lang == "hi":
            reply = (
                "🚨 यह एक गंभीर मेडिकल इमरजेंसी (हार्ट अटैक या जानलेवा लक्षण) हो सकती है! "
                "कृपया ओपीडी अपॉइंटमेंट का इंतजार बिल्कुल न करें। तुरंत 108 एम्बुलेंस बुलाएं या नजदीकी अस्पताल के इमरजेंसी वार्ड जाएं। "
                "क्या आपके मरीज सुरक्षित स्थिति में हैं?"
            )
        else:
            reply = (
                "🚨 This is a critical medical emergency (possible acute cardiac or life-threatening event)! "
                "Please do NOT wait for a routine outpatient clinic appointment. Call 108 Ambulance immediately or take the patient to the nearest hospital Emergency/ICU ward right now. "
                "Are they in a safe position right now?"
            )
        session["history"].append({"role": "assistant", "content": reply})
        return {
            "reply": reply,
            "triage_status": "EMERGENCY",
            "action_taken": "EMERGENCY_DISPATCH_TRIGGERED",
            "language": lang
        }

    # 3. Real Appointment Booking Execution
    t_lower = text.lower()
    time_matches = re.findall(r'\b(0?[1-9]|1[0-2])(?::([0-5][0-9]))?\s*(am|pm|baje)?\b', t_lower)
    is_booking_intent = any(k in t_lower for k in ["book", "confirm", "yes", "theek hai", "ha", "kar do", "slot"])
    
    if any(k in t_lower for k in ["10:00", "10:30", "11:00", "11:30", "04:00", "04:30", "05:00", "4:30", "10", "11", "5"]) and (is_booking_intent or len(session["history"]) >= 2):
        target_slot = "10:30 AM"
        if "10:00" in t_lower or "10 " in t_lower: target_slot = "10:00 AM"
        elif "11:00" in t_lower or "11 " in t_lower: target_slot = "11:00 AM"
        elif "11:30" in t_lower: target_slot = "11:30 AM"
        elif "04:00" in t_lower or "4 " in t_lower: target_slot = "04:00 PM"
        elif "04:30" in t_lower or "4:30" in t_lower: target_slot = "04:30 PM"
        elif "05:00" in t_lower or "5 " in t_lower: target_slot = "05:00 PM"

        dept = session.get("department", "General Physician")
        booking = book_appointment(BookAppointmentRequest(
            patient_name=msg.patient_name or "Caller",
            phone=msg.caller_phone or "+919876543210",
            department=dept,
            slot_time=target_slot,
            chief_complaint=text,
            urgency_level=session.get("last_triage", "ROUTINE")
        ))

        if lang == "hi":
            reply = f"✅ बधाई हो! आपका टोकन नंबर #{booking['token_number']} सफलतापूर्वक कन्फर्म हो गया है। {booking['doctor_name']} ({dept}) के साथ {target_slot} का समय आरक्षित कर दिया गया है। सारी जानकारी और गूगल मैप्स लिंक आपके व्हाट्सएप पर भेज दिया गया है।"
        else:
            reply = f"✅ Confirmed! Your appointment token is #{booking['token_number']} with {booking['doctor_name']} ({dept}) for {target_slot}. All visit details and clinic directions have been dispatched to your WhatsApp."

        session["history"].append({"role": "user", "content": text})
        session["history"].append({"role": "assistant", "content": reply})
        return {
            "reply": reply,
            "triage_status": session.get("last_triage", "ROUTINE"),
            "action_taken": "APPOINTMENT_BOOKED",
            "appointment_booked": booking,
            "language": lang
        }

    # 4. Inquire Slots / General Appointment Request
    if any(k in t_lower for k in ["appointment", "doctor", "डॉक्टर", "अपॉइंटमेंट", "milna", "booking", "slot"]):
        dept = session.get("department", "General Physician")
        if "emergency" in dept.lower() or "trauma" in dept.lower():
            dept = "General Physician"
            session["department"] = "General Physician"
        avail = check_availability(AvailabilityRequest(department=dept, date="today"))
        doc_name = avail.get("doctor_name") or "Dr. Rajesh Sharma"
        slots_list = avail.get("available_slots", ["10:00 AM", "10:30 AM", "11:00 AM", "04:30 PM"])
        slots_str = ", ".join(slots_list[:3])

        if lang == "hi":
            reply = f"जी हाँ, हमारे {dept} {doc_name} आज उपलब्ध हैं। आज के उपलब्ध स्लॉट हैं: {slots_str}। आप कौन सा समय चुनना चाहेंगे?"
        else:
            reply = f"Certainly! Our {dept} {doc_name} has openings today at: {slots_str}. Which time works best for you?"

        session["history"].append({"role": "user", "content": text})
        session["history"].append({"role": "assistant", "content": reply})
        return {
            "reply": reply,
            "triage_status": session.get("last_triage", "ROUTINE"),
            "action_taken": f"CHECKED_SLOTS_{dept.upper()}",
            "language": lang
        }

    # 5. Call LLM (Groq / Qwen) for Context-Aware Clinical Reasoning
    groq_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
    if groq_key and not groq_key.startswith("your_"):
        system_prompt = f"""You are Dr. Priya, an empathetic, highly trained clinical receptionist and triage coordinator at Sanjeevani Community Health Center in Bengaluru.

CRITICAL RULES:
1. LANGUAGE REQUIREMENT: You MUST speak strictly in {"ENGLISH" if lang == "en" else "HINDI"}.
   - If the user asked for English or wrote in English, respond only in clear, professional English.
   - If the user wrote in Hindi, respond in polite, warm Hindi.
2. MEDICAL DOCTOR PERSONA:
   - Talk like an attentive clinical professional. Never repeat repetitive robotic phrases.
   - If user reports symptoms, acknowledge them with clinical empathy and guide them to the right specialist.
   - Keep answers concise (2 to 3 sentences maximum) for telephone voice conversation.
3. CLINIC DETAILS:
   - Location: 100 Feet Road, Indiranagar, Bengaluru.
   - Timings: Mon-Sat 8:30 AM to 8:00 PM.
   - Fees: General OPD ₹300, Specialist OPD ₹400.
   - Doctors: Dr. Rajesh Sharma (General Physician), Dr. Ananya Rao (Pediatrics), Dr. Vikram Patel (Orthopedics), Dr. Meera Iyer (Gynecology).
"""
        messages = [{"role": "system", "content": system_prompt}] + session["history"][-6:] + [{"role": "user", "content": text}]
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={
                    "model": "qwen/qwen3.8-27b",
                    "messages": messages,
                    "max_tokens": 150,
                    "temperature": 0.2
                },
                timeout=8
            )
            if r.status_code == 200:
                reply = r.json()["choices"][0]["message"]["content"].strip()
                session["history"].append({"role": "user", "content": text})
                session["history"].append({"role": "assistant", "content": reply})
                return {
                    "reply": reply,
                    "triage_status": session.get("last_triage", "ROUTINE"),
                    "action_taken": None,
                    "language": lang
                }
        except Exception:
            pass  # Fall through to deterministic smart clinical fallback

    # 6. High-Reliability Contextual Clinical Fallback
    if lang == "en":
        if any(k in t_lower for k in ["fee", "fees", "cost", "charge"]):
            reply = "Our consultation fee is ₹300 for General OPD and ₹400 for specialists like Pediatrics and Orthopedics."
        elif any(k in t_lower for k in ["timing", "time", "open", "hour"]):
            reply = "Sanjeevani Clinic is open Monday to Saturday from 8:30 AM to 8:00 PM. Casualty triage is available 24/7."
        elif any(k in t_lower for k in ["address", "where", "location"]):
            reply = "We are located at 100 Feet Road, Indiranagar, Bengaluru, right near the Indiranagar Metro Station."
        else:
            reply = "Hello! I am Dr. Priya at Sanjeevani Health Clinic. How can I assist you or your family with a consultation or appointment today?"
    else:
        if any(k in t_lower for k in ["fee", "fees", "kitna", "kharch"]):
            reply = "हमारे क्लिनिक में जनरल ओपीडी परामर्श शुल्क ₹300 है, और स्पेशलिस्ट डॉक्टरों के लिए ₹400 है।"
        elif any(k in t_lower for k in ["timing", "time", "kab", "samay"]):
            reply = "क्लिनिक सोमवार से शनिवार सुबह 8:30 से रात 8:00 बजे तक खुला रहता है।"
        elif any(k in t_lower for k in ["address", "kahan", "pata"]):
            reply = "हमारा क्लिनिक 100 Feet Road, Indiranagar, Bengaluru में स्थित है।"
        else:
            reply = "नमस्ते! मैं संजीवनी क्लिनिक से डॉ. प्रिया बोल रही हूँ। मैं आपकी या आपके परिवार की सेहत में क्या मदद कर सकती हूँ?"

    session["history"].append({"role": "user", "content": text})
    session["history"].append({"role": "assistant", "content": reply})

    return {
        "reply": reply,
        "triage_status": session.get("last_triage", "ROUTINE"),
        "action_taken": None,
        "language": lang
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
