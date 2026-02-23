# 🚗 1Charge - AI Roadside Assistance Chatbot

A comprehensive, intelligent roadside assistance platform that seamlessly connects stranded drivers with support services. This project demonstrates a complete conversation flow from **AI-Powered Chatbot** to **Human Agent Escalation**.

![Status](https://img.shields.io/badge/Status-Complete-success)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Backend](https://img.shields.io/badge/Backend-FastAPI-green)
![AI](https://img.shields.io/badge/AI-OpenAI_GPT-orange)
![Frontend](https://img.shields.io/badge/Frontend-HTML%2FJS-yellow)

---

## ✨ Key Features

# 🤖 1Charge Roadside Assistance Chatbot

A production-ready, AI-powered chatbot for automotive breakdown assistance. It features a modular architecture, JWT security, and a seamless **Chatbot-to-Human Escalation Flow**.

## 🌟 Key Features

### 1. **Intelligent Chatbot (Level 1 Qualification)**
*   **Identity Verification**: Auto-verifies users via secure JWT tokens (no redundant questions).
*   **Location & Safety**: Captures GPS/Address and immediately assesses safety.
*   **Issue Diagnosis**: Interactive buttons for common issues (Engine, Tyre, Battery, Accident).
*   **Service Routing**: intelligently routes to "On-Spot Repair" or "Towing".

### 2. **AI Escalation Engine (Agent Sarah)**
*   **Smart Triggers**: Automatically detects emergencies (e.g., "accident", "unsafe", "scared").
*   **Seamless Handover**: Transitions context to a human agent without losing data.
*   **AI Persona**: "Agent Sarah" (powered by GPT-4o-mini) follows a strict empathy script:
    *   *Greeting & Reassurance*
    *   *Safety Check*
    *   *Solution Offer*

### 3. **Backend Architecture**
*   **Tech Stack**: Python (FastAPI), MySQL, Pydantic, OpenAI API.
*   **Security**: Role-Based Access Control (RBAC) - separate access for Users vs Agents.
*   **Lifecycle Management**: Full ticket status tracking (`OPEN`, `DISPATCHED`, `RESOLVED`).

## 🚀 Setup Instructions

### Prerequisites
*   Python 3.10+
*   MySQL (XAMPP or Railway)
*   OpenAI API Key

### Installation

1.  **Clone & Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Database**
    *   **Local**: Ensure XAMPP MySQL is running (`localhost`, root, no pass).
    *   Run `database_schema.sql` in phpMyAdmin to create `breakdown_db`.
    *   **Remote**: Update `.env` with Railway Proxy URL.

3.  **Run Application**
    ```bash
    python main.py
    ```
    *   Server starts at `http://localhost:8000`

### 📚 Documentation (Swagger UI)
Visit `http://localhost:8000/docs` to test all APIs interactively.
*   **Login**: Use phone `9876543211` (User) or `9999999999` (Agent Admin).
*   **Start Chat**: Call `/api/chatbot/start` with the token.

## 📂 Project Structure
```
chatbot_project/
├── app/
│   ├── api/          # REST Endpoints (Chat, Auth, Agent)
│   ├── core/         # Config, Security, AI Logic
│   ├── services/     # Business Logic (Chat Flow, Tickets)
│   └── models/       # Pydantic Schemas
├── demo.html         # Frontend Interface
├── database_schema.sql
└── requirements.txt
### 🔄 Seamless Handoff
*   **Auto-Escalation**: AI detects "Accident" or "Unsafe" to trigger immediate handoff.
*   **AI Agent Persona ("Agent Sarah")**:
    *   **Empathy Engine**: Uses a specialized system prompt to simulate a human agent ("Sarah").
    *   **Protocol Adherence**: Strictly follows the "First 60 Seconds" script: Greeting -> Safety Check -> Solution.
    *   **Context Aware**: Knows if location is missing and asks for it only if needed.
*   **Smart Handoff**: Agent acknowledges if location data is already present, avoiding redundant questions.

### 💻 CLI Testing Tool
*   **Headless Mode**: Includes `test_chat_cli.py` to test the full conversation flow directly from the terminal, bypassing the browser.
*   **Verification**: Ideal for verifying API logic and AI responses quickly.

---

## 🛠️ Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | **Python (FastAPI)** | High-performance async web framework. |
| **AI Engine** | **OpenAI GPT-4o-mini** | Intelligent intent classification and escalation detection. |
| **Database** | **MySQL** | Robust relational database for users, requests, and conversations. |
| **Frontend** | **HTML5 / CSS3 / JS** | Responsive web interface for users and agents. |
| **API Style** | **RESTful** | Standard HTTP methods for communication. |

---

## ⚙️ System Workflow

### 1. The Conversation Engine 🗣️
*   **State Machine**: The chatbot uses a finite state machine (`AWAITING_IDENTITY` → `AWAITING_LOCATION` → `AWAITING_ISSUE`) to guide users.
*   **Session Management**: Each user gets a unique `session_id` to persist context across messages.

### 2. Location Intelligence 📍
*   **GPS Capture**: The frontend (`demo.html`) uses the browser's `navigator.geolocation` API.
*   **Data Flow**: Coordinates are sent as a JSON payload to `/api/chatbot/message`.
*   **Dashboard View**: Agents can click "📍 View on Map" to see the exact location on Google Maps.

### 3. AI-Driven Escalation 🚨
*   **Detection**: The backend (`chatbot_service.py`) uses OpenAI to analyze every user message.
*   **Classification**: Inputs are classified into `ACCIDENT`, `UNSAFE`, `AGENT`, or `NORMAL`.
*   **Action**: High-priority classes trigger immediate escalation and alert the Agent Dashboard.

### 4. The Agent Loop 👮
*   **Polling**: The Agent Dashboard (`agent_dashboard.html`) polls `/api/agent/escalations` every 5 seconds.
*   **Alerting**: New high-priority items appear instantly.
*   **Resolution**: Clicking "Resolve" updates the database status to `RESOLVED`.

---

## 🚀 Getting Started

### 1. Prerequisites
*   Python 3.8 or higher.
*   MySQL Server running.
*   OpenAI API Key (in `.env`).

### 2. Installation
Install the required Python packages:
```bash
pip install -r requirements.txt
```

### 3. Configuration
1.  **Database**: Import `database_schema.sql` into your MySQL instance.
    ```bash
    mysql -u root -p < database_schema.sql
    ```
2.  **Environment**: 
    *   Edit `.env` file.
    *   Add your `OPENAI_API_KEY`.
    *   Update DB credentials if necessary.

---

## 🎮 How to Run the Demo

### Step 1: Open the Customer Chat
1.  Double-click **`demo.html`** to open it in your browser.
2.  Click **"Start New Chat"**.
3.  **Login**: Enter a registered phone number:
    *   `9876543210` (Test User - verified)
    *   *Note: Unregistered numbers will be rejected (Strict Mode).*

### Step 2: Open the Agent Dashboard
1.  Double-click **`agent_dashboard.html`** to open it in a **separate tab**.
2.  Keep this tab visible to watch for incoming requests.

### Step 3: Test Scenarios

#### 🟢 Scenario A: The Happy Path (Standard Request)
1.  **Chat**: Share Location -> "Yes, safe" -> "Flat Tyre".
2.  **Bot**: Offers "On-spot repair".
3.  **Result**: Bot creates a Service Request (REQ...).
4.  **Dashboard**: A **BLUE** card appears showing the request.

#### 🔴 Scenario B: The Emergency (AI Handlin)
1.  **Chat**: Type "I had a crash!" or "Car is smoking!".
2.  **AI**: Detects `ACCIDENT` context.
3.  **Bot**: "EMERGENCY DETECTED. Connecting you to priority support..."
4.  **Dashboard**: A **RED** card appears immediately!
5.  **Chat**: Simulates "Agent Sarah" joining the chat.

---

## 🔌 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/chatbot/start` | Initialize a new chat session. |
| `POST` | `/api/chatbot/message` | Send user message (Text/GPS). |
| `GET` | `/api/agent/escalations` | Fetch active tickets. |
| `POST` | `/api/agent/resolve/<id>` | Mark a ticket as resolved. |

---

### Created for 1Charge 🚗
This project implements a production-grade architecture with separation of concerns, AI integration, and real-time dashboard capabilities.
