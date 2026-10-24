# 📑 CareCompass AI — API Reference

Base URL: `http://localhost:8000/api/v1`

---

## 1. Triage Endpoints

### `POST /api/v1/triage`
Processes an incoming health request and returns either a clinical decision with matched caregivers, or a targeted follow-up question.

#### Request Body
```json
{
  "user_input": "papa ko do din se bukhar hai aur khansi bhi",
  "language": "auto",
  "location": {
    "lat": 28.54,
    "lng": 77.27
  },
  "conversation_history": []
}
```

#### Fields
- `user_input` (*string*, required): Free-text health description (English, Hindi, Hinglish, 1-2000 chars).
- `language` (*string*, optional, default: `"auto"`): Language hint or `"auto"` for automatic detection.
- `location` (*object*, required):
  - `lat` (*float*): Latitude between 27.5 and 29.5 (Delhi NCR).
  - `lng` (*float*): Longitude between 76.0 and 78.5.
- `conversation_history` (*array of objects*, optional): Previous dialog turns with `role` and `text` / `follow_up_question`.

#### Successful Care Decision (`200 OK`)
```json
{
  "follow_up_question": null,
  "care_type": "paramedic_home_visit",
  "urgency": "same_day",
  "red_flags": [],
  "reasoning": "Patient requires physical vitals check or in-person home health evaluation for acute symptoms without red flags. Sanocare Medic home visit recommended. Urgency assessed as same day.",
  "matched_caregivers": [
    {
      "caregiver_id": "CG_014",
      "score": 0.94,
      "reason": "Hindi-speaking, 3.1 km away, free 14:00–20:00"
    }
  ],
  "confidence": 0.92,
  "detected_language": "Hinglish",
  "medical_context": "Clinical Protocol: Monitor body temperature every 4-6 hours. Ensure oral hydration with electrolyte fluids."
}
```

#### Follow-Up Response (`200 OK`)
```json
{
  "follow_up_question": "Happy to help. Could you tell me the main symptom or service you need (home visit, nursing, lab test, or teleconsult)?",
  "care_type": null,
  "urgency": null,
  "red_flags": [],
  "reasoning": "Input too vague to determine care type safely. Follow-up question asked.",
  "matched_caregivers": [],
  "confidence": 0.0,
  "detected_language": "Hinglish",
  "medical_context": null
}
```

---

## 2. Caregiver Directory & Verification Endpoints

### `GET /api/v1/caregivers`
Retrieve active or all caregivers from the supply roster.

#### Query Parameters
- `role` (*string*, optional): Filter by `medic`, `doctor`, or `phlebotomist`.
- `language` (*string*, optional): Filter by language (e.g. `Hindi`, `English`).
- `active_only` (*boolean*, default: `true`): Filter by active status.

---

### `GET /api/v1/caregivers/{caregiver_id}/verify`
Verifies caregiver license registration live using TinyFish Agent API.

#### Response (`200 OK`)
```json
{
  "caregiver": {
    "caregiver_id": "CG_001",
    "name": "Dr. Aarav Sharma",
    "role": "doctor",
    "qualification": "MBBS, MD",
    "rating": 4.9
  },
  "verification": {
    "caregiver_id": "CG_001",
    "registration_number": "MED-CG_001-2026",
    "verified": true,
    "verification_source": "National Medical Commission (NMC)",
    "license_status": "Active & In Good Standing",
    "credential_tier": "Verified Clinical Practitioner",
    "last_verified_at": "2026-10-24T00:00:00Z"
  }
}
```

---

## 3. Knowledge & Observability Endpoints

### `GET /api/v1/health`
Health check reporting system uptime, active services, and dataset statistics.

### `GET /api/v1/medical-grounding?query={symptoms}`
Query TinyFish clinical knowledge base for verified first-aid and medical guidance.

### `POST /api/v1/feedback`
Submit coordinator feedback to record ground-truth corrections.
```json
{
  "request_id": "REQ-ABCD1234EF56",
  "correct_care_type": "paramedic_home_visit",
  "correct_urgency": "same_day",
  "was_helpful": true,
  "notes": "Patient had slight cough, home visit verified."
}
```

### `GET /api/v1/analytics/summary`
Returns real-time triage distribution and latency metrics.
