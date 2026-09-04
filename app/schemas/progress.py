from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List, Dict

class WeightLogCreate(BaseModel):
    weight_kg: float = Field(..., ge=20, le=500)

class WeightLogResponse(BaseModel):
    id: int
    user_id: int
    weight_kg: float
    logged_at: datetime
    
    class Config:
        from_attributes = True

class MeasurementCreate(BaseModel):
    waist_cm: Optional[float] = Field(None, ge=20, le=300)
    hip_cm: Optional[float] = Field(None, ge=20, le=300)
    arm_cm: Optional[float] = Field(None, ge=10, le=100)

class MeasurementResponse(BaseModel):
    id: int
    user_id: int
    waist_cm: Optional[float] = None
    hip_cm: Optional[float] = None
    arm_cm: Optional[float] = None
    logged_at: datetime
    
    class Config:
        from_attributes = True

class WaterLogCreate(BaseModel):
    amount_ml: float = Field(..., ge=0, le=10000)

class WaterLogResponse(BaseModel):
    id: int
    user_id: int
    amount_ml: float
    logged_at: datetime
    
    class Config:
        from_attributes = True

class StepLogCreate(BaseModel):
    steps: int = Field(..., ge=0)
    date: date

class StepLogResponse(BaseModel):
    id: int
    user_id: int
    steps: int
    date: date
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProgressSummaryRequest(BaseModel):
    user_id: int
    weight_history: List[Dict]
    measurements_history: List[Dict]
    workout_adherence_pct: float
    avg_difficulty_feedback: str

class ProgressSummaryResponse(BaseModel):
    summary_text: str
    trend: str
