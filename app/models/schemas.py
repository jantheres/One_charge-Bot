
from pydantic import BaseModel
from typing import Optional, Dict

class LoginRequest(BaseModel):
    phone: str

class MessageRequest(BaseModel):
    session_id: str
    message: str
    message_type: Optional[str] = "text"
    location: Optional[Dict] = None

class StatusUpdate(BaseModel):
    status: str
    
class Token(BaseModel):
    access_token: str
    token_type: str

class StartResponse(BaseModel):
    session_id: str
    message: str
    state: str
    options: Optional[list] = None

class ChatResponse(BaseModel):
    message: str
    state: str
    should_escalate: Optional[bool] = False
    options: Optional[list] = None
    request_id: Optional[int] = None
    escalation_reason: Optional[str] = None
