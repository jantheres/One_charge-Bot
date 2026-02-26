# 1Charge Chatbot - Integrated API Documentation

This documentation reflects the **Stateless, Pre-Authenticated Architecture**. The chatbot service assumes authentication is handled at the infrastructure level (API Gateway/Firewall) and relies on the host application to provide user profile context.

---

## 🚀 Core Endpoint

### `POST /api/chatbot/message`
Handle all chatbot interactions. Sessions are automatically initialized or retrieved based on the `user_id`.

**Request Body:**
```json
{
  "user_id": 1,
  "name": "John Doe",
  "phone": "9876543210",
  "vehicle_model": "Tesla Model 3",
  "message": "My car won't start",
  "message_type": "text",
  "location": {
    "latitude": 12.9716,
    "longitude": 77.5946
  }
}
```

**Fields:**
- `user_id` (Integer, Required): Unique identifier from the host application.
- `name` (String, Required): User's display name.
- `phone` (String, Required): User's registered phone number.
- `vehicle_model` (String, Required): User's vehicle for context.
- `message` (String, Required): The user's input text or GPS string.
- `message_type` (String): `text` or `gps`. Defaults to `text`.
- `location` (Object, Optional): JSON object with `latitude` and `longitude`.

**Response:**
```json
{
  "message": "I'm sorry to hear that. Are you in a safe location?",
  "state": "AWAITING_SAFETY_CHECK",
  "options": ["Yes, I am safe", "No, I need help"],
  "should_escalate": false,
  "request_id": null,
  "escalation_reason": null
}
```

---

## 🚨 Emergency Workflow (Crisis Interceptor)
The API includes a top-level **Crisis Interceptor**. If the `message` contains keywords like *accident, crash, fire, smoke, danger* or if AI detects a high-priority intent:
1. Standard bot prompts (Location/Safety) are bypassed.
2. The session state immediately moves to `ESCALATED`.
3. A ticket is created in the database.
4. The response includes `should_escalate: true` and a valid `request_id`.

---

## 👮 Agent Dashboard Endpoints

### `GET /api/agent/escalations`
Fetch all active service requests and escalations.
- **Statuses returned:** `OPEN`, `IN_PROGRESS`, `DISPATCHED`, `ON_SITE`.

### `PATCH /api/agent/ticket/{item_id}/status`
Update the status of a specific ticket.
- **Valid Statuses:** `OPEN`, `IN_PROGRESS`, `DISPATCHED`, `ON_SITE`, `RESOLVED`, `CLOSED`.

---

## 🔒 Security Note
This service is **stateless** and does not manage its own JWT tokens. It trusts the `user_id` provided in the payload. Production deployment must ensure this endpoint is only accessible to authenticated internal traffic.
