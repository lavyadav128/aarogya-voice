"""
Clinical Triage Router for AarogyaVoice.
Implements evidence-based algorithmic symptom assessment for triage prioritization.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/triage", tags=["Clinical Triage"])

class TriageRequest(BaseModel):
    symptoms: str
    duration_days: Optional[int] = 1
    patient_age: Optional[int] = 30

class TriageResponse(BaseModel):
    severity_level: str  # EMERGENCY, URGENT, ROUTINE
    severity_color: str  # RED, YELLOW, GREEN
    urgency_score: int   # 1 to 10
    recommended_department: str
    action_instructions: str
    action_instructions_hi: str
    dispatch_ambulance: bool

EMERGENCY_KEYWORDS = [
    # English
    "chest pain", "heart attack", "heart", "cardiac", "breathless", "shortness of breath",
    "suffocation", "unconscious", "fainted", "fainting", "stroke", "paralysis",
    "heavy bleeding", "bleeding heavily", "blood vomiting", "poison", "head injury",
    "severe sweating", "cold sweat",
    # Romanized Hindi / Hinglish
    "chhati me dard", "sine me dard", "dil ka daura", "saans lene me dikkat", "saans phool",
    "behosh", "khun ki ulti", "zehar", "chakkar aake gir", "chhati",
    # Devanagari Hindi
    "छाती में दर्द", "सीने में दर्द", "छाती", "सीना", "सीने", "दिल", "दौरा", "हार्ट अटैक",
    "पसीना", "सांस", "साँस", "बेहोश", "बेहोशी", "खून", "रक्त", "लकवा", "जहर"
]

URGENT_KEYWORDS = [
    # English
    "high fever", "102", "103", "104", "persistent vomiting", "vomiting continuously",
    "severe abdominal pain", "severe stomach pain", "fracture", "broken bone",
    "child dehydration", "baby lethargic",
    # Romanized Hindi / Hinglish
    "tez bukhar", "ultiyan", "pet me bahut dard", "haddi toot", "baccha ro raha hai",
    # Devanagari Hindi
    "तेज बुखार", "बुखार", "उल्टी", "पेट में तेज दर्द", "हड्डी", "फ्रैक्चर", "बच्चे को बुखार"
]

@router.post("/evaluate", response_model=TriageResponse)
def evaluate_symptoms(req: TriageRequest):
    text = req.symptoms.lower()

    # 1. EMERGENCY (RED FLAG)
    for kw in EMERGENCY_KEYWORDS:
        if kw in text:
            return TriageResponse(
                severity_level="EMERGENCY",
                severity_color="RED",
                urgency_score=10,
                recommended_department="Emergency Casualty / Trauma Center",
                action_instructions="CRITICAL: Do not wait for an OPD slot. Call 108 Ambulance immediately or rush to the nearest emergency ward.",
                action_instructions_hi="आपातकालीन स्थिति: ओपीडी स्लॉट का इंतजार न करें। तुरंत 108 एम्बुलेंस बुलाएं या नजदीकी इमरजेंसी वार्ड जाएं।",
                dispatch_ambulance=True
            )

    # 2. URGENT CARE (YELLOW FLAG)
    for kw in URGENT_KEYWORDS:
        if kw in text or (req.duration_days and req.duration_days >= 3 and "fever" in text):
            # Pediatric department check
            dept = "Pediatrician" if req.patient_age and req.patient_age < 14 else "General Physician"
            return TriageResponse(
                severity_level="URGENT",
                severity_color="YELLOW",
                urgency_score=7,
                recommended_department=dept,
                action_instructions="Priority same-day consultation recommended within 2 to 4 hours.",
                action_instructions_hi="आज ही प्राथमिकता के आधार पर 2 से 4 घंटे के भीतर डॉक्टर से परामर्श लें।",
                dispatch_ambulance=False
            )

    # 3. ROUTINE OPD (GREEN FLAG)
    dept = "General Physician"
    if "bone" in text or "joint" in text or "kamar" in text or "ghutna" in text or "fracture" in text:
        dept = "Orthopedic"
    elif "pregnant" in text or "mahila" in text or "period" in text or "gyno" in text:
        dept = "Gynecologist"
    elif req.patient_age and req.patient_age < 14:
        dept = "Pediatrician"

    return TriageResponse(
        severity_level="ROUTINE",
        severity_color="GREEN",
        urgency_score=3,
        recommended_department=dept,
        action_instructions="Routine outpatient booking. Standard clinic visit scheduled.",
        action_instructions_hi="सामान्य ओपीडी परामर्श। सामान्य समय पर डॉक्टर से मिल सकते हैं।",
        dispatch_ambulance=False
    )
