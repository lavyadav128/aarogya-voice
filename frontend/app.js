/**
 * AarogyaVoice Frontend Client Application
 * Connects to FastAPI backend, manages live appointments, call logs,
 * and handles interactive two-way voice talk with Web Speech STT and TTS.
 */

let ttsEnabled = true;
let isRecording = false;
let recognition = null;
let currentSessionPhone = "+919876543210";

document.addEventListener("DOMContentLoaded", () => {
  fetchAppointments();
  fetchCallLogs();

  // Periodic polling for appointments & call logs
  setInterval(() => {
    fetchAppointments();
    fetchCallLogs();
  }, 4000);

  // Initialize Speech Recognition (Microphone Voice Input)
  initSpeechRecognition();

  // Text Chat Form Submission
  const form = document.getElementById("chat-form");
  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const input = document.getElementById("chat-input");
      const message = input.value.trim();
      if (!message) return;
      input.value = "";
      sendChatMessage(message);
    });
  }

  // TTS Voice Output Toggle
  const ttsBtn = document.getElementById("tts-toggle");
  if (ttsBtn) {
    ttsBtn.addEventListener("click", () => {
      ttsEnabled = !ttsEnabled;
      document.getElementById("tts-label").innerText = `Voice: ${ttsEnabled ? "ON" : "OFF"}`;
      document.getElementById("tts-icon").className = ttsEnabled 
        ? "fa-solid fa-volume-high text-emerald-400" 
        : "fa-solid fa-volume-xmark text-slate-500";
      if (!ttsEnabled && window.speechSynthesis) {
        window.speechSynthesis.cancel();
        hideWaveform();
      }
    });
  }
});

// ==============================================================================
// Web Speech Recognition (Microphone Voice Talk)
// ==============================================================================

function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    console.warn("Web Speech Recognition API is not supported in this browser.");
    const micBtn = document.getElementById("voice-talk-btn");
    if (micBtn) {
      micBtn.title = "Speech Recognition not supported in this browser (use Chrome or Edge).";
    }
    return;
  }

  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = true;

  const langSelect = document.getElementById("voice-lang");
  recognition.lang = langSelect ? langSelect.value : "en-US";

  recognition.onstart = () => {
    isRecording = true;
    updateMicButtonUI(true);
    showListeningIndicator();
  };

  recognition.onresult = (event) => {
    let transcript = "";
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      transcript += event.results[i][0].transcript;
    }
    const input = document.getElementById("chat-input");
    if (input) input.value = transcript;

    // If final result obtained
    if (event.results[event.results.length - 1].isFinal) {
      recognition.stop();
      if (transcript.trim().length > 0) {
        sendChatMessage(transcript.trim());
        if (input) input.value = "";
      }
    }
  };

  recognition.onerror = (event) => {
    console.error("Speech recognition error:", event.error);
    isRecording = false;
    updateMicButtonUI(false);
    hideListeningIndicator();
  };

  recognition.onend = () => {
    isRecording = false;
    updateMicButtonUI(false);
    hideListeningIndicator();
  };
}

function toggleVoiceRecording() {
  if (!recognition) {
    initSpeechRecognition();
    if (!recognition) {
      alert("Microphone voice recognition is supported on Google Chrome, Microsoft Edge, and Safari. Please use a supported browser.");
      return;
    }
  }

  if (isRecording) {
    recognition.stop();
    isRecording = false;
    updateMicButtonUI(false);
    hideListeningIndicator();
  } else {
    // Stop any ongoing speech before listening
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
      hideWaveform();
    }
    const langSelect = document.getElementById("voice-lang");
    if (langSelect) {
      recognition.lang = langSelect.value;
    }
    try {
      recognition.start();
    } catch (e) {
      console.warn("Recognition already started:", e);
    }
  }
}

function updateMicButtonUI(active) {
  const btn = document.getElementById("voice-talk-btn");
  const icon = document.getElementById("mic-btn-icon");
  const text = document.getElementById("mic-btn-text");
  const headerBtn = document.getElementById("header-call-btn");
  const headerIcon = document.getElementById("header-call-icon");
  const headerText = document.getElementById("header-call-text");

  if (active) {
    if (btn) {
      btn.className = "w-full py-3 px-4 rounded-xl font-bold text-sm flex items-center justify-center gap-2.5 transition bg-red-600 hover:bg-red-700 text-white shadow-lg shadow-red-600/30 animate-pulse cursor-pointer";
    }
    if (icon) icon.className = "fa-solid fa-microphone-lines text-base animate-bounce";
    if (text) text.innerText = "Listening to you... Click to Stop";

    if (headerBtn) headerBtn.className = "px-3.5 py-1.5 rounded-xl bg-red-600 text-white text-xs font-bold flex items-center gap-2 transition animate-pulse";
    if (headerIcon) headerIcon.className = "fa-solid fa-phone-slash";
    if (headerText) headerText.innerText = "End Call";
  } else {
    if (btn) {
      btn.className = "w-full py-3 px-4 rounded-xl font-bold text-sm flex items-center justify-center gap-2.5 transition bg-emerald-500 hover:bg-emerald-600 text-slate-950 shadow-lg shadow-emerald-500/20 cursor-pointer";
    }
    if (icon) icon.className = "fa-solid fa-microphone text-base";
    if (text) text.innerText = "Click to Talk (Microphone)";

    if (headerBtn) headerBtn.className = "px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:brightness-110 text-slate-950 text-xs font-bold flex items-center gap-2 transition shadow-md shadow-emerald-500/20";
    if (headerIcon) headerIcon.className = "fa-solid fa-phone";
    if (headerText) headerText.innerText = "Start Voice Talk";
  }
}

function showListeningIndicator() {
  const el = document.getElementById("listening-indicator");
  if (el) el.classList.remove("hidden");
}

function hideListeningIndicator() {
  const el = document.getElementById("listening-indicator");
  if (el) el.classList.add("hidden");
}

// ==============================================================================
// Chat & Communication Engine
// ==============================================================================

function sendQuickPrompt(promptText) {
  sendChatMessage(promptText);
}

async function sendChatMessage(message) {
  appendUserMessage(message);

  try {
    const res = await fetch("/api/simulator/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message,
        caller_phone: currentSessionPhone,
        preferred_language: document.getElementById("voice-lang")?.value.startsWith("hi") ? "hi" : "en"
      })
    });

    if (res.ok) {
      const data = await res.json();
      appendAgentMessage(data);

      if (ttsEnabled && data.reply) {
        speakResponse(data.reply, data.language || "en");
      }

      // Refresh appointments and logs immediately if action occurred
      if (data.action_taken) {
        setTimeout(fetchAppointments, 400);
        setTimeout(fetchCallLogs, 400);
      }
    } else {
      appendSystemMessage("Error reaching agent server. Please make sure the backend is running.");
    }
  } catch (err) {
    appendSystemMessage("Connection error: " + err.message);
  }
}

function resetConversation() {
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel();
    hideWaveform();
  }
  if (isRecording && recognition) {
    recognition.stop();
  }

  fetch("/api/simulator/reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: "reset", caller_phone: currentSessionPhone })
  });

  const box = document.getElementById("chat-box");
  if (box) {
    box.innerHTML = `
      <div class="flex items-start gap-2.5 text-xs text-slate-400">
        <div class="h-6 w-6 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
          <i class="fa-solid fa-user-doctor text-xs"></i>
        </div>
        <div class="bg-slate-900 border border-slate-800 p-3 rounded-2xl rounded-tl-none text-slate-200 space-y-1">
          <p class="font-medium text-white">Hello! Welcome to Sanjeevani Community Health Center. I am Dr. Priya.</p>
          <p class="text-xs text-slate-400">How can I assist you or your family with your health, symptoms, or doctor appointments today?</p>
          <p class="text-[11px] text-slate-500 italic mt-1">(नमस्ते! आप हिंदी या English किसी में भी बात कर सकते हैं।)</p>
        </div>
      </div>
    `;
  }
}

function appendUserMessage(text) {
  const box = document.getElementById("chat-box");
  const div = document.createElement("div");
  div.className = "flex items-start justify-end gap-2.5 text-xs text-slate-300";
  div.innerHTML = `
    <div class="bg-emerald-600/25 border border-emerald-500/40 p-3 rounded-2xl rounded-tr-none text-emerald-100 max-w-[85%]">
      <p class="font-medium">${escapeHtml(text)}</p>
    </div>
    <div class="h-6 w-6 rounded-full bg-emerald-600 text-slate-950 flex items-center justify-center shrink-0 font-bold">
      <i class="fa-solid fa-user text-xs"></i>
    </div>
  `;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function appendAgentMessage(data) {
  const box = document.getElementById("chat-box");
  const div = document.createElement("div");
  div.className = "flex items-start gap-2.5 text-xs text-slate-300";

  let badgeHtml = "";
  if (data.triage_status === "EMERGENCY") {
    badgeHtml = `<span class="inline-block mt-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-red-500/20 border border-red-500/40 text-red-300 animate-pulse">🚨 RED EMERGENCY</span>`;
  } else if (data.triage_status === "URGENT") {
    badgeHtml = `<span class="inline-block mt-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 border border-amber-500/40 text-amber-300">🟡 URGENT CARE</span>`;
  }

  let actionHtml = "";
  if (data.appointment_booked) {
    const app = data.appointment_booked;
    actionHtml = `
      <div class="mt-2 p-2.5 bg-slate-950/90 border border-emerald-500/40 rounded-xl text-[11px] text-emerald-300 space-y-0.5">
        <div class="font-bold text-xs text-emerald-400">🎟️ Token #${app.token_number} Confirmed</div>
        <div>${escapeHtml(app.doctor_name)} • ${escapeHtml(app.slot_time)}</div>
        <div class="text-[10px] text-slate-400 flex items-center gap-1 mt-1">
          <i class="fa-brands fa-whatsapp text-emerald-400"></i> WhatsApp slip & directions dispatched
        </div>
      </div>
    `;
  }

  div.innerHTML = `
    <div class="h-6 w-6 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
      <i class="fa-solid fa-user-doctor text-xs"></i>
    </div>
    <div class="bg-slate-900 border border-slate-800 p-3 rounded-2xl rounded-tl-none text-slate-200 space-y-1.5 max-w-[85%]">
      <p class="leading-relaxed">${escapeHtml(data.reply)}</p>
      ${badgeHtml}
      ${actionHtml}
    </div>
  `;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function appendSystemMessage(text) {
  const box = document.getElementById("chat-box");
  const div = document.createElement("div");
  div.className = "text-center text-[11px] text-red-400 py-1";
  div.innerText = text;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

// ==============================================================================
// Voice Synthesis (TTS Voice Output)
// ==============================================================================

function speakResponse(text, lang) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();

  showWaveform();

  // Strip emojis for clean vocalization
  const cleanText = text.replace(/[🚨🔴🟡🟢✅🎟️]/g, "").trim();
  const utterance = new SpeechSynthesisUtterance(cleanText);

  const voices = window.speechSynthesis.getVoices();
  let selectedVoice = null;

  if (lang === "hi") {
    selectedVoice = voices.find(v => v.lang.includes("hi") || v.name.includes("Hindi") || v.name.includes("Kalpana"));
    utterance.lang = "hi-IN";
  } else {
    // English Indian or British / Natural English
    selectedVoice = voices.find(v => v.lang.includes("en-IN") || v.name.includes("India") || v.name.includes("Neerja") || v.name.includes("Ravi"));
    if (!selectedVoice) {
      selectedVoice = voices.find(v => v.lang.startsWith("en"));
    }
    utterance.lang = "en-IN";
  }

  if (selectedVoice) {
    utterance.voice = selectedVoice;
  }
  utterance.rate = 1.02;

  utterance.onend = () => {
    hideWaveform();
    // Hands-Free Auto-Listen: if caller has Hands-Free mode enabled, start listening automatically!
    const handsFree = document.getElementById("hands-free-toggle")?.checked;
    if (handsFree && recognition && !isRecording) {
      setTimeout(() => {
        toggleVoiceRecording();
      }, 600);
    }
  };

  utterance.onerror = () => hideWaveform();

  window.speechSynthesis.speak(utterance);
}

function showWaveform() {
  const wf = document.getElementById("waveform");
  if (wf) wf.classList.remove("hidden");
}

function hideWaveform() {
  const wf = document.getElementById("waveform");
  if (wf) wf.classList.add("hidden");
}

// ==============================================================================
// Live Data Polling (Appointments & Call Logs)
// ==============================================================================

async function fetchAppointments() {
  try {
    const res = await fetch("/api/appointments");
    if (!res.ok) return;
    const items = await res.json();

    const tbody = document.getElementById("appointments-tbody");
    if (!tbody) return;

    if (items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-slate-500">No appointments scheduled today yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = items.map(item => {
      let badgeClass = "badge-routine";
      if (item.urgency_level === "EMERGENCY") badgeClass = "badge-emergency";
      if (item.urgency_level === "URGENT") badgeClass = "badge-urgent";

      return `
        <tr class="hover:bg-slate-800/40 transition">
          <td class="py-2.5 px-3 font-mono font-bold text-emerald-400">#${item.token_number}</td>
          <td class="py-2.5 px-3">
            <div class="font-medium text-white">${escapeHtml(item.patient_name)}</div>
            <div class="text-[10px] text-slate-500">${escapeHtml(item.phone)}</div>
          </td>
          <td class="py-2.5 px-3">
            <div class="text-slate-200">${escapeHtml(item.doctor_name)}</div>
            <div class="text-[10px] text-slate-400">${escapeHtml(item.department)}</div>
          </td>
          <td class="py-2.5 px-3 font-semibold text-slate-200">${escapeHtml(item.slot_time)}</td>
          <td class="py-2.5 px-3">
            <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold ${badgeClass}">
              ${escapeHtml(item.urgency_level)}
            </span>
          </td>
          <td class="py-2.5 px-3">
            <span class="text-emerald-400 text-[11px] font-medium flex items-center gap-1">
              <i class="fa-solid fa-circle-check text-[10px]"></i> ${escapeHtml(item.status)}
            </span>
          </td>
        </tr>
      `;
    }).join("");

    const statBookings = document.getElementById("stat-bookings");
    const statWhatsapp = document.getElementById("stat-whatsapp");
    if (statBookings) statBookings.innerText = items.length;
    if (statWhatsapp) statWhatsapp.innerText = items.length;
  } catch (e) {
    console.error("Error fetching appointments:", e);
  }
}

async function fetchCallLogs() {
  try {
    const res = await fetch("/api/call-logs");
    if (!res.ok) return;
    const calls = await res.json();

    const container = document.getElementById("call-logs-container");
    if (!container) return;

    if (calls.length === 0) {
      container.innerHTML = `<p class="text-slate-500 text-xs text-center py-4">No calls logged yet.</p>`;
      return;
    }

    container.innerHTML = calls.slice(0, 5).map(c => {
      let badge = `<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold badge-routine">ROUTINE</span>`;
      if (c.triage_rating === "EMERGENCY") badge = `<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold badge-emergency">EMERGENCY</span>`;
      if (c.triage_rating === "URGENT") badge = `<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold badge-urgent">URGENT</span>`;

      return `
        <div class="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition">
          <div class="flex items-center justify-between text-xs mb-1.5">
            <div class="flex items-center gap-2">
              <span class="font-mono text-slate-300 font-semibold">${escapeHtml(c.caller_phone)}</span>
              <span class="text-[10px] text-slate-500">• ${c.duration_seconds}s</span>
              <span class="text-[10px] text-emerald-400/90 bg-emerald-500/10 px-1.5 py-0.5 rounded">${escapeHtml(c.language_detected)}</span>
            </div>
            ${badge}
          </div>
          <p class="text-xs text-slate-300">${escapeHtml(c.summary)}</p>
        </div>
      `;
    }).join("");

    const statCalls = document.getElementById("stat-calls");
    if (statCalls) statCalls.innerText = 140 + calls.length;
  } catch (e) {
    console.error("Error fetching call logs:", e);
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
