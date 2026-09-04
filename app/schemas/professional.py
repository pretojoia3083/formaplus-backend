from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List, Dict
from app.models.professional import ProfessionalType, ProfessionalStatus, ServiceType, SessionStatus

class ProfessionalCreate(BaseModel):
    user_id: int
    professional_type: ProfessionalType
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: Optional[str] = None
    bio: Optional[str] = None
    specialties: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    experience_years: Optional[int] = Field(None, ge=0)
    education: Optional[List[Dict[str, str]]] = None
    service_type: ServiceType = ServiceType.BOTH
    service_locations: Optional[List[str]] = None
    online_platforms: Optional[List[str]] = None
    price_per_hour_brl: Optional[float] = Field(None, ge=0)
    price_per_session_brl: Optional[float] = Field(None, ge=0)
    package_prices: Optional[Dict[str, float]] = None
    profile_image_url: Optional[str] = None
    gallery_images: Optional[List[str]] = None
    video_intro_url: Optional[str] = None
    availability_schedule: Optional[Dict] = None
    timezone: str = "America/Sao_Paulo"

class ProfessionalUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = None
    bio: Optional[str] = None
    specialties: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    experience_years: Optional[int] = Field(None, ge=0)
    education: Optional[List[Dict[str, str]]] = None
    service_type: Optional[ServiceType] = None
    service_locations: Optional[List[str]] = None
    online_platforms: Optional[List[str]] = None
    price_per_hour_brl: Optional[float] = Field(None, ge=0)
    price_per_session_brl: Optional[float] = Field(None, ge=0)
    package_prices: Optional[Dict[str, float]] = None
    profile_image_url: Optional[str] = None
    gallery_images: Optional[List[str]] = None
    video_intro_url: Optional[str] = None
    availability_schedule: Optional[Dict] = None
    timezone: Optional[str] = None
    status: Optional[ProfessionalStatus] = None

class ProfessionalResponse(BaseModel):
    id: int
    user_id: int
    professional_type: ProfessionalType
    status: ProfessionalStatus
    name: str
    email: str
    phone: Optional[str] = None
    bio: Optional[str] = None
    specialties: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    experience_years: Optional[int] = None
    education: Optional[List[Dict[str, str]]] = None
    service_type: ServiceType
    service_locations: Optional[List[str]] = None
    online_platforms: Optional[List[str]] = None
    price_per_hour_brl: Optional[float] = None
    price_per_session_brl: Optional[float] = None
    package_prices: Optional[Dict[str, float]] = None
    rating_avg: float
    rating_count: int
    profile_image_url: Optional[str] = None
    gallery_images: Optional[List[str]] = None
    video_intro_url: Optional[str] = None
    availability_schedule: Optional[Dict] = None
    timezone: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProfessionalListResponse(BaseModel):
    id: int
    name: str
    professional_type: ProfessionalType
    profile_image_url: Optional[str] = None
    specialties: Optional[List[str]] = None
    rating_avg: float
    rating_count: int
    price_per_session_brl: Optional[float] = None
    experience_years: Optional[int] = None

class ProfessionalServiceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    duration_minutes: int = Field(60, ge=15, le=180)
    price_brl: float = Field(..., ge=0)
    is_active: bool = True

class ProfessionalServiceResponse(BaseModel):
    id: int
    professional_id: int
    name: str
    description: Optional[str] = None
    duration_minutes: int
    price_brl: float
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProfessionalAvailabilityCreate(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)
    start_time: str
    end_time: str
    is_available: bool = True

class ProfessionalAvailabilityResponse(BaseModel):
    id: int
    professional_id: int
    day_of_week: int
    start_time: str
    end_time: str
    is_available: bool
    
    class Config:
        from_attributes = True

class ProfessionalSessionCreate(BaseModel):
    professional_id: int
    service_id: Optional[int] = None
    scheduled_date: datetime
    session_type: str
    location: Optional[str] = None
    notes: Optional[str] = None

class ProfessionalSessionResponse(BaseModel):
    id: int
    professional_id: int
    user_id: int
    service_id: Optional[int] = None
    scheduled_date: datetime
    scheduled_end: Optional[datetime] = None
    status: SessionStatus
    session_type: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    user_feedback: Optional[str] = None
    user_rating: Optional[int] = None
    price_brl: float
    payment_status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProfessionalSessionUpdate(BaseModel):
    status: Optional[SessionStatus] = None
    user_feedback: Optional[str] = None
    user_rating: Optional[int] = Field(None, ge=1, le=5)
    user_rating_comment: Optional[str] = None
    professional_notes: Optional[str] = None

class ProfessionalReviewCreate(BaseModel):
    professional_id: int
    session_id: Optional[int] = None
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class ProfessionalReviewResponse(BaseModel):
    id: int
    professional_id: int
    user_id: int
    session_id: Optional[int] = None
    rating: int
    comment: Optional[str] = None
    is_verified: bool
    created_at: datetime
    user_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class ProfessionalSearchParams(BaseModel):
    professional_type: Optional[ProfessionalType] = None
    service_type: Optional[ServiceType] = None
    specialties: Optional[List[str]] = None
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    max_price: Optional[float] = Field(None, ge=0)
    experience_min_years: Optional[int] = Field(None, ge=0)
    location: Optional[str] = None
    availability_day: Optional[int] = Field(None, ge=0, le=6)
    availability_time: Optional[str] = None
    limit: int = 20
    offset: int = 0
