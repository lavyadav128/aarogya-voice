"""
Database & State Store for AarogyaVoice
Provides high-performance, thread-safe in-memory and SQLite-backed storage for
Doctors, Appointments, Live Calls, Triage Assessments, and Notifications.
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Any

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aarogya.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Doctors Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        qualification TEXT NOT NULL,
        room TEXT NOT NULL,
        consultation_fee INTEGER NOT NULL
    )
    """)

    # Available Slots Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        slot_time TEXT NOT NULL,
        is_booked INTEGER DEFAULT 0,
        FOREIGN KEY(doctor_id) REFERENCES doctors(id)
    )
    """)

    # Confirmed Appointments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token_number INTEGER NOT NULL,
        patient_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        doctor_name TEXT NOT NULL,
        department TEXT NOT NULL,
        date TEXT NOT NULL,
        slot_time TEXT NOT NULL,
        chief_complaint TEXT,
        urgency_level TEXT DEFAULT 'ROUTINE',
        status TEXT DEFAULT 'CONFIRMED',
        created_at TEXT NOT NULL
    )
    """)

    # Call Records & Transcripts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS call_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        call_id TEXT NOT NULL,
        caller_phone TEXT NOT NULL,
        duration_seconds INTEGER DEFAULT 0,
        language_detected TEXT DEFAULT 'Hindi/Hinglish',
        triage_rating TEXT DEFAULT 'ROUTINE',
        summary TEXT,
        full_transcript TEXT,
        audio_url TEXT,
        timestamp TEXT NOT NULL
    )
    """)

    # WhatsApp / SMS Outbox Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient_phone TEXT NOT NULL,
        channel TEXT DEFAULT 'WhatsApp',
        message_body TEXT NOT NULL,
        status TEXT DEFAULT 'SENT',
        sent_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

# Initialize tables immediately
init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
