from sqlalchemy import Column, Integer, String, Text, Float, JSON, Enum as SAEnum, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class MuscleGroup(str, enum.Enum):
    CHEST = "chest"
    BACK = "back"
    LEGS = "legs"
    SHOULDERS = "shoulders"
    BICEPS = "biceps"
    TRICEPS = "triceps"
    CORE = "core"
    GLUTES = "glutes"
    FULL_BODY = "full_body"

class Equipment(str, enum.Enum):
    BODYWEIGHT = "bodyweight"
    DUMBBELL = "dumbbell"
    BARBELL = "barbell"
    MACHINE = "machine"
    CABLE = "cable"
    KETTLEBELL = "kettlebell"
    BAND = "band"
    BENCH = "bench"
    NONE = "none"

class Difficulty(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    muscle_group = Column(SAEnum(MuscleGroup, native_enum=False), nullable=False)
    equipment = Column(SAEnum(Equipment, native_enum=False), nullable=False)
    difficulty = Column(SAEnum(Difficulty, native_enum=False), nullable=False)
    instructions = Column(Text, nullable=True)
    video_url = Column(String(512), nullable=True)
    image_url = Column(String(512), nullable=True)
    contraindications = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session_exercises = relationship("SessionExercise", back_populates="exercise")
