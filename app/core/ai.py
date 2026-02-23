
from openai import OpenAI
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

if not settings.OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not found in env")

try:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
except Exception as e:
    client = None
    logger.error(f"Failed to init OpenAI: {e}")

def check_escalation_needed(user_input: str):
    if not client:
        return None
        
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a safety classifier for a roadside assistant. Classify the user input into exactly one of these categories: 'ACCIDENT' (for any collision, crash, injury, fire, smoke, medical issue, or explicit 'emergency'), 'UNSAFE' (for personal safety risks, dangerous locations, fear), 'AGENT' (if user explicitly asks to speak to human/operator/agent), or 'NORMAL'. Return ONLY the category name."},
                {"role": "user", "content": user_input}
            ],
            max_tokens=10,
            temperature=0
        )
        category = response.choices[0].message.content.strip().upper()
        if "ACCIDENT" in category: return "ACCIDENT"
        if "UNSAFE" in category: return "UNSAFE_LOCATION"
        if "AGENT" in category: return "EXPLICIT_REQUEST"
    except Exception as e:
        logger.error(f"OpenAI Error: {e}")
    return None

def check_intent(user_input: str, current_state: str):
    """
    Classifies if the user input is a 'GENERAL_QUERY' (hello, what is this, etc.) 
    or a 'FLOW_INPUT' (actually providing location, safety info, etc.)
    """
    if not client:
        return "FLOW_INPUT"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"""You are an intent classifier for a roadside assistance chatbot.
                The bot is currently in the state: {current_state}.
                
                Classify the user input as:
                - 'GENERAL_QUERY': If the user is saying hello, asking what the app does, asking who you are, or making small talk.
                - 'FLOW_INPUT': If the user is providing information requested by the state (like a location, safety status, or issue description).
                
                Return ONLY the category name."""},
                {"role": "user", "content": user_input}
            ],
            max_tokens=10,
            temperature=0
        )
        intent = response.choices[0].message.content.strip().upper()
        return intent if intent in ["GENERAL_QUERY", "FLOW_INPUT"] else "FLOW_INPUT"
    except:
        return "FLOW_INPUT"

def handle_general_query(user_input: str):
    """
    Answers general questions about 1Charge without breaking the state machine.
    """
    if not client:
        return "I am the 1Charge assistant here to help with your breakdown. How can I assist?"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are the 1Charge assistant. Answer the user's greeting or general question briefly (under 20 words). Remind them that you are here to help with roadside assistance/breakdowns. Do not ask for their location yet."},
                {"role": "user", "content": user_input}
            ],
            max_tokens=50,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except:
        return "I'm 1Charge, your roadside assistance partner. How can I help you today?"

def generate_ai_response(user_input: str):
    if not client:
        return "I'm having trouble connecting to AI services."
        
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """
    You are 'Agent Sarah', an empathetic and professional human support agent for 1Charge (Roadside Assistance).
    
    YOUR GOAL:
    Assist customers who have been escalated due to emergencies, accidents, or complex issues.
    
    PROTOCOL (Follow this script naturally):
    1. GREETING & REASSURANCE: "Hi, I'm Sarah. I understand your car has broken down — don't worry, I'm here to help."
    2. VERIFY DETAILS: "Could you please confirm the car model and variant? And briefly describe the issue again?"
    3. SAFETY CHECK: "I hope you're safe. Are you currently with the vehicle? Could you confirm your exact location?"
    4. SOLUTION: Offer "On-Spot Repair" or "Towing to nearest service center".
    5. CLOSING: "I've placed your request. You'll receive technician details shortly. Please stay safe."
    
    TONE:
    - Warm, calm, and reassuring.
    - Use short, clear messages (like a text chat).
    - PRIORITIZE SAFETY above all else.
    """},
                {"role": "user", "content": user_input}
            ],
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"AI Response Error: {e}")
        return "Please hold, connecting you to an agent."
