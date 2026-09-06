from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TrainerRegister(BaseModel):
    full_name: str
    cref: Optional[str] = None
    bio: Optional[str] = None
    specialties: Optional[str] = None
    experience_years: Optional[int] = None


class TrainerResponse(BaseModel):
    id: int
    user_id: int
    full_name: str
    cref: Optional[str] = None
    bio: Optional[str] = None
    specialties: Optional[str] = None
    experience_years: Optional[int] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessageCreate(BaseModel):
    receiver_id: int
    message: str


class ChatMessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ChatConversation(BaseModel):
    user_id: int
    user_name: str
    last_message: str
    last_message_at: datetime
    unread_count: int


class TrainerClientResponse(BaseModel):
    id: int
    trainer_id: int
    user_id: int
    status: str
    created_at: datetime
    client_name: Optional[str] = None

    class Config:
        from_attributes = True


class AssignClientRequest(BaseModel):
    user_email: str
