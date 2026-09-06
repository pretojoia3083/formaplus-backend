from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_plan_type
from app.models.user import User
from app.models.nutrition import Meal, MealLog
from app.schemas.nutrition import (
    MealPlanResponse,
    MealResponse,
    MealLogCreate,
    MealLogResponse,
    MealPlanGenerationResponse,
)
from app.services.nutrition_service import NutritionService

router = APIRouter()
nutrition_service = NutritionService()

@router.post("/nutrition/generate", response_model=MealPlanResponse)
async def generate_meal_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        plan = nutrition_service.generate_meal_plan(db=db, user_id=current_user.id)
        db.refresh(plan)
        return plan
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/nutrition/active", response_model=Optional[MealPlanResponse])
async def get_active_meal_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = nutrition_service.get_active_plan(db=db, user_id=current_user.id)
    return plan

@router.get("/nutrition/today", response_model=List[MealResponse])
async def get_today_meals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    meals = nutrition_service.get_today_meals(db=db, user_id=current_user.id)
    return meals

@router.post("/nutrition/log", response_model=MealLogResponse)
async def log_meal(
    log_data: MealLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        log = nutrition_service.log_meal(
            db=db,
            user_id=current_user.id,
            meal_id=log_data.meal_id,
            meal_type=log_data.meal_type,
            freeform_description=log_data.freeform_description,
            photo_url=log_data.photo_url,
            estimated_calories=log_data.estimated_calories,
            estimated_macros=log_data.estimated_macros,
            confirmed_by_user=log_data.confirmed_by_user
        )
        return log
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/nutrition/estimate-meal")
async def estimate_meal_from_photo(
    description: str,
    current_user: User = Depends(require_plan_type("premium")),
    db: Session = Depends(get_db)
):
    try:
        result = nutrition_service.estimate_meal_from_photo(
            db=db,
            image_description=description
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/nutrition/daily-progress")
async def get_daily_calorie_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        progress = nutrition_service.get_daily_calorie_progress(
            db=db,
            user_id=current_user.id
        )
        return progress
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/nutrition/history")
async def get_meal_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 30,
    offset: int = 0
):
    logs = db.query(MealLog).filter(
        MealLog.user_id == current_user.id
    ).order_by(
        MealLog.logged_at.desc()
    ).offset(offset).limit(limit).all()
    
    return {"total": len(logs), "logs": logs}
