import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.routers.triage import evaluate_symptoms, TriageRequest
from backend.routers.appointments import check_availability, book_appointment, AvailabilityRequest, BookAppointmentRequest

def test_triage_emergency():
    res = evaluate_symptoms(TriageRequest(symptoms="Chest pain and severe breathlessness"))
    assert res.severity_level == "EMERGENCY"
    assert res.dispatch_ambulance is True
    print("[PASS] Emergency Triage Test Passed!")

def test_triage_routine():
    res = evaluate_symptoms(TriageRequest(symptoms="Mild cold and cough for checkup"))
    assert res.severity_level == "ROUTINE"
    print("[PASS] Routine Triage Test Passed!")

def test_availability_and_booking():
    avail = check_availability(AvailabilityRequest(department="General Physician"))
    assert avail["status"] == "success"
    assert len(avail["available_slots"]) > 0
    slot = avail["available_slots"][0]
    print(f"[PASS] Slot Availability Passed! Open slot: {slot}")

    booking = book_appointment(BookAppointmentRequest(
        patient_name="Ramesh Verma",
        phone="+919876543210",
        department="General Physician",
        slot_time=slot,
        chief_complaint="Routine blood pressure checkup"
    ))
    assert booking["status"] == "success"
    assert booking["token_number"] > 100
    print(f"[PASS] Slot Booking Passed! Token: #{booking['token_number']}")

if __name__ == "__main__":
    test_triage_emergency()
    test_triage_routine()
    test_availability_and_booking()
    print("\nALL LOCAL TESTS PASSED CLEANLY!")
