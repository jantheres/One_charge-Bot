# 1Charge Chatbot - Integrated API Documentation

This documentation reflects the **Stateless, Pre-Authenticated Architecture**. The chatbot service assumes authentication is handled at the infrastructure level (API Gateway/Firewall) and relies on the host application to provide user profile context.

---

## 🚀 Core Endpoint

### `POST /api/chatbot/message`
Handle all chatbot interactions. Sessions are automatically initialized or retrieved based on the `user_id`.

**Trusted Authentication Context (Headers):**
- `X-User-Id` (Required)
- `X-User-Name` (Optional; if omitted the chatbot can fetch from host app DB)
- `X-User-Phone` (Optional)
- `X-Vehicle-Model` (Optional)

**Request Body:**
```json
{
  "message": "My car won't start",
  "message_type": "text",
  "location": {
    "latitude": 12.9716,
    "longitude": 77.5946
  }
}
```

**Fields:**
- `message` (String, Required): The user's input text or GPS string.
- `message_type` (String): `text` or `gps`. Defaults to `text`.
- `location` (Object, Optional): JSON object with `latitude` and `longitude`.

**Response:**
```json
{
  "session_id": "uuid",
  "message": "I'm sorry to hear that. Are you safe right now?",
  "state": "SAFETY",
  "options": ["Yes, I am safe", "No, I need help"],
  "should_escalate": false,
  "ticket_id": null,
  "escalation_reason": null,
  "service_type": null,
  "priority": null
}
```

---

## �️ The 5-Step Automated Journey

The backend enforces a deterministic state machine. Each request advances the user through these steps:

1.  **IDENTITY**: Greets the user and verifies their mobile number.
2.  **LOCATION**: Collects GPS coordinates or a typed address.
3.  **SAFETY & PROXIMITY**: Verifies the user is safe AND with the vehicle.
4.  **ISSUE**: Identifies the problem (Engine, Tyre, Battery, etc.).
5.  **ROUTING**: Identifies the service type (On-Spot vs Towing).

Clients should use the `state` field in the response to determine what UI to show, and the `options` field for clickable buttons.

---

## 🚨 Emergency Workflow (Agent Sarah)

The API includes a **Crisis Interceptor**. If the message contains emergency keywords or life-threatening distress:
1.  Qualification steps are bypassed.
2.  The session moves to `ESCALATED`.
3.  **Agent Sarah** introduces herself in the `message` field.
4.  If phone or location are missing, the response will dynamically ask for them while in the `ESCALATED` state.

---

## 👮 Agent Dashboard Endpoints

### `GET /api/agent/escalations`
Fetch all active service requests and escalations.

### `PATCH /api/agent/ticket/{ticket_id}/status`
Update ticket status (e.g., to `RESOLVED` or `DISPATCHED`).

---

## 🧑‍💼 Explicit Escalation

### `POST /api/chatbot/escalate`
Force escalation for an existing session (e.g., user taps a "Talk to agent" button).

**Headers:** Same trusted `X-User-*` headers as `/api/chatbot/message`.

**Request Body:**
```json
{
  "reason": "AGENT_REQUEST",
  "priority": "high",
  "collected_context": {}
}
```
*Note: No `session_id` required; the API finds the active session for the authenticated `user_id`.*

---

## 🔒 Security Note
This service trusts a gateway to authenticate the user and inject `X-User-*` headers. Production deployment must ensure the API is only accessible behind that gateway.
