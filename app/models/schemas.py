from pydantic import BaseModel
from typing import Optional, Dict, List

class ChatMessageRequest(BaseModel):
    user_id: int
    name: str
    phone: str
    vehicle_model: Optional[str] = ""
    message: str
    message_type: Optional[str] = "text" # 'text' (default) or 'gps'
    location: Optional[Dict] = None

class StatusUpdate(BaseModel):
    status: str

class ChatResponse(BaseModel):
    message: str
    state: str
    should_escalate: Optional[bool] = False
    options: Optional[List[str]] = None
    request_id: Optional[str] = None
    escalation_reason: Optional[str] = None
