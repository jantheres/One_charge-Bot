
from fastapi import APIRouter, HTTPException
from app.models.schemas import MessageRequest, StartResponse, ChatResponse
from app.services.chat_service import (
    sessions, ChatbotSession, get_session, create_session,
    handle_escalation,
    initialize_session_with_user, handle_location_collection,
    handle_safety_assessment, handle_issue_identification,
    handle_service_routing, save_conversation
)
from app.core.ai import (
    generate_ai_response, get_unified_response
)
import uuid

router = APIRouter()

@router.api_route("/start", methods=["GET", "POST"], tags=["Chatbot"], summary="Start New Session", response_model=StartResponse)
async def start_conversation():
    """
    Start a new Chatbot conversation.
    
    *   **Supports**: Both `GET` and `POST`.
    *   **Initial State**: Jumps directly to `AWAITING_LOCATION`.
    """
    session_id = f"session_{uuid.uuid4().hex[:12]}"
    
    session = create_session(session_id)
    
    # Guest defaults
    user_id = None
    user_name = "Guest User"
    
    response = initialize_session_with_user(session, user_id, user_name)
    
    return {
        "session_id": session_id,
        "message": response["message"],
        "state": response["state"],
        "options": response.get("options")
    }

@router.post("/message", tags=["Chatbot"], summary="Send Message", response_model=ChatResponse)
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
    
    # NEW: Safety check - don't process if journey is done
    if session.state == "COMPLETED":
        return {
            "message": "This request is already completed and help is on the way. If you have a new issue, please start a new session.",
            "state": "COMPLETED",
            "request_id": session.collected_data.get("request_id")
        }

    session.add_message("user", user_input)
    
    analysis = get_unified_response(
        user_input=user_input,
        state=session.state,
        history=session.conversation_history,
        collected_data=session.collected_data,
        logic_guidance=None
    )

    # 2. Logic Execution (Source of Truth)
    # We use the AI's extraction to guide the logic
    res = {"success": True, "message": None}
    current_state = session.state
    extracted = analysis.get("extracted", {})
    
    if current_state == "AWAITING_LOCATION":
        res = handle_location_collection(
            session, 
            user_input, 
            req.message_type, 
            verified_location=extracted.get("location")
        )
    elif current_state == "AWAITING_SAFETY_CHECK":
        res = handle_safety_assessment(session, user_input)
    elif current_state == "AWAITING_ISSUE_TYPE":
        res = handle_issue_identification(session, user_input)
    elif current_state == "AWAITING_SERVICE_PREFERENCE":
        res = handle_service_routing(session, user_input)

    # 3. Final Bot Message (AI translates the logic result into premium voice)
    # If the logic failed (e.g. invalid location), AI must tell the user to fix it.
    final_analysis = get_unified_response(
        user_input=user_input,
        state=session.state, # Updated state
        history=session.conversation_history,
        collected_data=session.collected_data,
        logic_guidance=res.get("message") # Tells AI exactly what happened in the logic
    )
    
    # 4. Handle Escalation
    if final_analysis.get("escalation") and session.state != "ESCALATED":
        return handle_escalation(session, final_analysis["escalation"])

    response = {
        "message": final_analysis.get("message"),
        "state": session.state,
        "options": ["Share GPS Location", "Type Address"] if session.state == "AWAITING_LOCATION" else None,
        "request_id": session.collected_data.get("request_id")
    }

    # Save and update history
    save_conversation(session_id, user_input, response.get('message', ''), session.state, response.get('should_escalate', False))
    session.add_message("assistant", response.get('message', ''))
    
    return response
