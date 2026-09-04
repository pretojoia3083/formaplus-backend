from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.models.preference import Location

class PreferenceCreate(BaseModel):
    training_days_per_week: Optional[int] = Field(None, ge=1, le=7)
    session_duration_min: Optional[int] = Field(None, ge=10, le=180)
    location: Optional[Location] = None
    available_equipment: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    disliked_foods: Optional[List[str]] = None
    liked_foods: Optional[List[str]] = None

class PreferenceUpdate(BaseModel):
    training_days_per_week: Optional[int] = Field(None, ge=1, le=7)
    session_duration_min: Optional[int] = Field(None, ge=10, le=180)
    location: Optional[Location] = None
    available_equipment: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    disliked_foods: Optional[List[str]] = None
    liked_foods: Optional[List[str]] = None

class PreferenceResponse(BaseModel):
    id: int
    user_id: int
    training_days_per_week: Optional[int] = None
    session_duration_min: Optional[int] = None
    location: Optional[Location] = None
    available_equipment: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    disliked_foods: Optional[List[str]] = None
    liked_foods: Optional[List[str]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
