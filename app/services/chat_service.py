
from typing import Dict
from datetime import datetime
from app.db.connection import get_db_connection
from app.core.ai import check_escalation_needed, generate_ai_response
import json

class ChatbotSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state = "INITIAL"
        self.collected_data = {}
        self.conversation_history = []
        self.created_at = datetime.now()

    def update_state(self, new_state: str):
        self.state = new_state

    def add_message(self, role: str, content: str):
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

# In-memory session store (Ideally Redis)
sessions: Dict[str, ChatbotSession] = {}

def get_session(session_id: str):
    return sessions.get(session_id)

def create_session(session_id: str):
    sessions[session_id] = ChatbotSession(session_id)
    return sessions[session_id]
    
def save_conversation(session_id: str, user_msg: str, bot_msg: str, state: str, escalate: bool):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
            INSERT INTO conversations (session_id, user_message, bot_response, state, should_escalate)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (session_id, user_msg, bot_msg, state, escalate))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error saving convo: {e}")

# --- Handler Logic (State Machine) ---

def initialize_session_with_user(session: ChatbotSession, user_id: int, user_name: str):
    """
    Initialize session with authenticated user data.
    Skips AWAITING_IDENTITY state.
    """
    session.collected_data['customer_id'] = user_id
    session.collected_data['name'] = user_name
    session.update_state("AWAITING_LOCATION")
    
    return {
        "message": f"Hello {user_name}! I'm here to help. To get started, please share your location.",
        "state": "AWAITING_LOCATION",
        "options": ["Share GPS Location", "Type Address"]
    }

def handle_location_collection(session: ChatbotSession, user_input: str, msg_type: str):
    if msg_type == 'gps' or 'gps:' in user_input.lower():
        try:
            coords = user_input.lower().replace('gps:', '').strip()
            session.collected_data['location'] = coords
            session.collected_data['location_type'] = 'GPS_RAW'
        except:
             session.collected_data['location'] = user_input
    else:
        session.collected_data['location'] = user_input
        session.collected_data['location_type'] = 'ADDRESS'
        
    session.update_state("AWAITING_SAFETY_CHECK")
    return {
        "message": "Thank you for the location. For your safety: Are you currently with the vehicle? Is it in a safe location?",
        "state": "AWAITING_SAFETY_CHECK",
        "options": ["Yes, with vehicle and it's safe", "With vehicle but not in safe spot", "I'm not with the vehicle"]
    }

def handle_safety_assessment(session: ChatbotSession, user_input: str):
    if "not in safe" in user_input.lower():
        session.update_state("ESCALATED")
        return {
            "message": "⚠️ UNSAFE SITUATION. Connecting to agent immediately.",
            "should_escalate": True,
            "state": "ESCALATED",
            "escalation_reason": "UNSAFE_LOCATION"
        }
        
    session.collected_data['safe_status'] = "SAFE"
    session.update_state("AWAITING_ISSUE_TYPE")
    return {
        "message": "Glad to hear you are safe. Can you describe the issue? Or select from options:",
        "state": "AWAITING_ISSUE_TYPE",
        "options": ["Engine not starting", "Flat tyre", "Battery issue", "Overheating", "Accident / collision"]
    }

def handle_issue_identification(session: ChatbotSession, user_input: str):
    issue = user_input
    session.collected_data['issue'] = issue
    
    if "accident" in issue.lower() or "collision" in issue.lower():
        session.update_state("ESCALATED")
        return {
            "message": "⚠️ ACCIDENT REPORTED. Connecting priority agent.",
            "should_escalate": True,
            "state": "ESCALATED",
            "escalation_reason": "ACCIDENT"
        }
        
    session.update_state("AWAITING_SERVICE_PREFERENCE")
    return {
        "message": f"Understood: {issue}. Would you like on-spot repair or towing?",
        "state": "AWAITING_SERVICE_PREFERENCE",
        "options": ["On-Spot Repair", "Towing Assistance"]
    }

from app.services.ticket_service import TicketService

def handle_service_routing(session: ChatbotSession, user_input: str):
    service = "TOWING" if "tow" in user_input.lower() else "REPAIR"
    
    req_id = TicketService.create_service_request(
        session.collected_data.get('customer_id'),
        session.session_id,
        session.collected_data.get('issue'),
        service,
        session.collected_data.get('location')
    )
        
    session.update_state("COMPLETED")
    return {
        "message": f"Request {req_id} created for {service}. A technician has been dispatched.",
        "state": "COMPLETED",
        "request_id": req_id
    }

def handle_escalation(session: ChatbotSession, reason: str):
    session.update_state("ESCALATED")
    
    TicketService.create_escalation(
        session.collected_data.get('customer_id'),
        session.session_id,
        reason,
        session.collected_data,
    )
    
    return {
        "message": "🚨 <b>[System]</b> Escalating to Priority Support...<br><br><b>[Agent Sarah Connected]</b><br>I have prioritized your case. I see you reported an emergency. <br><b>Can you tell me more about your situation? Are you safe?</b>",
        "state": "ESCALATED",
        "should_escalate": True,
        "escalation_reason": reason,
        "priority": "HIGH",
        "collected_data": session.collected_data
    }
