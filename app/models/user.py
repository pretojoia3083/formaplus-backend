from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class PlanType(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    PREMIUM = "premium"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    plan_type = Column(SAEnum(PlanType, native_enum=False), default=PlanType.FREE)
    status = Column(SAEnum(UserStatus, native_enum=False), default=UserStatus.ACTIVE)

    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False)
    goals = relationship("Goal", back_populates="user")
    preferences = relationship("Preference", back_populates="user", uselist=False)
    workout_plans = relationship("WorkoutPlan", back_populates="user")
    meal_plans = relationship("MealPlan", back_populates="user")
    weight_logs = relationship("WeightLog", back_populates="user")
    measurements = relationship("Measurement", back_populates="user")
    water_logs = relationship("WaterLog", back_populates="user")
    step_logs = relationship("StepLog", back_populates="user")
    ai_conversations = relationship("AIConversation", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")
    meal_logs = relationship("MealLog", back_populates="user")
    professional_profile = relationship("Professional", back_populates="user", uselist=False)
