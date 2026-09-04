from sqlalchemy import Column, Integer, ForeignKey, String, JSON, Enum as SAEnum, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class Location(str, enum.Enum):
    GYM = "gym"
    HOME = "home"

class Preference(Base):
    __tablename__ = "preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    training_days_per_week = Column(Integer, nullable=True)
    session_duration_min = Column(Integer, nullable=True)
    location = Column(SAEnum(Location, native_enum=False), nullable=True)
    available_equipment = Column(JSON, nullable=True)
    dietary_restrictions = Column(JSON, nullable=True)
    disliked_foods = Column(JSON, nullable=True)
    liked_foods = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="preferences")
