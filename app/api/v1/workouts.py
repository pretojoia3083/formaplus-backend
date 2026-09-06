from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_plan_type
from app.models.user import User
from app.models.workout import WorkoutSession, SessionExercise, WorkoutPlan
from app.schemas.workout import (
    WorkoutPlanResponse,
    WorkoutSessionResponse,
    ExerciseLogCreate,
    ExerciseLogResponse,
    WorkoutAdaptationRequest,
    WorkoutAdaptationResponse,
    ExerciseSubstitutionRequest,
    ExerciseSubstitutionResponse,
    WorkoutGenerationResponse,
)
from app.services.workout_service import WorkoutService

router = APIRouter()
workout_service = WorkoutService()

@router.post("/workouts/generate", response_model=WorkoutPlanResponse)
async def generate_workout_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        plan = workout_service.generate_workout_plan(db=db, user_id=current_user.id)
        db.refresh(plan)
        return plan
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/workouts/active", response_model=Optional[WorkoutPlanResponse])
async def get_active_workout_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = workout_service.get_active_plan(db=db, user_id=current_user.id)
    return plan

@router.get("/workouts/today", response_model=Optional[WorkoutSessionResponse])
async def get_today_workout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = workout_service.get_today_workout(db=db, user_id=current_user.id)
    return session

@router.post("/workouts/sessions/{session_id}/start")
async def start_workout(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        session = workout_service.start_workout(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )
        return {
            "message": "Treino iniciado!",
            "session_id": session.id,
            "status": session.status.value
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/workouts/exercises/{session_exercise_id}/log", response_model=ExerciseLogResponse)
async def log_exercise(
    session_exercise_id: int,
    log_data: ExerciseLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        log = workout_service.log_exercise(
            db=db,
            session_exercise_id=session_exercise_id,
            user_id=current_user.id,
            weight_kg=log_data.weight_kg,
            reps_done=log_data.reps_done,
            difficulty_feedback=log_data.difficulty_feedback
        )
        return log
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/workouts/sessions/{session_id}/finish")
async def finish_workout(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        session = workout_service.finish_workout(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )
        return {
            "message": "Treino finalizado!",
            "session_id": session.id,
            "status": session.status.value
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/workouts/sessions/{session_id}/adapt", response_model=WorkoutAdaptationResponse)
async def adapt_workout(
    session_id: int,
    request: WorkoutAdaptationRequest,
    current_user: User = Depends(require_plan_type("pro")),
    db: Session = Depends(get_db)
):
    try:
        result = workout_service.adapt_workout(
            db=db,
            session_id=session_id,
            available_minutes=request.available_minutes,
            user_id=current_user.id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/workouts/exercises/{session_exercise_id}/substitute", response_model=ExerciseSubstitutionResponse)
async def substitute_exercise(
    session_exercise_id: int,
    current_user: User = Depends(require_plan_type("pro")),
    db: Session = Depends(get_db)
):
    try:
        result = workout_service.substitute_exercise(
            db=db,
            session_exercise_id=session_exercise_id,
            user_id=current_user.id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/workouts/history")
async def get_workout_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 30,
    offset: int = 0
):
    logs = db.query(WorkoutSession).filter(
        WorkoutSession.workout_plan.has(user_id=current_user.id),
        WorkoutSession.status == "completed"
    ).order_by(
        WorkoutSession.scheduled_date.desc()
    ).offset(offset).limit(limit).all()
    
    return {"total": len(logs), "sessions": logs}
