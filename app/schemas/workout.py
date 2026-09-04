from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.models.workout import WorkoutPlanStatus, WorkoutSessionStatus, DifficultyFeedback
from app.models.exercise import MuscleGroup, Equipment, Difficulty

class ExerciseResponse(BaseModel):
    id: int
    name: str
    muscle_group: MuscleGroup
    equipment: Equipment
    difficulty: Difficulty
    instructions: Optional[str] = None
    video_url: Optional[str] = None
    image_url: Optional[str] = None
    contraindications: Optional[List[str]] = None
    
    class Config:
        from_attributes = True

class SessionExerciseCreate(BaseModel):
    exercise_id: int
    sets: int = Field(..., ge=1, le=10)
    reps: int = Field(..., ge=1, le=50)
    rest_seconds: int = Field(..., ge=10, le=300)
    order_index: int

class SessionExerciseResponse(BaseModel):
    id: int
    exercise_id: int
    exercise: Optional[ExerciseResponse] = None
    sets: int
    reps: int
    rest_seconds: int
    order_index: int
    
    class Config:
        from_attributes = True

class WorkoutSessionResponse(BaseModel):
    id: int
    workout_plan_id: int
    day_of_week: str
    focus: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    status: WorkoutSessionStatus
    session_exercises: List[SessionExerciseResponse] = []
    created_at: datetime
    
    class Config:
        from_attributes = True

class WorkoutPlanCreate(BaseModel):
    goal_snapshot: dict
    status: WorkoutPlanStatus = WorkoutPlanStatus.ACTIVE
    version: int = 1

class WorkoutPlanResponse(BaseModel):
    id: int
    user_id: int
    goal_snapshot: dict
    status: WorkoutPlanStatus
    version: int
    sessions: List[WorkoutSessionResponse] = []
    created_at: datetime
    
    class Config:
        from_attributes = True

class ExerciseLogCreate(BaseModel):
    session_exercise_id: int
    weight_kg: Optional[float] = Field(None, ge=0)
    reps_done: Optional[int] = Field(None, ge=0)
    difficulty_feedback: Optional[DifficultyFeedback] = None

class ExerciseLogResponse(BaseModel):
    id: int
    session_exercise_id: int
    weight_kg: Optional[float] = None
    reps_done: Optional[int] = None
    difficulty_feedback: Optional[DifficultyFeedback] = None
    completed_at: datetime
    
    class Config:
        from_attributes = True

class WorkoutGenerationRequest(BaseModel):
    user_id: int
    goal: str
    experience_level: str
    training_days: int = Field(..., ge=1, le=7)
    session_duration: int = Field(..., ge=10, le=180)
    location: str
    available_equipment: List[str]
    restrictions: Optional[List[str]] = None

class WorkoutGenerationResponse(BaseModel):
    workout: List[dict]
    message: Optional[str] = None

class WorkoutAdaptationRequest(BaseModel):
    original_session_id: int
    available_minutes: int = Field(..., ge=5, le=180)

class WorkoutAdaptationResponse(BaseModel):
    adapted_session: dict
    message: Optional[str] = None

class ExerciseSubstitutionRequest(BaseModel):
    exercise_id: int
    exercise_name: str
    muscle_group: MuscleGroup
    available_equipment: List[str]
    experience_level: str

class ExerciseSubstitutionResponse(BaseModel):
    replacement_exercise_id: int
    reason: str
