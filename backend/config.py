import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    CLINIC_NAME: str = os.getenv("CLINIC_NAME", "Sanjeevani Community Health Center")
    CLINIC_LOCATION: str = os.getenv("CLINIC_LOCATION", "Indiranagar, Bengaluru, Karnataka")
    CLINIC_PHONE: str = os.getenv("CLINIC_PHONE", "+91 80 2520 4400")
    EMERGENCY_AMBULANCE_NUMBER: str = os.getenv("EMERGENCY_AMBULANCE_NUMBER", "108")
    
    BOLNA_API_KEY: str = os.getenv("BOLNA_API_KEY", "")
    BOLNA_AGENT_ID: str = os.getenv("BOLNA_AGENT_ID", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    BACKEND_PUBLIC_URL: str = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8000")

settings = Settings()
