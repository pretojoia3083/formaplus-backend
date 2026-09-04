from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.user import PlanType
from app.models.subscription import SubscriptionStatus, PaymentStatus

class SubscriptionCreate(BaseModel):
    user_id: int
    plan: PlanType
    current_period_end: datetime
    provider_subscription_id: Optional[str] = None

class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    plan: PlanType
    status: SubscriptionStatus
    current_period_end: datetime
    provider_subscription_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class PaymentCreate(BaseModel):
    subscription_id: int
    amount: float = Field(..., ge=0)
    provider_ref: Optional[str] = None

class PaymentResponse(BaseModel):
    id: int
    subscription_id: int
    amount: float
    status: PaymentStatus
    provider_ref: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class SubscriptionPlan(BaseModel):
    plan_type: PlanType
    price_brl: float
    features: list
