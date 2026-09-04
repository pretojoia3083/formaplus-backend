from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.progress import (
    WeightLogCreate,
    WeightLogResponse,
    MeasurementCreate,
    MeasurementResponse,
    WaterLogCreate,
    WaterLogResponse,
    StepLogCreate,
    StepLogResponse,
    ProgressSummaryResponse,
)
from app.services.progress_service import ProgressService

router = APIRouter()
progress_service = ProgressService()

@router.get("/dashboard")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        data = progress_service.get_dashboard_data(db=db, user_id=current_user.id)
        return data
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/progress/summary", response_model=ProgressSummaryResponse)
async def get_progress_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        summary = progress_service.generate_progress_summary(db=db, user_id=current_user.id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/progress/weight", response_model=WeightLogResponse)
async def log_weight(
    log_data: WeightLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        log = progress_service.log_weight(
            db=db,
            user_id=current_user.id,
            weight_kg=log_data.weight_kg
        )
        return log
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/progress/weight", response_model=List[WeightLogResponse])
async def get_weight_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = 30
):
    try:
        logs = progress_service.get_weight_history(
            db=db,
            user_id=current_user.id,
            days=days
        )
        return logs
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/progress/measurements", response_model=MeasurementResponse)
async def log_measurements(
    log_data: MeasurementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        log = progress_service.log_measurements(
            db=db,
            user_id=current_user.id,
            waist_cm=log_data.waist_cm,
            hip_cm=log_data.hip_cm,
            arm_cm=log_data.arm_cm
        )
        return log
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/progress/measurements", response_model=List[MeasurementResponse])
async def get_measurements_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = 30
):
    try:
        logs = progress_service.get_measurements_history(
            db=db,
            user_id=current_user.id,
            days=days
        )
        return logs
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/progress/water", response_model=WaterLogResponse)
async def log_water(
    log_data: WaterLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        log = progress_service.log_water(
            db=db,
            user_id=current_user.id,
            amount_ml=log_data.amount_ml
        )
        return log
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/progress/water/today")
async def get_water_today(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        total = progress_service.get_water_today(db=db, user_id=current_user.id)
        return {"total_ml": total, "target_ml": 2000}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/progress/water/history")
async def get_water_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = 7
):
    try:
        history = progress_service.get_water_history(
            db=db,
            user_id=current_user.id,
            days=days
        )
        return history
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/progress/steps", response_model=StepLogResponse)
async def log_steps(
    log_data: StepLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        log = progress_service.log_steps(
            db=db,
            user_id=current_user.id,
            steps=log_data.steps,
            log_date=log_data.date
        )
        return log
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/progress/steps/today")
async def get_steps_today(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        steps = progress_service.get_steps_today(db=db, user_id=current_user.id)
        return {"steps": steps, "target": 10000}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/progress/streak")
async def get_streak(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        streak = progress_service.calculate_streak(db=db, user_id=current_user.id)
        return {"streak": streak}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
