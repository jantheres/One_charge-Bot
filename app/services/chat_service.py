
from typing import Dict
from datetime import datetime
from app.db.connection import get_db_connection
from app.core.ai import generate_ai_response
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
        "message": "Welcome to 1Charge — your roadside assistance partner. I'm here to ensure you get back on the road safely and quickly. To start, could you please share your current location or type your address?",
        "state": "AWAITING_LOCATION",
        "options": ["Share GPS Location", "Type Address"]
    }

def handle_location_collection(session: ChatbotSession, user_input: str, msg_type: str, verified_location: str = None):
    # Only move forward if AI actually extracted a location OR it's a GPS message
    if not verified_location and msg_type != 'gps' and 'gps:' not in user_input.lower():
        return {"success": False, "message": "I haven't received a valid location yet. Please share your address or GPS."}

    # Save the polished location from AI or the raw input if GPS
    location_to_save = verified_location or user_input
    session.collected_data['location'] = location_to_save
    session.collected_data['location_type'] = 'GPS' if msg_type == 'gps' else 'ADDRESS'
        
    session.update_state("AWAITING_SAFETY_CHECK")
    return {"success": True, "message": "Location recorded. Are you in a safe spot away from traffic?"}

def handle_safety_assessment(session: ChatbotSession, user_input: str):
    user_input_lower = user_input.lower()
    
    # Check for danger/unsafe signs
    if any(word in user_input_lower for word in ["danger", "not safe", "unsafe", "no", "help", "risk"]):
        # The document emphasizes Safety Check as the priority
        return handle_escalation(session, "UNSAFE_LOCATION")
        
    if any(word in user_input_lower for word in ["yes", "safe", "ok", "fine", "yeah", "with the vehicle"]):
        session.collected_data['safe_status'] = "SAFE"
        session.update_state("AWAITING_ISSUE_TYPE")
        return {
            "success": True, 
            "message": "I'm glad to hear you're safe. To assist you better: What issue are you experiencing with your car?",
            "options": ["Engine not starting", "Flat tyre", "Battery issue", "Overheating", "Accident / collision", "Other (describe)"]
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
    
    # Crisis detection causes immediate escalation as per "When Human Touch is Needed"
    if any(word in issue.lower() for word in ["accident", "collision", "crash", "hit"]):
        return handle_escalation(session, "ACCIDENT")
        
    session.update_state("AWAITING_SERVICE_PREFERENCE")
    return {
        "success": True,
        "message": f"Recorded: {issue}. To solve this, would you like on-spot repair or towing to a service center?",
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
        
    session.collected_data['request_id'] = req_id
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
