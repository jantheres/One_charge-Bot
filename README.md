# 🚗 1Charge - Integrated AI Roadside Assistance

A production-grade, safety-first roadside assistance platform designed for seamless integration into existing authenticated applications. This project implements a **Stateless Single-Endpoint Architecture** with automated **Crisis Interception** and **Agent Escalation**.

![Status](https://img.shields.io/badge/Status-Integrated-success)
![AI](https://img.shields.io/badge/AI-Crisis_Interceptor-red)
![Backend](https://img.shields.io/badge/Backend-FastAPI-green)

---

## ✨ System Architecture

### 1. **Integrated & Stateless**
The chatbot is designed to live inside an already-authenticated App or Website.
- **Single Endpoint**: `POST /api/chatbot/message` handles everything.
- **No Login Required**: Authentication is handled by the host application / API gateway.
- **Trusted User Context**: The gateway injects identity/profile context via headers:
  - `X-User-Id` (required)
  - Optional: `X-User-Name`, `X-User-Phone`, `X-Vehicle-Model` (if omitted, the chatbot can fetch from the host app DB)
- **Auto-Initialization**: Sessions are automatically created or retrieved using the `X-User-Id`.

### 2. **Safety-First Crisis Interceptor** 🚨
The system prioritizes human life over bot qualification logic.
- **Immediate Detection**: Every message is screened by AI and keyword filters for emergencies (Accidents, Fire, Danger).
- **Zero-Latency Escalation**: If a crisis is detected, the bot bypasses standard prompts and connects the user to **Agent Sarah** immediately.

### 3. **Level 1 Qualification (Bot Flow)**
For non-emergencies, the bot follows a structured journey:
- **Location Capture**: GPS or text address.
- **Safety Status**: Mandatory check before proceeding.
- **Issue Diagnosis**: Engine, Battery, Tyre, Overheating, etc.
- **Service Routing**: Options for On-Spot Repair or Towing.

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+**
- **MySQL Server** (XAMPP recommended)
- **OpenAI API Key** (in `.env`)

### 2. Database Setup
1. Run `database_schema.sql` in your MySQL manager (it creates `breakdown_db` and the runtime tables).
2. Ensure your `.env` DB settings match your local MySQL credentials.

### 3. Run the Backend
```bash
python main.py
```
Server starts at `http://localhost:8000`.

---

## 🎮 Testing the Integration

### Customer Side (`demo.html`)
- Open `demo.html` in your browser.
- It simulates a logged-in session by sending the trusted `X-User-*` headers.
- **Standard Flow**: Say "Hi" -> Provide Location -> "I am safe" -> "Flat Tyre".
- **Crisis Flow**: Type "I just crashed my car!" to trigger the **Crisis Interceptor**.

### Agent Side (`agent_dashboard.html`)
- Open in a separate tab.
- It displays escalations in real-time.
- **Red Cards**: High-priority emergencies.
- **Blue Cards**: Standard service requests.

### Postman
- Use **`OneCharge_Integrated.postman_collection.json`** for direct API testing.
- No tokens are required in the header; authentication is assumed at the gateway level.

---

## 🔌 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/chatbot/message` | Consolidated chat endpoint (handles text, GPS, and profiles). |
| `GET` | `/api/agent/escalations` | Fetch all active human intervention tasks. |
| `PATCH` | `/api/agent/ticket/{id}/status` | Transition ticket through the service lifecycle. |

---

### Created for 1Charge 🚗
This architecture demonstrates a modern approach to AI integration, prioritizing deterministic safety triggers and stateless scalability.
