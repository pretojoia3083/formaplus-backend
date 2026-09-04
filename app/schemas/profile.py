from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.profile import Sex, ActivityLevel, ExperienceLevel

class ProfileCreate(BaseModel):
    age: Optional[int] = Field(None, ge=10, le=120)
    sex: Optional[Sex] = None
    height_cm: Optional[float] = Field(None, ge=50, le=300)
    weight_kg: Optional[float] = Field(None, ge=20, le=500)
    activity_level: Optional[ActivityLevel] = None
    experience_level: Optional[ExperienceLevel] = None

class ProfileUpdate(BaseModel):
    age: Optional[int] = Field(None, ge=10, le=120)
    sex: Optional[Sex] = None
    height_cm: Optional[float] = Field(None, ge=50, le=300)
    weight_kg: Optional[float] = Field(None, ge=20, le=500)
    activity_level: Optional[ActivityLevel] = None
    experience_level: Optional[ExperienceLevel] = None

class ProfileResponse(BaseModel):
    id: int
    user_id: int
    age: Optional[int] = None
    sex: Optional[Sex] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    activity_level: Optional[ActivityLevel] = None
    experience_level: Optional[ExperienceLevel] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
