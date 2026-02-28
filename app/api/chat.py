
from __future__ import annotations

import json
import uuid
from typing import Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException

from app.core.ai import SYSTEM_PROMPT, get_ai_response
from app.core.auth_context import UserContext, get_user_context
from app.models.schemas import (
    ChatRequest,
    ChatResponseModel,
    LocationPayload,
    ChatbotMessageRequest,
    ChatbotMessageResponse,
    EscalateRequest,
    EscalateResponse,
)
from app.services.db import (
    create_session,
    create_ticket,
    get_active_session,
    get_chat_history,
    get_customer_profile,
    get_open_ticket_for_session,
    get_session_by_id,
    save_message,
    update_session,
)

router = APIRouter()


ISSUE_OPTIONS = [
    "Engine not starting",
    "Flat tyre",
    "Battery issue",
    "Overheating",
    "Accident / collision",
    "Other (describe)",
]

SAFETY_OPTIONS = ["Yes, I am safe", "No, I need help"]


def _normalize_state(s: Optional[str]) -> str:
    s = (s or "").upper().strip()
    if not s:
        return "IDENTITY"
    if "ESC" in s:
        return "ESCALATED"
    if "IDEN" in s:
        return "IDENTITY"
    if "LOC" in s:
        return "LOCATION"
    if "SAFE" in s:
        return "SAFETY"
    if "ISS" in s:
        return "ISSUE"
    if "ROUT" in s:
        return "ROUTING"
    if "CONF" in s:
        return "CONFIRMATION"
    return "IDENTITY"


def _user_requested_agent(text: str) -> bool:
    t = (text or "").lower()
    return any(w in t for w in ["talk to agent", "agent", "human", "person", "someone", "call me", "real support", "escalate"])


def _is_emergency_keyword(text: str) -> bool:
    t = (text or "").lower()
    # Broad detection for emergency/danger
    emergency_words = [
        "emergency", "accident", "collision", "crash", "hit", "danger", "unsafe", 
        "fire", "ambulance", "police", "help", "save", "die", "dying", "hurt", 
        "bleeding", "pain", "injured", "hospital", "stuck", "trapped", "danger", "threat"
    ]
    return any(w in t for w in emergency_words)


def _determine_service(issue_category: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Return (service_type, priority)."""
    if not issue_category:
        return None, None
    c = str(issue_category).lower()
    if "flat" in c or "tyre" in c:
        return "on_spot", "normal"
    if "battery" in c or "jump" in c:
        return "on_spot", "normal"
    if "engine" in c or "start" in c or "not starting" in c:
        return "technician_assessment", "normal"
    if "overheat" in c or "temperature" in c:
        return "technician_assessment", "high"
    if "accident" in c or "collision" in c or "crash" in c:
        return "towing", "emergency"
    return None, None


def _enforce_progression(current_state: str, facts: dict) -> str:
    """Deterministic state machine enforcing Identity -> Location -> Safety -> Issue -> Routing -> Confirmation."""
    state = _normalize_state(current_state)

    has_identity = _coerce_bool(facts.get("phone_verified")) is True
    has_location = bool(
        facts.get("location_confirmed")
        or facts.get("latitude") is not None
        or facts.get("longitude") is not None
        or facts.get("address")
    )
    is_safe = _coerce_bool(facts.get("is_safe")) is True
    is_with_vehicle = _coerce_bool(facts.get("is_with_vehicle")) is True
    
    has_issue = bool(facts.get("issue_category"))
    has_service = bool(facts.get("service_type"))

    if state == "IDENTITY":
        return "LOCATION" if has_identity else "IDENTITY"
    if state == "LOCATION":
        return "SAFETY" if has_location else "LOCATION"
    if state == "SAFETY":
        return "ISSUE" if (is_safe and is_with_vehicle) else "SAFETY"
    if state == "ISSUE":
        return "ROUTING" if has_issue else "ISSUE"
    if state == "ROUTING":
        return "CONFIRMATION" if has_service else "ROUTING"
    if state == "CONFIRMATION":
        return "CONFIRMATION"
    if state == "ESCALATED":
        return "ESCALATED"
    return "IDENTITY"


def _options_for_state(state: str) -> Optional[list[str]]:
    state = _normalize_state(state)
    if state == "SAFETY":
        return SAFETY_OPTIONS
    if state == "ISSUE":
        return ISSUE_OPTIONS
    if state == "ROUTING":
        return ["On-Spot Repair", "Towing Assistance"]
    return None


def _merge_facts(current: dict, new: dict) -> dict:
    merged = dict(current or {})
    for k, v in (new or {}).items():
        if v is not None:
            # logic: don't let LLM overwrite a 'True' confirmation with 'False' 
            # if we already have structured data.
            if k in ["location_confirmed", "phone_verified", "is_safe", "is_with_vehicle"] and merged.get(k) is True and v is False:
                continue
            merged[k] = v
    return merged


def _coerce_bool(v) -> Optional[bool]:
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ["true", "1", "yes", "y"]:
        return True
    if s in ["false", "0", "no", "n"]:
        return False
    return None


def _is_placeholder_location(lat: Optional[float], lng: Optional[float], address: Optional[str]) -> bool:
    addr = (address or "").strip().lower()
    # Swagger UI commonly uses "string" as a placeholder.
    if addr in ["string", "n/a", "na", "none"]:
        addr = ""
    if lat is not None and lng is not None:
        try:
            if float(lat) == 0.0 and float(lng) == 0.0 and not addr:
                return True
        except Exception:
            pass
    return False


def _build_agent_context(user: UserContext, session_id: str, facts: dict, reason: str, priority: str) -> dict:
    return {
        "session_id": session_id,
        "user": {
            "user_id": user.user_id,
            "name": user.name,
            "phone": user.phone,
            "vehicle_model": user.vehicle_model,
        },
        "safety": {
            "is_safe": facts.get("is_safe"),
        },
        "location": {
            "latitude": facts.get("latitude") or facts.get("lat"),
            "longitude": facts.get("longitude") or facts.get("lng"),
            "address": facts.get("address"),
        },
        "issue": {
            "issue_category": facts.get("issue_category"),
        },
        "routing": {
            "service_type": facts.get("service_type"),
        },
        "priority": priority,
        "reason": reason,
        "facts": facts,
    }


async def _escalate_session(
    *,
    user: UserContext,
    session_id: str,
    facts: dict,
    reason: str,
    priority: str,
    user_visible_message: str,
) -> ChatbotMessageResponse:
    open_ticket = get_open_ticket_for_session(session_id)
    if open_ticket:
        ticket_id = open_ticket["id"]
    else:
        ticket_id = create_ticket(
            session_id=session_id,
            user_id=user.user_id,
            source="ESCALATION",
            reason=reason,
            priority=priority,
            collected_data=_build_agent_context(user, session_id, facts, reason, priority),
            customer_name=user.name,
            phone=user.phone,
            vehicle_model=user.vehicle_model,
        )

    facts = dict(facts or {})
    facts["priority"] = priority
    facts["escalation_reason"] = reason

    update_session(session_id, "ESCALATED", facts, status="ESCALATED")
    
    # Dynamic Escalation Greeting based on context
    issue = facts.get("issue_category")
    if reason == "ACCIDENT" or (issue and "accident" in issue.lower()):
        context_phrase = "there's been an accident"
    elif reason == "UNSAFE":
        context_phrase = "you're in an unsafe situation"
    elif issue:
        context_phrase = f"your vehicle is having a {issue.lower()} issue"
    else:
        context_phrase = "you're facing an emergency"

    escalation_greeting = (
        f"Hi, thank you for reaching out. My name is Agent Sarah, and I'll be assisting you from here. "
        f"I understand {context_phrase} — don't worry, I'm here to help."
    )
    
    bot_message = f"{user_visible_message}\n\n{escalation_greeting}\n\nReplies received will be soon."
    save_message(session_id, "assistant", bot_message)

    return ChatbotMessageResponse(
        message=bot_message,
        state="ESCALATED",
        options=None,
        should_escalate=True,
        ticket_id=ticket_id,
        escalation_reason=reason,
        service_type=facts.get("service_type"),
        priority=priority,
        extracted_data=facts,
    )


async def _handle_chatbot_message(req: ChatbotMessageRequest, user: UserContext) -> ChatbotMessageResponse:
    """
    Shared handler for both:
    - Production endpoint (header-based user context)
    - Legacy demo endpoint (body-based user context)
    """
    # 0) Enrich missing profile context from host app DB (optional)
    if not user.name or not str(user.name).strip() or not user.phone or not user.vehicle_model:
        prof = get_customer_profile(str(user.user_id))
        if prof:
            user = UserContext(
                user_id=str(user.user_id),
                name=(user.name or prof.get("name") or "User"),
                phone=(user.phone or prof.get("phone")),
                vehicle_model=(user.vehicle_model or prof.get("vehicle_model")),
            )
        else:
            user = UserContext(
                user_id=str(user.user_id),
                name=(user.name or "User"),
                phone=user.phone,
                vehicle_model=user.vehicle_model,
            )

    # 1) Load or create session (one active session per user_id)
    session = get_active_session(str(user.user_id))

    is_new_session = False
    if not session:
        is_new_session = True
        session_id = str(uuid.uuid4())
        initial_data = {
            "user_name": user.name,
            "phone_or_email": user.phone,
            "vehicle_model": user.vehicle_model,
            "unclear_count": 0,
        }
        create_session(
            session_id=session_id,
            customer_id=str(user.user_id),
            system_prompt=SYSTEM_PROMPT,
            initial_data=initial_data,
            initial_flow_step="IDENTITY",
        )
        session = {
            "session_id": session_id,
            "customer_id": str(user.user_id),
            "extracted_data": initial_data,
            "current_flow_step": "IDENTITY",
            "status": "ACTIVE",
        }

    session_id = session["session_id"]
    facts = session.get("extracted_data") or {}
    if isinstance(facts, str):
        facts = json.loads(facts)

    # Clean obvious Swagger placeholders from stored facts
    if str(facts.get("address", "")).strip().lower() in ["string", "n/a", "na", "none"]:
        facts.pop("address", None)
    if facts.get("latitude") == 0 or facts.get("latitude") == 0.0:
        # keep 0 only if explicitly intended; Swagger placeholders often set 0,0
        if facts.get("longitude") in (0, 0.0):
            facts.pop("latitude", None)
            facts.pop("longitude", None)
            facts.pop("location_confirmed", None)

    # Always sync current authenticated context into facts (prevents stale profile data)
    if user.name and str(user.name).strip():
        facts["user_name"] = user.name
    if user.phone:
        facts["phone_or_email"] = user.phone
    if user.vehicle_model:
        facts["vehicle_model"] = user.vehicle_model

    # 2) Apply structured location from client (app/web)
    if req.location:
        lat = req.location.latitude
        lng = req.location.longitude
        addr = req.location.address
        if not _is_placeholder_location(lat, lng, addr):
            if lat is not None:
                facts["latitude"] = lat
            if lng is not None:
                facts["longitude"] = lng
            if addr and addr.strip().lower() != "string":
                facts["address"] = addr
            if (lat is not None) or (lng is not None) or (addr and addr.strip().lower() != "string"):
                facts["location_confirmed"] = True

    # 3) Persist user message
    user_message = req.message
    save_message(session_id, "user", user_message)

    # If this session is already escalated, check if the user is trying to restart
    is_escalated = str(session.get("status", "")).upper() == "ESCALATED"
    if is_escalated:
        greetings = ["hi", "hello", "start", "restart", "menu", "status"]
        if any(g in user_message.lower() for g in greetings):
             update_session(session_id, "RESOLVED", facts, status="RESOLVED")
             return await _handle_chatbot_message(req, user)

    # Swagger UI commonly sends placeholder "string" as message; do not escalate on that.
    if str(user_message).strip().lower() == "string":
        bot_message = f"Welcome! I'm here to help. Could you please confirm your registered mobile number?"
        update_session(session_id, "IDENTITY", facts, status="ACTIVE")
        save_message(session_id, "assistant", bot_message)
        return ChatbotMessageResponse(
            message=bot_message,
            state="IDENTITY",
            options=None,
            should_escalate=False,
            ticket_id=None,
            escalation_reason=None,
            service_type=facts.get("service_type"),
            priority=facts.get("priority"),
            extracted_data=facts,
        )

    # 4) Build LLM history (system prompt stored in DB + current context injection)
    history = get_chat_history(session_id, limit=12)
    current_state = _normalize_state(session.get("current_flow_step"))

    context_msg = {
        "role": "system",
        "content": (
            f"AUTH_CONTEXT: user_id={user.user_id}, name={user.name}, phone={user.phone}, vehicle_model={user.vehicle_model}. "
            f"CURRENT_STATE: {current_state}. "
            f"FACTS_JSON: {json.dumps(facts)}. "
            "INSTRUCTION: Follow the journey: Identity -> Location -> Safety -> Issue -> Routing. Ask one clear question for the current step. "
            "Safety and proximity check must be confirmed before identifying the issue. "
            "If user is in danger or distress, escalate immediately."
        ),
    }
    history.insert(0, context_msg)

    ai_res = await get_ai_response(history)
    ai_confidence = float(ai_res.get("confidence", 1.0) or 0.0)
    ai_extracted = ai_res.get("extracted_data", {}) if isinstance(ai_res.get("extracted_data", {}), dict) else {}
    facts = _merge_facts(facts, ai_extracted)

    # 6) Deterministic routing decision
    service_type, priority = _determine_service(facts.get("issue_category"))
    if service_type:
        facts["service_type"] = service_type
    if priority:
        facts["priority"] = priority

    # 7) Unclear response tracking + escalation triggers
    unclear_count = int(facts.get("unclear_count") or 0)
    user_requested_human = _user_requested_agent(user_message)

    state_after = _enforce_progression(current_state, facts)

    # Safety is the top-level deterministic rule:
    # - If the user is NOT safe -> immediate escalation
    # - If the user IS safe -> do NOT escalate based only on an LLM-emergency misclassification
    is_safe_val = _coerce_bool(facts.get("is_safe"))
    if is_safe_val is False:
        return await _escalate_session(
            user=user,
            session_id=session_id,
            facts=facts,
            reason="UNSAFE",
            priority="emergency",
            user_visible_message="I’m sorry you’re not safe. I’m connecting you to a human agent right now. If you are in immediate danger, please contact local emergency services.",
        )

    # Reset unclear_count when the user provides a valid answer for the current step
    if current_state == "SAFETY" and is_safe_val is not None:
        unclear_count = 0
    elif current_state == "LOCATION" and (
        facts.get("location_confirmed") or facts.get("latitude") or facts.get("longitude") or facts.get("address")
    ):
        unclear_count = 0
    elif current_state == "ISSUE" and facts.get("issue_category"):
        unclear_count = 0

    missing_critical = False
    if state_after == "SAFETY" and facts.get("is_safe") is None:
        missing_critical = True
    if state_after == "LOCATION" and not (
        facts.get("location_confirmed") or facts.get("latitude") or facts.get("longitude") or facts.get("address")
    ):
        missing_critical = True
    if state_after == "ISSUE" and not facts.get("issue_category"):
        missing_critical = True

    if (not is_new_session) and ai_confidence < 0.55 and missing_critical:
        unclear_count += 1
    facts["unclear_count"] = unclear_count

    is_accident = "accident" in str(facts.get("issue_category", "")).lower() or "collision" in str(
        facts.get("issue_category", "")
    ).lower()

    # If the user is ALREADY escalated, skip the new escalation detection
    if is_escalated:
        should_escalate = False
    else:
        is_emergency = _is_emergency_keyword(user_message)
        should_escalate = (
            user_requested_human
            or is_emergency
            or is_accident
            or unclear_count > 2
            or ai_res.get("next_step") == "ESCALATED"
            or ai_res.get("emergency_level") == "HIGH"
        )

    if should_escalate:
        # Determine reason
        if user_requested_human:
            reason = "AGENT_REQUEST"
        elif is_accident or is_emergency:
            reason = "EMERGENCY"
        else:
            reason = "UNCLEAR"

        pr = "emergency" if (is_accident or is_emergency) else "high"
        
        # Determine if we still need info to show in the FIRST escalation message
        needed = []
        if not facts.get("phone_verified"): needed.append("mobile number")
        if not (facts.get("latitude") or facts.get("address")): needed.append("location")
        
        esc_msg = "Connecting you to a human agent now."
        if needed:
            esc_msg = f"I'm connecting you to an agent, but first, could you please provide your {' and '.join(needed)} so they can help you faster?"

        return await _escalate_session(
            user=user,
            session_id=session_id,
            facts=facts,
            reason=reason,
            priority=pr,
            user_visible_message=esc_msg,
        )

    # 8) Handle post-escalation responses (if already escalated)
    if is_escalated:
        open_ticket = get_open_ticket_for_session(session_id)
        ticket_id = open_ticket["id"] if open_ticket else None
        
        # Check what we had BEFORE this message vs NOW
        had_all = bool(session.get("extracted_data", {}).get("phone_verified")) and \
                  bool(session.get("extracted_data", {}).get("latitude") or session.get("extracted_data", {}).get("address"))
        
        has_phone = bool(facts.get("phone_verified"))
        has_loc = bool(facts.get("latitude") or facts.get("address"))
        
        if (not had_all) and has_phone and has_loc:
            # We JUST finished collecting everything
            bot_message = "Thank you! I've received your details. Our team is on the way and will reach you very soon."
        elif not has_phone or not has_loc:
            needed = []
            if not has_phone: needed.append("mobile number")
            if not has_loc: needed.append("location")
            bot_message = f"Agent Sarah is reviewing your case. Could you please provide your {' and '.join(needed)} so she can assist you faster?"
        else:
            bot_message = "Agent Sarah is reviewing your case. Please stay safe; our team is arranging assistance now."
            
        update_session(session_id, "ESCALATED", facts, status="ESCALATED")
        save_message(session_id, "assistant", bot_message)
        return ChatbotMessageResponse(
            message=bot_message,
            state="ESCALATED",
            options=["Start New Request"],
            should_escalate=True,
            ticket_id=ticket_id,
            escalation_reason=facts.get("escalation_reason"),
            service_type=facts.get("service_type"),
            priority=facts.get("priority") or "high",
            extracted_data=facts,
        )

    # 9) Continue bot flow
    bot_message = ai_res.get("user_reply") or ai_res.get("message") or "Thanks. One moment while I help you."
    
    # State-Message Alignment Fix
    # If the state machine progressed, but the AI message is still asking for the previous step's data,
    # we should override it with a proper transition message.
    if state_after == "LOCATION" and (current_state == "IDENTITY" or current_state == "LOCATION"):
        if "location" not in bot_message.lower() and "address" not in bot_message.lower():
            bot_message = "Thank you for confirming your mobile number. Now, could you please provide your current location? You can share your GPS coordinates or a typed address."

    if state_after == "SAFETY" and (current_state == "LOCATION" or current_state == "SAFETY"):
        if facts.get("is_safe") is None or facts.get("is_with_vehicle") is None:
             bot_message = "I've recorded your location. To ensure we can help you properly: Are you safe and are you currently with the vehicle?"
        elif not facts.get("is_safe"):
             bot_message = "I'm concerned for your safety. Are you in a safe location away from traffic?"
        elif not facts.get("is_with_vehicle"):
             bot_message = "I'm glad you are safe. However, for us to assist you with the vehicle, we need to know if you are currently with it. Are you at the car's location?"
            
    if state_after == "ISSUE" and current_state == "SAFETY":
        if "safe" in bot_message.lower():
            bot_message = "I'm glad to hear you're safe. What issue are you experiencing with your car?"

    if state_after == "IDENTITY":
        if len(bot_message) < 10 or "number" not in bot_message.lower():
            bot_message = f"Welcome! I see you are logged in as {user.name}. To assist you with your {user.vehicle_model}, could you please confirm your registered mobile number?"

    if state_after == "CONFIRMATION":
        bot_message = "Thank you! Your service has been booked. Our team will reach you soon."
        
    update_session(session_id, state_after, facts, status="ACTIVE")
    save_message(session_id, "assistant", bot_message)

    return ChatbotMessageResponse(
        message=bot_message,
        state=state_after,
        options=_options_for_state(state_after),
        should_escalate=False,
        ticket_id=None,
        escalation_reason=None,
        service_type=facts.get("service_type"),
        priority=facts.get("priority"),
        extracted_data=facts,
    )


@router.post("/chatbot/message", response_model=ChatbotMessageResponse, tags=["Chatbot"])
async def chatbot_message(
    req: ChatbotMessageRequest,
    user: UserContext = Depends(get_user_context),
):
    """
    Production endpoint. User identity/context must be provided by a trusted gateway via X-User-* headers.
    """
    return await _handle_chatbot_message(req=req, user=user)


@router.post("/chatbot/escalate", response_model=EscalateResponse, tags=["Chatbot"])
async def chatbot_escalate(
    req: EscalateRequest,
    user: UserContext = Depends(get_user_context),
):
    session = get_active_session(str(user.user_id))
    if not session:
        # Create session if it doesn't exist but user wants to escalate
        session_id = str(uuid.uuid4())
        initial_data = {"unclear_count": 0}
        create_session(
            session_id=session_id,
            customer_id=str(user.user_id),
            system_prompt=SYSTEM_PROMPT,
            initial_data=initial_data,
            initial_flow_step="ESCALATED",
        )
        session_id_val = session_id
        facts = initial_data
    else:
        session_id_val = session["session_id"]
        facts = session.get("extracted_data") or {}
        if isinstance(facts, str):
            facts = json.loads(facts)

    if req.collected_context:
        facts = _merge_facts(facts, req.collected_context)

    open_ticket = get_open_ticket_for_session(session_id_val)
    if open_ticket:
        ticket_id = open_ticket["id"]
    else:
        ticket_id = create_ticket(
            session_id=session_id_val,
            user_id=user.user_id,
            source="ESCALATION",
            reason=req.reason,
            priority=req.priority,
            collected_data=_build_agent_context(user, session_id_val, facts, req.reason, req.priority),
            customer_name=user.name,
            phone=user.phone,
            vehicle_model=user.vehicle_model,
        )

    update_session(session_id_val, "ESCALATED", facts, status="ESCALATED")
    save_message(session_id_val, "assistant", "I’m connecting you to a human agent now.")

    return EscalateResponse(ticket_id=int(ticket_id), status="OPEN")


@router.post("/chat", response_model=ChatResponseModel, tags=["Chat"])
async def chat_endpoint(req: ChatRequest):
    # Legacy compatibility wrapper (used by demo.html historically).
    user = UserContext(
        user_id=str(req.customer_id),
        name=req.name or "User",
        phone=req.phone,
        vehicle_model=req.registered_vehicle,
    )

    location = None
    if req.lat is not None or req.lng is not None:
        location = LocationPayload(latitude=req.lat, longitude=req.lng)

    res = await _handle_chatbot_message(
        req=ChatbotMessageRequest(message=req.message, message_type="text", location=location),
        user=user,
    )

    priority = (res.priority or "normal").lower()
    emergency_level = "HIGH" if priority == "emergency" else ("MEDIUM" if priority == "high" else "LOW")

    return ChatResponseModel(
        intent="SUPPORT",
        emergency_level=emergency_level,
        confidence=0.9,
        extracted_data=res.extracted_data or {},
        next_step=res.state,
        user_reply=res.message,
    )
