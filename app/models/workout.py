from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, JSON, Enum as SAEnum, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class WorkoutPlanStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class WorkoutSessionStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"

class DifficultyFeedback(str, enum.Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    VERY_HARD = "very_hard"

class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    goal_snapshot = Column(JSON, nullable=False)
    status = Column(SAEnum(WorkoutPlanStatus, native_enum=False), default=WorkoutPlanStatus.ACTIVE)
    version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="workout_plans")
    sessions = relationship("WorkoutSession", back_populates="workout_plan")

class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id = Column(Integer, primary_key=True, index=True)
    workout_plan_id = Column(Integer, ForeignKey("workout_plans.id"), nullable=False)
    day_of_week = Column(String(20), nullable=False)
    focus = Column(String(100), nullable=True)
    scheduled_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(SAEnum(WorkoutSessionStatus, native_enum=False), default=WorkoutSessionStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    workout_plan = relationship("WorkoutPlan", back_populates="sessions")
    session_exercises = relationship("SessionExercise", back_populates="workout_session")

class SessionExercise(Base):
    __tablename__ = "session_exercises"

    id = Column(Integer, primary_key=True, index=True)
    workout_session_id = Column(Integer, ForeignKey("workout_sessions.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    sets = Column(Integer, nullable=False)
    reps = Column(Integer, nullable=False)
    rest_seconds = Column(Integer, nullable=False)
    order_index = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    workout_session = relationship("WorkoutSession", back_populates="session_exercises")
    exercise = relationship("Exercise", back_populates="session_exercises")
    logs = relationship("ExerciseLog", back_populates="session_exercise")

class ExerciseLog(Base):
    __tablename__ = "exercise_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_exercise_id = Column(Integer, ForeignKey("session_exercises.id"), nullable=False)
    weight_kg = Column(Float, nullable=True)
    reps_done = Column(Integer, nullable=True)
    difficulty_feedback = Column(SAEnum(DifficultyFeedback, native_enum=False), nullable=True)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session_exercise = relationship("SessionExercise", back_populates="logs")
