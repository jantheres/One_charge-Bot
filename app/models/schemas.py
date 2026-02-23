from typing import Optional, Dict, List

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
    options: Optional[List[str]] = None

class ChatResponse(BaseModel):
    message: str
    state: str
    should_escalate: Optional[bool] = False
    options: Optional[List[str]] = None
    request_id: Optional[str] = None
    escalation_reason: Optional[str] = None
