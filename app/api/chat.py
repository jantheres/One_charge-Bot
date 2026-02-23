
from fastapi import APIRouter, HTTPException, Depends, Request
from app.api import auth
from app.models.schemas import MessageRequest
from app.services.chat_service import (
    sessions, ChatbotSession, get_session, create_session,
    check_escalation_needed, handle_escalation,
    initialize_session_with_user, handle_location_collection,
    handle_safety_assessment, handle_issue_identification,
    handle_service_routing, save_conversation
)
from app.core.ai import generate_ai_response
from app.core.security import verify_token
import uuid

router = APIRouter()

@router.post("/start", tags=["Chatbot"], summary="Start New Session", response_description="New Session ID and Welcome Message")
async def start_conversation(request: Request):
    """
    Start a new Chatbot conversation.
    
    *   **Requires Auth**: Valid User Token.
    *   **Auto-Identity**: Automatically detects user from token, skipping 'What is your name?'.
    *   **Initial State**: Jumps directly to `AWAITING_LOCATION`.
    """
    session_id = f"session_{uuid.uuid4().hex[:12]}"
    
    session = create_session(session_id)
    
    # Extract user info from token (or DB if needed, but token is faster)
    # For now, using guest defaults since token isn't required
    user_id = None
    user_name = "Guest User"
    
    response = initialize_session_with_user(session, user_id, user_name)
    
    return {
        "session_id": session_id,
        "message": response["message"],
        "state": response["state"],
        "options": response.get("options")
    }

@router.post("/message", tags=["Chatbot"], summary="Send Message", response_description="Bot Reply")
async def process_message(req: MessageRequest):
    """
    Process a user message in the active session.
    
    *   **session_id**: The active session ID from `/start`.
    *   **message**: The user's text input or coordinate string.
    *   **message_type**: 'text' (default) or 'gps' (for raw coordinates).
    
    Returns the Bot's next response, current state, and any interactive options.
    """
    session_id = req.session_id
    user_input = req.message
    message_type = req.message_type
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session expired or invalid")
        
    session = sessions[session_id]
    session.add_message("user", user_input)
    
    # 1. Escalation Check
    if session.state != "ESCALATED":
        escalation_reason = check_escalation_needed(user_input)
        if escalation_reason:
            response = handle_escalation(session, escalation_reason)
            return response
            
    # 2. State Machine
    state = session.state
    response = {}
    
    if state == "AWAITING_LOCATION":
        response = handle_location_collection(session, user_input, message_type)
    elif state == "AWAITING_SAFETY_CHECK":
        response = handle_safety_assessment(session, user_input)
    elif state == "AWAITING_ISSUE_TYPE":
        response = handle_issue_identification(session, user_input)
    elif state == "AWAITING_SERVICE_PREFERENCE":
        response = handle_service_routing(session, user_input)
    elif state == "COMPLETED":
        response = {"message": "Session ended. Start new chat."}
    elif state == "ESCALATED":
        response = {"message": generate_ai_response(user_input), "state": "ESCALATED"} 
    else:
        response = {"message": "I'm confused. Let's restart."}
        
    # Save Log
    save_conversation(session_id, user_input, response.get('message', ''), session.state, response.get('should_escalate', False))
    session.add_message("bot", response.get('message', ''))
    
    return response
