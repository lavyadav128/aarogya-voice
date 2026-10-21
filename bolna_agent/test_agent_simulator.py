#!/usr/bin/env python3
"""
Local Interactive Simulator for AarogyaVoice.
Allows immediate testing of voice conversation turns, clinical triage, and slot booking
even without live telephony or active API keys.
"""

import os
import sys
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("LOCAL_API_URL", "http://localhost:8000")

def simulate_dialogue():
    print("=" * 70)
    print("  AAROGYAVOICE (आरोग्यVoice) - LOCAL CLINICAL VOICE SIMULATOR")
    print("  Sanjeevani Community Health Clinic, Bengaluru")
    print("=" * 70)
    print("Agent: 'नमस्ते! संजीवनी हेल्थ क्लिनिक में आपका स्वागत है। मैं प्रिया हूँ।'")
    print("       'मैं आज आपकी या आपके परिवार की क्या मदद कर सकती हूँ?'")
    print("-" * 70)
    print("Type patient responses in Hindi, Hinglish, or English. Type 'exit' to quit.\n")

    client = httpx.Client(base_url=BASE_URL, timeout=10.0)

    try:
        health = client.get("/health")
        if health.status_code != 200:
            print("[WARNING] Backend is not responding at http://localhost:8000. Start backend first with start.bat!")
    except Exception:
        print("[WARNING] Backend server is not running on http://localhost:8000.")
        print("Please run 'python backend/main.py' or 'start.bat' in another terminal.\n")

    while True:
        try:
            user_input = input("\n[Caller / Patient]: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Ending simulation session.")
                break

            # Query the backend agent simulation endpoint
            response = client.post("/api/simulator/chat", json={"message": user_input})
            if response.status_code == 200:
                data = response.json()
                print(f"\n[AarogyaVoice Agent]: {data.get('reply')}")
                if data.get("action_taken"):
                    print(f"  ⚡ Action Executed: {data.get('action_taken')}")
                if data.get("triage_status"):
                    badge = {"EMERGENCY": "🔴 EMERGENCY (RED)", "URGENT": "🟡 URGENT (YELLOW)", "ROUTINE": "🟢 ROUTINE (GREEN)"}.get(data.get("triage_status"), "ℹ️ ROUTINE")
                    print(f"  🩺 Clinical Triage: {badge}")
                if data.get("appointment_booked"):
                    app = data.get("appointment_booked")
                    print(f"  🎟️ Token #{app.get('token')}: {app.get('patient_name')} -> {app.get('doctor_name')} @ {app.get('slot_time')}")
            else:
                print(f"[Error {response.status_code}]: {response.text}")
        except KeyboardInterrupt:
            print("\nExiting simulator.")
            break
        except Exception as e:
            print(f"[Simulator Connection Error]: {e}")


if __name__ == "__main__":
    simulate_dialogue()
