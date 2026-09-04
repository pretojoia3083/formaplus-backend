from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.models.ai import ContextType, Role

class ConversationCreate(BaseModel):
    context_type: ContextType = ContextType.COACH

class ConversationResponse(BaseModel):
    id: int
    user_id: int
    started_at: datetime
    context_type: ContextType
    messages: List["MessageResponse"] = []
    
    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: Role
    content: str
    flagged_reason: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class CoachRequest(BaseModel):
    user_id: int
    user_message: str
    conversation_id: Optional[int] = None

class CoachResponse(BaseModel):
    response: str
    conversation_id: int
    message_id: int

class RiskClassificationRequest(BaseModel):
    user_message: str

class RiskClassificationResponse(BaseModel):
    category: str
    confidence: float
    reason: str
