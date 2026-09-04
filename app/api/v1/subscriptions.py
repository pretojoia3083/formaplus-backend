from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.subscription import Subscription, Payment
from app.schemas.subscription import (
    SubscriptionResponse,
    SubscriptionPlan,
    PaymentResponse,
)
from app.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

router = APIRouter()
subscription_service = SubscriptionService()

@router.get("/plans")
async def get_plans():
    plans = subscription_service.get_available_plans()
    return plans

@router.get("/plans/{plan_type}")
async def get_plan(plan_type: str):
    plans = subscription_service.get_available_plans()
    plan = next((p for p in plans if p["plan_type"] == plan_type), None)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plano não encontrado")
    return plan

@router.get("/subscription")
async def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        info = subscription_service.get_subscription_info(db=db, user_id=current_user.id)
        return info
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/subscription/create")
async def create_subscription(
    plan_type: str,
    payment_method_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if plan_type not in ["free", "pro", "premium"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plano inválido")
        
        result = subscription_service.create_subscription(
            db=db,
            user_id=current_user.id,
            plan_type=plan_type,
            payment_method_id=payment_method_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/subscription/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = subscription_service.cancel_subscription(db=db, user_id=current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/subscription/update")
async def update_subscription_plan(
    new_plan: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if new_plan not in ["free", "pro", "premium"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plano inválido")
        
        result = subscription_service.update_subscription_plan(
            db=db,
            user_id=current_user.id,
            new_plan=new_plan
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        if not sig_header:
            raise HTTPException(status_code=400, detail="Missing stripe-signature header")
        
        result = subscription_service.handle_webhook(
            payload=payload,
            sig_header=sig_header
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/payments")
async def get_payment_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 10,
    offset: int = 0
):
    try:
        subscription = db.query(Subscription).filter(
            Subscription.user_id == current_user.id
        ).first()
        
        if not subscription:
            return {"payments": [], "total": 0}
        
        payments = db.query(Payment).filter(
            Payment.subscription_id == subscription.id
        ).order_by(
            Payment.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        total = db.query(Payment).filter(
            Payment.subscription_id == subscription.id
        ).count()
        
        return {
            "payments": payments,
            "total": total
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
