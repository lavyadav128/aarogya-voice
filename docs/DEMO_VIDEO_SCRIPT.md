# AarogyaVoice — 2-Minute Demo Video Script
*Record this video using Loom or OBS Studio, upload to Google Drive or Luma, and ensure link sharing is set to 'Anyone with the link can view'.*

---

### Total Duration: 2 Minutes (120 Seconds)

#### 0:00 - 0:25: The Problem & Hook (Face + Intro)
* **Speaker:** "Hi everyone! In India, over 60% of inbound phone calls to local clinics and primary health centers go completely unanswered during morning rush hours. Even worse, over 800 million citizens cannot navigate complex English smartphone apps like Practo. When they are sick or in pain, they dial the clinic's phone number. Today, I'm thrilled to present **AarogyaVoice** — an autonomous multilingual clinical receptionist powered by **Bolna Voice AI**."

#### 0:25 - 0:55: Live Demo 1 — Emergency Clinical Triage
* **Visual:** Show the AarogyaVoice Dashboard (`http://localhost:8000`) and the Voice Console.
* **Speaker:** "Let's test an emergency scenario first. A caller dials in panicked."
* **Action:** Click the button: `मेरे पिताजी की छाती में तेज दर्द हो रहा है और पसीना आ रहा है` (or speak it into mic).
* **Agent Priya speaks aloud:** *"यह एक गंभीर आपातकालीन स्थिति हो सकती है! कृपया तुरंत 108 एम्बुलेंस पर कॉल करें या नजदीकी आपातकालीन वार्ड जाएं..."*
* **Visual:** Point to the red glowing `🚨 RED EMERGENCY` badge appearing in the dashboard.
* **Speaker:** "Notice how AarogyaVoice immediately recognizes life-threatening chest pain, halts any routine booking, gives emergency guidance in Hindi, and logs an alert on the casualty desk."

#### 0:55 - 1:35: Live Demo 2 — Vernacular OPD Slot Booking & WhatsApp
* **Speaker:** "Now let's look at a routine clinic booking in Hinglish."
* **Action:** Speak or type: *"मेरे 4 साल के बच्चे को कल से खांसी और बुखार है, डॉक्टर से मिलना है"*
* **Agent Priya speaks aloud:** *"मैंने आपके लक्षण समझ लिए हैं। हमारे Pediatrician Dr. Ananya Rao आज उपलब्ध हैं। उपलब्ध समय हैं: 10:30 AM, 11:00 AM, 04:30 PM। आप कौन सा समय चुनना चाहेंगे?"*
* **Action:** Respond: *"11:00 AM book kar dijiye"*
* **Agent Priya confirms:** *"बधाई हो! आपका टोकन नंबर #106 है। Dr. Ananya Rao के साथ 11:00 AM का स्लॉट बुक कर दिया गया है। सारी जानकारी आपके व्हाट्सएप पर भेज दी गई है।"*
* **Visual:** Show the appointment row immediately populating the live OPD table, and the WhatsApp outbox token.

#### 1:35 - 2:00: Architecture & YC Vision
* **Visual:** Switch briefly to the architecture diagram in the README.
* **Speaker:** "Under the hood, AarogyaVoice is orchestrated through Bolna, using Sarvam AI and Deepgram for vernacular speech recognition, fast LLM tool calling for slot checks, and Cartesia for sub-500ms voice synthesis. This directly empowers understaffed clinics to operate 24/7 without missing a single patient. Thank you Bolna team and Symphony for this opportunity!"
