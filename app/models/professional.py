from sqlalchemy import Column, Integer, String, DateTime, Float, Text, JSON, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class ProfessionalType(str, enum.Enum):
    PERSONAL_TRAINER = "personal_trainer"
    NUTRITIONIST = "nutritionist"
    PHYSIOTHERAPIST = "physiotherapist"
    PSYCHOLOGIST = "psychologist"
    COACH = "coach"

class ProfessionalStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class ServiceType(str, enum.Enum):
    IN_PERSON = "in_person"
    ONLINE = "online"
    BOTH = "both"

class SessionStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class Professional(Base):
    __tablename__ = "professionals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    professional_type = Column(SAEnum(ProfessionalType, native_enum=False), nullable=False)
    status = Column(SAEnum(ProfessionalStatus, native_enum=False), default=ProfessionalStatus.PENDING)
    
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    bio = Column(Text, nullable=True)
    specialties = Column(JSON, nullable=True)
    certifications = Column(JSON, nullable=True)
    experience_years = Column(Integer, nullable=True)
    education = Column(JSON, nullable=True)
    
    service_type = Column(SAEnum(ServiceType, native_enum=False), default=ServiceType.BOTH)
    service_locations = Column(JSON, nullable=True)
    online_platforms = Column(JSON, nullable=True)
    
    price_per_hour_brl = Column(Float, nullable=True)
    price_per_session_brl = Column(Float, nullable=True)
    package_prices = Column(JSON, nullable=True)
    
    rating_avg = Column(Float, default=0)
    rating_count = Column(Integer, default=0)
    
    profile_image_url = Column(String(512), nullable=True)
    gallery_images = Column(JSON, nullable=True)
    video_intro_url = Column(String(512), nullable=True)
    
    availability_schedule = Column(JSON, nullable=True)
    timezone = Column(String(50), default="America/Sao_Paulo")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="professional_profile")
    services = relationship("ProfessionalService", back_populates="professional")
    reviews = relationship("ProfessionalReview", back_populates="professional")
    sessions = relationship("ProfessionalSession", back_populates="professional")
    availability = relationship("ProfessionalAvailability", back_populates="professional")

class ProfessionalService(Base):
    __tablename__ = "professional_services"

    id = Column(Integer, primary_key=True, index=True)
    professional_id = Column(Integer, ForeignKey("professionals.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, default=60)
    price_brl = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    professional = relationship("Professional", back_populates="services")

class ProfessionalAvailability(Base):
    __tablename__ = "professional_availability"

    id = Column(Integer, primary_key=True, index=True)
    professional_id = Column(Integer, ForeignKey("professionals.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)
    start_time = Column(String(5), nullable=False)
    end_time = Column(String(5), nullable=False)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    professional = relationship("Professional", back_populates="availability")

class ProfessionalSession(Base):
    __tablename__ = "professional_sessions"

    id = Column(Integer, primary_key=True, index=True)
    professional_id = Column(Integer, ForeignKey("professionals.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("professional_services.id"), nullable=True)
    
    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    scheduled_end = Column(DateTime(timezone=True), nullable=True)
    status = Column(SAEnum(SessionStatus, native_enum=False), default=SessionStatus.PENDING)
    
    session_type = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    user_feedback = Column(Text, nullable=True)
    user_rating = Column(Integer, nullable=True)
    user_rating_comment = Column(Text, nullable=True)
    
    professional_notes = Column(Text, nullable=True)
    
    price_brl = Column(Float, nullable=False)
    payment_status = Column(String(50), default="pending")
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    professional = relationship("Professional", back_populates="sessions")
    user = relationship("User")
    service = relationship("ProfessionalService")

class ProfessionalReview(Base):
    __tablename__ = "professional_reviews"

    id = Column(Integer, primary_key=True, index=True)
    professional_id = Column(Integer, ForeignKey("professionals.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("professional_sessions.id"), nullable=True)
    
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    professional = relationship("Professional", back_populates="reviews")
    user = relationship("User")
