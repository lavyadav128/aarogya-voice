/**
 * AarogyaVoice Frontend Client Application
 * Connects to FastAPI backend, manages live appointments, call logs,
 * and handles interactive voice simulation with browser Web Speech.
 */

let ttsEnabled = true;

document.addEventListener("DOMContentLoaded", () => {
  fetchAppointments();
  fetchCallLogs();

  // Set up periodic polling for live updates
  setInterval(() => {
    fetchAppointments();
    fetchCallLogs();
  }, 4000);

  // Chat Form Submission
  const form = document.getElementById("chat-form");
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const input = document.getElementById("chat-input");
    const message = input.value.trim();
    if (!message) return;
    input.value = "";
    sendChatMessage(message);
  });

  // TTS Toggle Button
  const ttsBtn = document.getElementById("tts-toggle");
  ttsBtn.addEventListener("click", () => {
    ttsEnabled = !ttsEnabled;
    document.getElementById("tts-label").innerText = `Voice Audio: ${ttsEnabled ? "ON" : "OFF"}`;
    document.getElementById("tts-icon").className = ttsEnabled ? "fa-solid fa-volume-high text-emerald-400" : "fa-solid fa-volume-xmark text-slate-500";
    if (!ttsEnabled && window.speechSynthesis) {
      window.speechSynthesis.cancel();
      hideWaveform();
    }
  });
});

function sendQuickPrompt(promptText) {
  sendChatMessage(promptText);
}

async function sendChatMessage(message) {
  appendUserMessage(message);

  try {
    const res = await fetch("/api/simulator/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: message })
    });

    if (res.ok) {
      const data = await res.json();
      appendAgentMessage(data);

      if (ttsEnabled && data.reply) {
        speakResponse(data.reply);
      }

      // Refresh appointments and logs immediately if action occurred
      if (data.action_taken) {
        setTimeout(fetchAppointments, 500);
        setTimeout(fetchCallLogs, 500);
      }
    } else {
      appendSystemMessage("Error reaching agent server. Please make sure the backend is running.");
    }
  } catch (err) {
    appendSystemMessage("Connection error: " + err.message);
  }
}

function appendUserMessage(text) {
  const box = document.getElementById("chat-box");
  const div = document.createElement("div");
  div.className = "flex items-start justify-end gap-2.5 text-xs text-slate-300";
  div.innerHTML = `
    <div class="bg-emerald-600/20 border border-emerald-500/30 p-3 rounded-2xl rounded-tr-none text-emerald-200">
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
    badgeHtml = `<span class="inline-block mt-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-red-500/20 border border-red-500/40 text-red-300">🚨 RED EMERGENCY</span>`;
  } else if (data.triage_status === "URGENT") {
    badgeHtml = `<span class="inline-block mt-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 border border-amber-500/40 text-amber-300">🟡 URGENT CARE</span>`;
  }

  let actionHtml = "";
  if (data.appointment_booked) {
    actionHtml = `
      <div class="mt-2 p-2 bg-slate-950/80 border border-emerald-500/30 rounded-xl text-[11px] text-emerald-300">
        <div><b>Token #${data.appointment_booked.token} Confirmed!</b></div>
        <div>${escapeHtml(data.appointment_booked.doctor_name)} @ ${escapeHtml(data.appointment_booked.slot_time)}</div>
        <div class="text-[10px] text-slate-400 mt-1">📱 WhatsApp slip dispatched</div>
      </div>
    `;
  }

  div.innerHTML = `
    <div class="h-6 w-6 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
      <i class="fa-solid fa-robot text-xs"></i>
    </div>
    <div class="bg-slate-900 border border-slate-800 p-3 rounded-2xl rounded-tl-none text-slate-200 space-y-1 max-w-[85%]">
      <p>${escapeHtml(data.reply)}</p>
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

function speakResponse(text) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();

  showWaveform();

  const cleanText = text.replace(/[🚨🔴🟡🟢✅]/g, "");
  const utterance = new SpeechSynthesisUtterance(cleanText);

  // Try to find Hindi voice or Indian English
  const voices = window.speechSynthesis.getVoices();
  const preferredVoice = voices.find(v => v.lang.includes("hi") || v.lang.includes("IN") || v.name.includes("India"));
  if (preferredVoice) {
    utterance.voice = preferredVoice;
  }
  utterance.rate = 1.05;

  utterance.onend = () => hideWaveform();
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

    // Update KPI counter
    document.getElementById("stat-bookings").innerText = items.length;
    document.getElementById("stat-whatsapp").innerText = items.length;
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

    document.getElementById("stat-calls").innerText = 140 + calls.length;
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
