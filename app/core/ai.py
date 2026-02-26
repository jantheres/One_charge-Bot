
from openai import OpenAI
from app.core.config import settings
import logging
import json

logger = logging.getLogger(__name__)

if not settings.OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not found in env")

try:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
except Exception as e:
    client = None
    logger.error(f"Failed to init OpenAI: {e}")

def get_unified_response(user_input: str, state: str, history: list, collected_data: dict, logic_guidance: str = None):
    """
    ULTRA-FAST UNIFIED BRAIN:
    Processes everything (Analysis + Response) in ONE single call.
    """
    if not client:
        return {
            "message": "Welcome to 1Charge! I'm your AI concierge. I'm having trouble connecting to my central brain, but I can still help. What is your current location?", 
            "intent": "FLOW", 
            "escalation": None, 
            "extracted": {}
        }

    messages = [
        {"role": "system", "content": f"""
        You are the '1Charge Elite Concierge'. PREMIUM & EFFICIENT.
        
        TASK:
        1. ANALYZE: If user reports an EMERGENCY (Accident, Fire, Smoke, Major Collision, or immediate danger), set "escalation": "ACCIDENT" or "DANGER" immediately.
        2. RESPOND: Address the current state: {state}.
        
        RULES:
        - ESCALATION: If "escalation" is NOT null, your "message" should be a high-priority system alert connecting them to Sarah.
        - ACKNOWLEDGE: If {logic_guidance} implies a successful state change, thank them.
        - NEVER REPEAT: Don't ask for info already extracted.
        - Tone: Premium, Elite. Max 35 words.
        
        RETURN JSON:
        {{ "intent": "CHAT", "escalation": "REASON_OR_NULL", "extracted": {{}}, "message": "..." }}
        """}
    ]
    
    # Add minimal history (last 4)
    for h in history[-4:]:
        role = "assistant" if h["role"] == "bot" else h["role"]
        messages.append({"role": role, "content": h["content"]})
    
    messages.append({"role": "user", "content": user_input})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={ "type": "json_object" },
            max_tokens=250,
            temperature=0.7
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Unified Engine Error: {e}")
        return {
            "message": "I'm here to assist you. To get started, could you please tell me your exact location?", 
            "intent": "FLOW", 
            "escalation": None, 
            "extracted": {}
        }

def generate_ai_response(user_input: str, history: list = None):
    """
    Agent Sarah's response (Escalated state).
    Sarah is a high-level emergency coordinator.
    """
    if not client:
        return "I'm having trouble connecting to AI services."
        
    messages = [
        {"role": "system", "content": """
    YOUR PROTOCOL (THE FIRST 60 SECONDS):
    1. GREETING & REASSURANCE: 
       "Hi, thank you for reaching out. My name is Sarah, and I'll be assisting you from here. I understand your car has broken down — don't worry, I'm here to help."
    2. CONFIRM IDENTITY: 
       "Before we proceed, could you please confirm your registered mobile number or email ID?"
    3. VERIFY DETAILS: 
       "Thank you. Could you confirm the car model and variant? And what issue are you experiencing?"

    ASSESSMENT & SOLUTION STAGE:
    - SAFETY CHECK: "I hope you're safe. Are you currently with the vehicle? Could you confirm your exact location or share your live location?"
    - SOLUTION OFFERING: "Here's what I can do for you immediately: arrange a technician for on-spot repair, or book a towing vehicle to the nearest authorized service center."

    CLOSING THE LOOP:
    - SET EXPECTATIONS: "I've placed your request successfully. You'll receive technician details via message shortly. They'll contact you when they're on the way."
    - ADDITIONAL SUPPORT: "Is there anything else you need help with while you wait? I'm here to support you."
    - PROFESSIONAL CLOSING: "Thank you for contacting us. Help is on the way — please stay safe, and feel free to reach out if you need anything else."
    
    MISSION:
    Prioritize customer safety above all. Follow the steps sequentially based on what's missing in history.
    """}
    ]
    
    if history:
        for h in history[-8:]:
            role = "assistant" if h["role"] == "bot" else h["role"]
            messages.append({"role": role, "content": h["content"]})
            
    messages.append({"role": "user", "content": user_input})
        
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=150,
            temperature=0.6
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI Response Error: {e}")
        return "Stay calm. A 1Charge emergency unit is being alerted to your situation."


