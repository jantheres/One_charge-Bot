
from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatMessageRequest, ChatResponse
from app.services.chat_service import (
    sessions, ChatbotSession, get_session, create_session,
    handle_escalation, handle_escalated_conversation,
    initialize_session_with_user, handle_location_collection,
    handle_safety_assessment, handle_issue_identification,
    handle_service_routing, save_conversation, _save_session_to_db
)
from app.core.ai import (
    generate_ai_response, get_unified_response
)

router = APIRouter()

@router.post("/message", tags=["Chatbot"], summary="Send Message", response_model=ChatResponse)
async def process_message(req: ChatMessageRequest):
    """
    Process a user message from an authenticated App/Website environment.
    
    *   **Requires**: No JWT (Security handled at infrastructure/network level).
    *   **Internal ID**: Uses `user_id` to maintain continuous context.
    *   **Profile**: Automatically uses name/phone/vehicle from request.
    """
    session_id = f"user_{req.user_id}"
    user_input = req.message
    message_type = req.message_type
    
    # 1. Get or Create Session
    session = get_session(session_id)
    new_session = False
    
    if not session:
        session = create_session(session_id)
        new_session = True
        init_res = initialize_session_with_user(
            session, 
            req.user_id, 
            req.name, 
            req.phone, 
            req.vehicle_model
        )
    session.add_message("user", user_input)
    
    # 2. Analyze intent
    analysis = get_unified_response(
        user_input=user_input,
        state=session.state,
        history=session.conversation_history,
        collected_data=session.collected_data,
        logic_guidance="This is a new session, please greet the user." if new_session else None
    )

    # 3. CRISIS INTERCEPTOR (Priority 1)
    # Immediate escalation for accidents, fires, or danger based on AI intent
    if analysis.get("escalation") and session.state != "ESCALATED":
        reason = analysis.get("escalation")
        esc_res = handle_escalation(session, reason)
        save_conversation(session_id, user_input, esc_res.get('message', ''), "ESCALATED", True)
        session.add_message("assistant", esc_res.get('message', ''))
        _save_session_to_db(session)
        return esc_res

    # 4. Logic processing (Check for completed sessions AFTER crisis check)
    if session.state == "COMPLETED":
        return {
            "message": "This request is already completed and help is on the way. If you have a new issue, please contact support.",
            "state": "COMPLETED",
            "request_id": session.collected_data.get("request_id")
        }

    # 5. State Machine Execution
    res = {"success": True, "message": None}
    current_state = session.state
    extracted = analysis.get("extracted", {})
    
    if current_state == "INITIAL" or current_state == "AWAITING_LOCATION":
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
    elif current_state == "ESCALATED":
        res = handle_escalated_conversation(session, user_input)
        save_conversation(session_id, user_input, res.get('message', ''), session.state, True)
        session.add_message("assistant", res.get('message', ''))
        return {
            "message": res.get("message"),
            "state": "ESCALATED",
            "should_escalate": True,
            "request_id": session.collected_data.get("request_id"),
            "escalation_reason": session.collected_data.get("escalation_reason")
        }

    # IMPORTANT: If the handler triggered an immediate escalation (e.g. via handle_escalation)
    if res.get("should_escalate"):
        save_conversation(session_id, user_input, res.get('message', ''), "ESCALATED", True)
        session.add_message("assistant", res.get('message', ''))
        _save_session_to_db(session)
        return {
            "message": res.get("message"),
            "state": "ESCALATED",
            "should_escalate": True,
            "request_id": res.get("request_id"),
            "escalation_reason": res.get("escalation_reason")
        }

    # Final Bot Message (AI translates logic output)
    guidance = res.get("message", "")
    if new_session:
        guidance = f"WELCOME_GREETING + {guidance}"

    final_analysis = get_unified_response(
        user_input=user_input,
        state=session.state,
        history=session.conversation_history,
        collected_data=session.collected_data,
        logic_guidance=guidance
    )
    
    # Handle AI-detected Escalation
    if final_analysis.get("escalation") and session.state != "ESCALATED":
        esc_res = handle_escalation(session, final_analysis["escalation"])
        save_conversation(session_id, user_input, esc_res.get('message', ''), "ESCALATED", True)
        session.add_message("assistant", esc_res.get('message', ''))
        _save_session_to_db(session)
        return esc_res

    # Options mapping
    state_options = {
        "AWAITING_LOCATION": ["Share GPS Location", "Type Address"],
        "AWAITING_SAFETY_CHECK": ["Yes, I am safe", "No, I need help"],
        "AWAITING_ISSUE_TYPE": ["Engine not starting", "Flat tyre", "Battery issue", "Overheating", "Accident / collision", "Other (describe)"],
        "AWAITING_SERVICE_PREFERENCE": ["On-Spot Repair", "Towing Assistance"],
    }

    response = {
        "message": final_analysis.get("message"),
        "state": session.state,
        "options": state_options.get(session.state),
        "request_id": session.collected_data.get("request_id"),
        "should_escalate": session.state == "ESCALATED",
        "escalation_reason": session.collected_data.get("escalation_reason")
    }

    save_conversation(session_id, user_input, response.get('message', ''), session.state, response.get('should_escalate', False))
    session.add_message("assistant", response.get('message', ''))
    _save_session_to_db(session)
    
    return response
