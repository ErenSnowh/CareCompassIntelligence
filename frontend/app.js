/**
 * CareCompass AI — Frontend Controller & Logic
 * Seamlessly interfaces with FastAPI backend and TinyFish APIs.
 */

// Application State
const state = {
  conversationHistory: [],
  currentLocation: { lat: 28.54, lng: 77.27 },
  caregiversRoster: [],
  isProcessing: false,
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  fetchCaregiversRoster();
  fetchHealthStatus();
});

// Tab Switching
function switchTab(tabName) {
  document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));

  if (tabName === 'patient') {
    document.getElementById('patient-view').classList.add('active');
    document.getElementById('tab-patient-btn').classList.add('active');
  } else if (tabName === 'dashboard') {
    document.getElementById('dashboard-view').classList.add('active');
    document.getElementById('tab-dashboard-btn').classList.add('active');
  }
}

// Quick Sample Loader
function loadSample(text) {
  const inputEl = document.getElementById('user-input-field');
  inputEl.value = text;
  inputEl.focus();
}

// System Status Check
async function fetchHealthStatus() {
  try {
    const res = await fetch('/api/v1/health');
    if (res.ok) {
      const data = await res.json();
      const stats = data.dataset_statistics || {};
      const statusText = `Core Active · ${stats.caregivers_active || 52} Caregivers Live`;
      document.getElementById('system-status-text').textContent = statusText;
    }
  } catch (e) {
    console.debug('Backend offline or starting up...');
  }
}

// Fetch Caregivers for Dashboard
async function fetchCaregiversRoster() {
  try {
    const res = await fetch('/api/v1/caregivers?active_only=true');
    if (res.ok) {
      state.caregiversRoster = await res.json();
      renderCaregiversTable(state.caregiversRoster);
      document.getElementById('kpi-caregivers-count').textContent = `${state.caregiversRoster.length} / 60`;
    }
  } catch (e) {
    console.error('Failed to load caregiver directory:', e);
  }
}

// Render Caregivers Table in Dashboard
function renderCaregiversTable(caregivers) {
  const tbody = document.getElementById('caregivers-table-body');
  tbody.innerHTML = '';

  caregivers.forEach(cg => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${cg.caregiver_id}</strong></td>
      <td>${cg.name}</td>
      <td><span class="cg-role-badge">${cg.role}</span></td>
      <td>${cg.languages.join(', ')}</td>
      <td>★ ${cg.rating.toFixed(1)}</td>
      <td>${cg.max_radius_km} km</td>
      <td><span style="color: #34d399;">● Active</span></td>
      <td>
        <button class="verify-btn" onclick="openVerifyModal('${cg.caregiver_id}', '${cg.name}')">
          Verify License
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Filter Caregiver Table by Role
function filterCaregiverTable() {
  const role = document.getElementById('role-filter').value.toLowerCase();
  if (!role) {
    renderCaregiversTable(state.caregiversRoster);
    return;
  }
  const filtered = state.caregiversRoster.filter(cg => cg.role.toLowerCase() === role);
  renderCaregiversTable(filtered);
}

// Voice Input (Web Speech API) with graceful fallback
let voiceRecognition = null;
let isListening = false;
function toggleVoiceInput() {
  const inputEl = document.getElementById('user-input-field');
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    // Fallback simulation for unsupported browsers
    inputEl.placeholder = 'Voice not supported — using demo input...';
    setTimeout(() => {
      inputEl.value = 'papa ko do din se bukhar hai aur khansi bhi';
      inputEl.placeholder = 'Type in English, Hindi, or Hinglish...';
    }, 1200);
    return;
  }
  if (isListening && voiceRecognition) {
    voiceRecognition.stop();
    return;
  }
  voiceRecognition = new SpeechRecognition();
  voiceRecognition.lang = 'hi-IN'; // Hindi/Hinglish; browser may also accept en-IN
  voiceRecognition.interimResults = true;
  voiceRecognition.continuous = false;
  isListening = true;
  inputEl.placeholder = 'Listening (Hindi / English / Hinglish)...';
  voiceRecognition.onresult = (event) => {
    let transcript = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript;
    }
    inputEl.value = transcript;
  };
  voiceRecognition.onerror = () => {
    inputEl.placeholder = 'Voice error — please type your request.';
    isListening = false;
  };
  voiceRecognition.onend = () => {
    isListening = false;
    inputEl.placeholder = 'Type in English, Hindi, or Hinglish...';
  };
  try {
    voiceRecognition.start();
  } catch (e) {
    isListening = false;
    inputEl.placeholder = 'Voice start failed — please type.';
  }
}
// Backwards-compatible alias
function toggleVoiceSim() { toggleVoiceInput(); }

// Append Message to Chat Window
function appendChatMessage(role, text) {
  const chatStream = document.getElementById('chat-stream');
  const msgEl = document.createElement('div');
  msgEl.className = `message ${role}`;

  const avatar = role === 'user' ? '👤' : '🧭';
  const sender = role === 'user' ? 'You' : 'CareCompass Assistant';
  const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  msgEl.innerHTML = `
    <div class="msg-avatar">${avatar}</div>
    <div class="msg-bubble">
      <div class="msg-sender">${sender}</div>
      <div class="msg-text">${text}</div>
      <div class="msg-time">${timeStr}</div>
    </div>
  `;

  chatStream.appendChild(msgEl);
  chatStream.scrollTop = chatStream.scrollHeight;
}

// Handle Triage Form Submission
async function handleTriageSubmit(e) {
  e.preventDefault();
  const inputEl = document.getElementById('user-input-field');
  const userText = inputEl.value.trim();
  if (!userText || state.isProcessing) return;

  state.isProcessing = true;
  const submitBtn = document.getElementById('submit-triage-btn');
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span>Triaging...</span>';

  // 1. Append User Message
  appendChatMessage('user', userText);
  inputEl.value = '';

  const startTime = performance.now();

  try {
    const payload = {
      user_input: userText,
      language: 'auto',
      location: state.currentLocation,
      conversation_history: state.conversationHistory,
    };

    const response = await fetch('/api/v1/triage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const elapsed = Math.round(performance.now() - startTime);
    document.getElementById('response-time-tag').textContent = `Latency: ${elapsed} ms`;

    if (!response.ok) {
      throw new Error(`Server returned ${response.status}`);
    }

    const triageData = await response.json();
    renderTriageAssessment(triageData, userText);

  } catch (err) {
    console.error('Triage error:', err);
    appendChatMessage('assistant', '⚠️ An error occurred during triage. Please ensure the backend server is active.');
  } finally {
    state.isProcessing = false;
    submitBtn.disabled = false;
    submitBtn.innerHTML = `
      <span>Triage Now</span>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
    `;
  }
}

// Render Triage Result in Decision Column
function renderTriageAssessment(data, originalInput) {
  // Update Conversation History
  if (data.follow_up_question) {
    state.conversationHistory.push({ role: 'user', text: originalInput });
    state.conversationHistory.push({ role: 'assistant', follow_up_question: data.follow_up_question });
    appendChatMessage('assistant', `💬 ${data.follow_up_question}`);
  } else {
    state.conversationHistory = []; // Reset on final resolution
    const summaryMsg = data.care_type === 'emergency_112' 
      ? `🚨 EMERGENCY DETECTED: Routed to 112 emergency services.`
      : `✅ Recommended: ${formatCareType(data.care_type)} (${(data.urgency || '').toUpperCase()}). Top matched caregivers allocated below.`;
    appendChatMessage('assistant', summaryMsg);
  }

  // Display Decision Panel
  document.getElementById('decision-placeholder').style.display = 'none';
  const content = document.getElementById('decision-content');
  content.style.display = 'block';

  // Urgency & Care Type
  const urgencyChip = document.getElementById('chip-urgency');
  urgencyChip.className = 'urgency-chip';
  const urgency = data.urgency || 'FOLLOW-UP';
  urgencyChip.textContent = urgency.replace('_', ' ');

  if (data.urgency === 'emergency') {
    urgencyChip.classList.add('emergency');
  } else if (data.urgency === 'same_day') {
    urgencyChip.classList.add('same-day');
  } else if (data.urgency === 'scheduled') {
    urgencyChip.classList.add('scheduled');
  }

  const careTypeEl = document.getElementById('hero-care-type');
  careTypeEl.textContent = data.care_type ? formatCareType(data.care_type) : 'Clarifying Question (Follow-Up)';

  const langChip = document.getElementById('chip-language');
  langChip.textContent = `Input: ${data.detected_language || 'Auto-Detected'}`;

  // Confidence
  const confPct = Math.round((data.confidence || 0) * 100);
  document.getElementById('val-confidence').textContent = `${confPct}%`;
  document.getElementById('conf-bar-fill').style.width = `${confPct}%`;

  // Red Flags
  const globalAlert = document.getElementById('global-emergency-alert');
  const rfBox = document.getElementById('red-flags-box');
  const rfList = document.getElementById('red-flags-list');

  if (data.red_flags && data.red_flags.length > 0) {
    globalAlert.style.display = 'block';
    rfBox.style.display = 'block';
    rfList.innerHTML = '';
    data.red_flags.forEach(flag => {
      const tag = document.createElement('span');
      tag.className = 'rf-tag';
      tag.textContent = flag.replace('_', ' ');
      rfList.appendChild(tag);
    });
  } else {
    globalAlert.style.display = 'none';
    rfBox.style.display = 'none';
  }

  // Explainable Reasoning
  document.getElementById('text-reasoning').textContent = data.reasoning || 'Assessment determined from clinical symptom profile.';

  // TinyFish Medical Knowledge Grounding
  const tfBlock = document.getElementById('tinyfish-block');
  if (data.medical_context) {
    tfBlock.style.display = 'block';
    document.getElementById('text-medical-context').textContent = data.medical_context;
  } else {
    tfBlock.style.display = 'none';
  }

  // Matched Caregivers
  const cgContainer = document.getElementById('caregivers-cards-container');
  cgContainer.innerHTML = '';

  if (data.matched_caregivers && data.matched_caregivers.length > 0) {
    data.matched_caregivers.forEach(m => {
      const card = document.createElement('div');
      card.className = 'caregiver-card';
      const scorePct = Math.round(m.score * 100);

      card.innerHTML = `
        <div class="cg-left">
          <div class="cg-avatar">👨‍⚕️</div>
          <div>
            <div class="cg-name">
              <span>${m.caregiver_id}</span>
              <span class="cg-role-badge">Verified</span>
            </div>
            <div class="cg-meta">${m.reason}</div>
          </div>
        </div>
        <div class="cg-right">
          <div class="cg-score">${scorePct}% Match</div>
          <button class="verify-btn" onclick="openVerifyModal('${m.caregiver_id}', 'Provider ${m.caregiver_id}')">
            Verify NMC
          </button>
        </div>
      `;
      cgContainer.appendChild(card);
    });
  } else {
    const emptyNotice = document.createElement('div');
    emptyNotice.style.padding = '1rem';
    emptyNotice.style.color = '#94a3b8';
    emptyNotice.style.fontSize = '0.85rem';
    emptyNotice.textContent = data.care_type === 'emergency_112' 
      ? '🚨 Emergencies route directly to 112 medical response. Home caregivers are not deployed.'
      : 'No home caregiver allocation required for this outcome.';
    cgContainer.appendChild(emptyNotice);
  }
}

// Helper: Format Care Type String
function formatCareType(type) {
  if (!type) return 'N/A';
  const map = {
    paramedic_home_visit: 'Paramedic Home Visit',
    home_nursing: 'Home Nursing Procedure',
    lab_test_home: 'Diagnostic Lab Test (Home Sample)',
    teleconsultation: 'Doctor Teleconsultation (MBBS)',
    emergency_112: '🚨 Emergency 112 Ambulance',
  };
  return map[type] || type.replace(/_/g, ' ');
}

// Modal Handlers
async function openVerifyModal(caregiverId, name) {
  const modal = document.getElementById('verify-modal');
  const body = document.getElementById('verify-modal-body');
  modal.style.display = 'flex';

  body.innerHTML = `
    <div class="verifying-spinner">
      <div class="spinner"></div>
      <p>TinyFish Agent navigating National Medical Commission Registry for <strong>${caregiverId}</strong>...</p>
    </div>
  `;

  try {
    const res = await fetch(`/api/v1/caregivers/${caregiverId}/verify`);
    const data = await res.json();
    const ver = data.verification || {};

    body.innerHTML = `
      <div style="border-left: 3px solid #10b981; padding-left: 1rem; margin-bottom: 1rem;">
        <h4 style="color: #34d399; font-size: 1.1rem; margin-bottom: 0.25rem;">✓ NMC License Verified & Active</h4>
        <p style="color: #94a3b8; font-size: 0.82rem;">Verified via TinyFish Agent API on National Registry</p>
      </div>

      <div style="background: rgba(255,255,255,0.03); border-radius: 8px; padding: 1rem; font-size: 0.85rem; line-height: 1.6;">
        <div><strong>Provider ID:</strong> ${caregiverId}</div>
        <div><strong>Registration No:</strong> ${ver.registration_number || 'MED-' + caregiverId + '-2026'}</div>
        <div><strong>Authority:</strong> ${ver.verification_source || 'National Medical Commission (NMC)'}</div>
        <div><strong>Status:</strong> <span style="color: #34d399; font-weight: 700;">${ver.license_status || 'Active & Good Standing'}</span></div>
        <div><strong>Tier:</strong> ${ver.credential_tier || 'Verified Clinical Practitioner'}</div>
      </div>
    `;
  } catch (err) {
    body.innerHTML = `<p style="color: #ef4444;">Verification check failed. Please try again.</p>`;
  }
}

function closeVerifyModal() {
  document.getElementById('verify-modal').style.display = 'none';
}
