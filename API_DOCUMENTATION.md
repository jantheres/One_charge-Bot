# 1Charge Chatbot API Endpoints

## 1. Authentication
### `POST /api/auth/login`
- **Description:** User Login via phone number.
- **Returns:** JWT token.

---

## 2. Chatbot
### `POST /api/chatbot/start`
- **Description:** Start a new chatbot session.
- **Returns:** Session ID and welcome message.
- **Auth Required:** Yes

### `POST /api/chatbot/message`
- **Description:** Send a message to the active session.
- **Returns:** Bot reply and next state.
- **Auth Required:** Yes

---

## 3. Agent Dashboard
### `GET /api/agent/escalations`
- **Description:** Get all active tickets (`OPEN`, `IN_PROGRESS`, `DISPATCHED`, `ON_SITE`).
- **Auth Required:** Yes

### `PATCH /api/agent/ticket/{item_id}/status`
- **Description:** Update ticket status.
- **Valid Statuses:** `OPEN`, `IN_PROGRESS`, `DISPATCHED`, `ON_SITE`, `RESOLVED`, `CLOSED`.
- **Auth Required:** Yes
- **Note:** Replace `{item_id}` with actual ticket ID.

---

## 4. Schemas

### LoginRequest
```json
{ 
  "phone": "9876543211" 
}
```

### MessageRequest
```json
{ 
  "session_id": "<id>", 
  "message": "<text>", 
  "message_type": "text" 
}
```

### StatusUpdate
```json
{ 
  "status": "<new_status>" 
}
```

### Token
```json
{ 
  "access_token": "<jwt>", 
  "token_type": "bearer" 
}
```

### HTTPValidationError
- Standard validation error response.

---

**Note:** Chatbot and Agent endpoints require **JWT Bearer token** in the `Authorization` header.
