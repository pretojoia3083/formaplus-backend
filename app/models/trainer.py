from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SAEnum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class TrainerStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Trainer(Base):
    __tablename__ = "trainers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    full_name = Column(String(200), nullable=False)
    cref = Column(String(50), nullable=True)
    bio = Column(Text, nullable=True)
    specialties = Column(String(500), nullable=True)
    experience_years = Column(Integer, nullable=True)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="trainer_profile")
    clients = relationship("TrainerClient", back_populates="trainer")


class TrainerClient(Base):
    __tablename__ = "trainer_clients"

    id = Column(Integer, primary_key=True, index=True)
    trainer_id = Column(Integer, ForeignKey("trainers.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    trainer = relationship("Trainer", back_populates="clients")
    user = relationship("User")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])
