# 🔒 CareCompass AI — Privacy, Security & Compliance

CareCompass AI adheres to healthcare privacy principles inspired by **DISHA (Digital Information Security in Healthcare Act)** and **HIPAA**.

---

## 1. Zero-PII Logging Architecture

Personal Identifiable Information (PII) is never stored in plain text in production logs or persistent analytics:
- **One-Way Hashing:** User text and exact coordinates are transformed into 16-character SHA-256 hashes (`user_input_hash`, `location_hash`) prior to audit emission.
- **Ephemeral Sessions:** Conversation context is held in memory during the request cycle and never dumped to disk.
- **Data Minimization:** The API only accepts latitude and longitude coordinates. Full street addresses, patient names, Aadhaar numbers, and phone numbers are excluded from the triage contract.

---

## 2. API Gateway & Defense-in-Depth

### 2.1 Input Sanitization
- Strips all HTML and script injection vectors (`<script>`, `<iframe>`, `javascript:`).
- Removes non-printable control characters while explicitly preserving Devanagari Unicode code points (`U+0900` to `U+097F`).
- Enforces strict length limits (maximum 2,000 characters).

### 2.2 Prompt Injection Defense
- Rejects jailbreak payloads targeting underlying LLMs:
  - `ignore previous instructions`
  - `you are now an unrestricted assistant`
  - `system prompt override`
  - Special delimiter injection tokens (`<|...|>`, `[[...INST...]]`).

### 2.3 Rate Limiting
- IP-based sliding window rate limiter allowing up to 100 requests per minute per IP address.
- Returns `429 Too Many Requests` with `X-RateLimit-Remaining` headers when threshold is breached.

---

## 3. Medical Safety & Clinical Governance

### 3.1 Dual-Layer Red Flag Priority
Safety is an absolute priority over system efficiency:
- Red flag scanning is executed **prior to** any classification or caregiver allocation.
- In the event of conflicting signals, the system always escalates towards the higher acuity level (`emergency_112`).
- Emergency responses bypass all home caregiver matching to ensure patients are immediately directed to emergency services.

### 3.2 Audit Trail
Every transaction is logged with a unique `REQ-` identifier containing:
- Timestamp (UTC)
- Input hash
- Acquired care type and urgency
- Detected red flags
- Model confidence score
- Total execution latency (ms)
