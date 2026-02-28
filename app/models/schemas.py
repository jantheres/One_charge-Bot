
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime

class ChatRequest(BaseModel):
    customer_id: str
    message: str
    name: Optional[str] = "User"
    phone: Optional[str] = None
    registered_vehicle: Optional[str] = "Unknown Vehicle"
    lat: Optional[float] = None
    lng: Optional[float] = None

class ChatResponseModel(BaseModel):
    intent: str
    emergency_level: str
    confidence: float
    extracted_data: Dict
    next_step: str
    user_reply: str


# --- Production (header-auth) API models ---

class LocationPayload(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None


class ChatbotMessageRequest(BaseModel):
    message: str
    message_type: Optional[str] = "text"  # text|gps|location
    location: Optional[LocationPayload] = None


class ChatbotMessageResponse(BaseModel):
    message: str
    state: str
    options: Optional[List[str]] = None
    should_escalate: bool = False
    ticket_id: Optional[int] = None
    escalation_reason: Optional[str] = None
    service_type: Optional[str] = None  # on_spot|towing|technician_assessment
    priority: Optional[str] = None  # normal|high|emergency
    extracted_data: Optional[Dict] = None

# Agent Dashboard Models
class EscalatedSession(BaseModel):
    session_id: str
    customer_id: str
    current_flow_step: str
    extracted_data: Dict
    updated_at: datetime

class SessionMessage(BaseModel):
    role: str
    content: str
    created_at: datetime

class SessionFullDetails(BaseModel):
    session_id: str
    customer_id: str
    current_flow_step: str
    extracted_data: Dict
    transcript: List[SessionMessage]


class TicketSummary(BaseModel):
    id: int
    session_id: str
    user_id: str
    source: str  # ESCALATION|SERVICE
    reason: str
    priority: str
    status: str
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    vehicle_model: Optional[str] = None
    collected_data: Dict
    created_at: datetime


class UpdateTicketStatusRequest(BaseModel):
    status: str


class EscalateRequest(BaseModel):
    reason: str
    priority: str
    collected_context: Optional[Dict] = None


class EscalateResponse(BaseModel):
    ticket_id: int
    status: str
