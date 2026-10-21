# AarogyaVoice (आरोग्यVoice) — Pitch Deck (7 Slides)
*Target Audience: YC Partner Grey Baker & Bolna Symphony Judges*

---

### Slide 1: Cover & Hook
* **Title:** AarogyaVoice (आरोग्यVoice)
* **Tagline:** Autonomous Multilingual Clinical Triage & Clinic Receptionist Agent
* **Subtitle:** Bringing 24/7 vernacular voice access to 800M+ Indians who cannot use smartphone apps.
* **Team:** Lav Yadav ([github.com/lavyadav182](https://github.com/lavyadav182))
* **Event:** Symphony Buildathon by Bolna (YC F25)

---

### Slide 2: The Critical Problem
* **60%+ of phone calls** to Tier-2/3 clinics and Primary Health Centers go unanswered during rush hours.
* **The Literacy & Digital Divide:** 800M+ citizens in India do not use English-language apps like Practo or Apollo 24/7. When sick or panicking, they pick up the phone and call.
* **Emergency Blindness:** Overwhelmed receptionists cannot differentiate between a life-threatening heart attack and a common viral cold until it is too late.

---

### Slide 3: The Solution — AarogyaVoice
* An **autonomous clinical voice receptionist** powered by Bolna Voice AI.
* **Zero App, Zero Internet for the Patient:** Works over any regular phone call (landline, feature phone, or smartphone).
* **Code-Switching Vernacular Understanding:** Seamlessly speaks Hindi, Hinglish, and English with sub-500ms voice response time.
* **Autonomous Clinical Triage:** Evaluates symptom urgency in real-time. Instantly intercepts emergencies to dispatch 108 ambulances, while booking routine patients into live doctor slots.

---

### Slide 4: Real-Time Architecture & Workflow
```
[Patient Calls Phone] 
       ↓ 
[Plivo / Exotel Telephony] 
       ↓ 
[Bolna Voice AI Orchestrator] 
  ├── STT: Sarvam Saarika / Deepgram Nova-2 (Vernacular Speech)
  ├── LLM: GPT-4o-mini / Gemini Flash (Clinical Protocol & Tool Calling)
  └── TTS: Cartesia Sonic / Sarvam Bulbul (Natural Indian Voice)
       ↓ (Dynamic Webhook Execution)
[FastAPI Clinical Engine] 
  ├── Live Slot Check & Calendar Reservation
  ├── Evidence-Based Emergency Triage Algorithm
  └── Instant WhatsApp Confirmation Token & Clinic Map Dispatch
```

---

### Slide 5: Live Demo Highlights
* **Demo 1 (Emergency):** Caller reports severe left chest pain and sweating -> Agent immediately triggers RED triage, halts routine booking, instructs them to dial 108, and alerts the casualty ward.
* **Demo 2 (Vernacular OPD Booking):** Mother calls in Hinglish for her child's fever -> Agent routes to Pediatrician, checks open slots, books 11:00 AM, and dispatches Token #106 via WhatsApp.
* **Staff Dashboard:** Clinic reception sees incoming callers, live transcripts, audio recordings, and confirmed token queues in real-time.

---

### Slide 6: Business Model & Market Size (TAM)
* **Target Customers:** 200,000+ private clinics, polyclinics, nursing homes, and diagnostic chains across India.
* **Pricing Model:** B2B SaaS subscription:
  * ₹2,999/month ($35/mo) per clinic for up to 1,000 calls.
  * ₹4,999/month ($60/mo) for multi-doctor clinics with custom WhatsApp integration.
* **Market Opportunity:** $1.4B addressable market in India and Southeast Asia for automated healthcare front desks.

---

### Slide 7: Why We Win & What's Next
* **High Defensibility:** Proprietary clinical triage prompting combined with localized vernacular code-switching.
* **Production Ready:** Built on Bolna's open orchestration framework with modular STT/LLM/TTS pluggability.
* **Vision:** Expand AarogyaVoice to government Primary Health Centers (PHCs) and rural telemedicine kiosks.
