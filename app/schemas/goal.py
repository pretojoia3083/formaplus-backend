from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.goal import GoalType

class GoalCreate(BaseModel):
    goal_type: GoalType
    target_weight_kg: Optional[float] = Field(None, ge=20, le=500)
    target_date: Optional[datetime] = None

class GoalUpdate(BaseModel):
    goal_type: Optional[GoalType] = None
    target_weight_kg: Optional[float] = Field(None, ge=20, le=500)
    target_date: Optional[datetime] = None

class GoalResponse(BaseModel):
    id: int
    user_id: int
    goal_type: GoalType
    target_weight_kg: Optional[float] = None
    target_date: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
