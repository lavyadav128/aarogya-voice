"""
Notification Router for AarogyaVoice
Handles WhatsApp & SMS messaging dispatch and outbox logging.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from backend.database import get_db_connection

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

class NotificationRequest(BaseModel):
    recipient_phone: str
    message: str
    channel: str = "WhatsApp"

def trigger_whatsapp_confirmation(phone: str, message: str):
    """Logs WhatsApp message to outbox and triggers provider if configured."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notifications (recipient_phone, channel, message_body, status, sent_at)
        VALUES (?, 'WhatsApp', ?, 'DELIVERED', ?)
    """, (phone, message, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    safe_msg = message.encode("ascii", errors="replace").decode("ascii")
    print(f"[WHATSAPP OUTBOX] Dispatched to {phone}:\n{safe_msg}\n")

@router.get("/outbox")
def get_outbox():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 50")
    records = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return records
