
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
    Initialize session.
    """
    session.collected_data['customer_id'] = user_id
    session.collected_data['name'] = user_name
    session.update_state("AWAITING_LOCATION")
    
    return {
        "message": f"Hello! I'm your 1Charge assistant. I'm here to help with any vehicle breakdowns. To get started, could you please share your current location?",
        "state": "AWAITING_LOCATION",
        "options": ["Share GPS Location", "Type Address"]
    }

def handle_location_collection(session: ChatbotSession, user_input: str, msg_type: str):
    # Validation: If input is very short and not GPS, ask for more detail
    if msg_type == 'text' and len(user_input.split()) < 2 and not any(char.isdigit() for char in user_input):
         return {
            "message": "I'm sorry, I couldn't quite get that address. Could you provide a more specific location or landmark?",
            "state": "AWAITING_LOCATION",
            "options": ["Share GPS Location", "Type Address"]
        }

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
        "message": "Thank you. Location recorded. Now, for your safety: Are you currently in a safe spot away from traffic?",
        "state": "AWAITING_SAFETY_CHECK",
        "options": ["Yes, I am safe", "No, I am in danger/not safe"]
    }

def handle_safety_assessment(session: ChatbotSession, user_input: str):
    user_input_lower = user_input.lower()
    
    # Check for danger/unsafe signs
    if any(word in user_input_lower for word in ["danger", "not safe", "unsafe", "no", "help", "risk"]):
        session.update_state("ESCALATED")
        return handle_escalation(session, "UNSAFE_LOCATION")
        
    # Check for safety confirmation
    if any(word in user_input_lower for word in ["yes", "safe", "ok", "fine", "yeah"]):
        session.collected_data['safe_status'] = "SAFE"
        session.update_state("AWAITING_ISSUE_TYPE")
        return {
            "message": "Glad to hear you are safe. Can you describe the issue? Or select from options:",
            "state": "AWAITING_ISSUE_TYPE",
            "options": ["Engine not starting", "Flat tyre", "Battery issue", "Overheating", "Accident / collision"]
        }
    
    # If ambiguous, ask again
    return {
        "message": "I want to ensure you are safe before we proceed. Are you in a safe location away from oncoming traffic?",
        "state": "AWAITING_SAFETY_CHECK",
        "options": ["Yes, I am safe", "No, I am in danger/not safe"]
    }

def handle_issue_identification(session: ChatbotSession, user_input: str):
    issue = user_input
    session.collected_data['issue'] = issue
    
    if any(word in issue.lower() for word in ["accident", "collision", "crash", "hit"]):
        return handle_escalation(session, "ACCIDENT")
        
    session.update_state("AWAITING_SERVICE_PREFERENCE")
    return {
        "message": f"Understood: {issue}. To solve this, would you like on-spot repair or towing to a service center?",
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
        "message": f"Got it! Request {req_id} has been created for {service}. A technician is being assigned right now. Please stay near your phone.",
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
