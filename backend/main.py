"""
AarogyaVoice Main Application
FastAPI Server powering Voice AI orchestration, clinical triage,
appointment management, and real-time dashboard.
"""

import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

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
    version="1.0.0"
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
# Interactive Voice Dialogue Simulator Endpoint (Zero-Latency for Judges/Demo)
# ==============================================================================

class SimulatorMessage(BaseModel):
    message: str
    caller_phone: Optional[str] = "+919876543210"
    patient_name: Optional[str] = "Priya Sharma"

# Session state in memory for simulator turns
sim_sessions = {}

@app.post("/api/simulator/chat")
def simulate_voice_turn(msg: SimulatorMessage):
    """
    Real-time intelligent conversational fallback that emulates Bolna agent execution,
    triggering real database lookups, clinical triage, and slot booking.
    """
    text = msg.message.lower().strip()
    session_id = msg.caller_phone or "default"
    session = sim_sessions.setdefault(session_id, {"step": 0, "department": "General Physician"})

    response_data = {
        "reply": "",
        "action_taken": None,
        "triage_status": None,
        "appointment_booked": None
    }

    # 1. Check for Emergency Triage
    triage_result = evaluate_symptoms(TriageRequest(symptoms=msg.message))
    if triage_result.severity_level == "EMERGENCY":
        response_data["reply"] = (
            "🚨 यह एक गंभीर आपातकालीन स्थिति (Medical Emergency) हो सकती है! "
            "कृपया ओपीडी स्लॉट का इंतजार न करें। तुरंत 108 एम्बुलेंस पर कॉल करें या नजदीकी आपातकालीन वार्ड जाएं। "
            "क्या आप सुरक्षित स्थान पर हैं?"
        )
        response_data["action_taken"] = "EMERGENCY_DISPATCH_TRIGGERED"
        response_data["triage_status"] = "EMERGENCY"
        return response_data

    # 2. Greeting or Opening Inquiries
    if any(k in text for k in ["hello", "namaste", "hi", "helo", "pranam"]):
        response_data["reply"] = (
            "नमस्ते! संजीवनी हेल्थ क्लिनिक में आपका स्वागत है। मैं प्रिया बोल रही हूँ। "
            "आपको या आपके परिवार में किसको क्या समस्या है? कृपया बताइए।"
        )
        return response_data

    # 3. Clinic Timing / Location Inquiries
    if any(k in text for k in ["timing", "time", "kab khula", "address", "kahan", "fees", "fee", "pata"]):
        if any(k in text for k in ["address", "kahan", "pata"]):
            response_data["reply"] = "क्लिनिक 100 Feet Road, Indiranagar, Bengaluru में स्थित है। मेट्रो स्टेशन के बिलकुल पास है।"
        elif any(k in text for k in ["fees", "fee"]):
            response_data["reply"] = "जनरल ओपीडी परामर्श शुल्क ₹300 है, और स्पेशलिस्ट डॉक्टरों के लिए ₹400 है।"
        else:
            response_data["reply"] = "हमारा क्लिनिक सोमवार से शनिवार सुबह 8:30 से रात 8:00 बजे तक खुला रहता है।"
        return response_data

    # 4. Triage & Symptom Evaluation
    if any(k in text for k in ["bukhar", "fever", "dard", "pain", "chot", "cough", "cold", "doctor"]):
        dept = triage_result.recommended_department
        session["department"] = dept
        response_data["triage_status"] = triage_result.severity_level

        # Check real-time slots
        avail = check_availability(AvailabilityRequest(department=dept, date="today"))
        slots = avail.get("available_slots", [])
        slots_str = ", ".join(slots[:3]) if slots else "आज कोई स्लॉट उपलब्ध नहीं है"

        response_data["reply"] = (
            f"मैंने आपके लक्षण समझ लिए हैं। हमारे {dept} {avail.get('doctor_name')} आज उपलब्ध हैं। "
            f"उपलब्ध समय हैं: {slots_str}। आप कौन सा समय चुनना चाहेंगे?"
        )
        response_data["action_taken"] = f"CHECKED_SLOTS_{dept.upper()}"
        return response_data

    # 5. Booking Slot Confirmation
    if any(k in text for k in ["am", "pm", "baje", "book", "ha", "yes", "confirm", "10", "11", "4", "5"]):
        dept = session.get("department", "General Physician")
        target_slot = "10:30 AM" if "10" in text else ("11:00 AM" if "11" in text else "04:30 PM")

        booking = book_appointment(BookAppointmentRequest(
            patient_name=msg.patient_name or "मरीज",
            phone=msg.caller_phone or "+919876543210",
            department=dept,
            slot_time=target_slot,
            chief_complaint=msg.message,
            urgency_level=triage_result.severity_level
        ))

        response_data["reply"] = booking["voice_response"]
        response_data["action_taken"] = "APPOINTMENT_BOOKED"
        response_data["appointment_booked"] = {
            "token": booking["token_number"],
            "patient_name": booking["patient_name"],
            "doctor_name": booking["doctor_name"],
            "slot_time": booking["slot_time"]
        }
        return response_data

    # Default fallback
    response_data["reply"] = (
        "जी, मैं सुन रही हूँ। क्या आप डॉक्टर से अपॉइंटमेंट लेना चाहते हैं, या क्लिनिक के समय या स्थान की जानकारी चाहिए?"
    )
    return response_data


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
