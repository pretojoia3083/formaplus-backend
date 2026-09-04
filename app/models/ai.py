from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Text, Enum as SAEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class ContextType(str, enum.Enum):
    COACH = "coach"
    ONBOARDING = "onboarding"
    SUPPORT = "support"

class Role(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"

class AIConversation(Base):
    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    context_type = Column(SAEnum(ContextType, native_enum=False), default=ContextType.COACH)

    # Relationships
    user = relationship("User", back_populates="ai_conversations")
    messages = relationship("AIMessage", back_populates="conversation")

class AIMessage(Base):
    __tablename__ = "ai_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("ai_conversations.id"), nullable=False)
    role = Column(SAEnum(Role, native_enum=False), nullable=False)
    content = Column(Text, nullable=False)
    flagged_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    conversation = relationship("AIConversation", back_populates="messages")
