from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_plan_type
from app.models.user import User
from app.models.workout import WorkoutSession, SessionExercise, WorkoutPlan, WorkoutPlanStatus, WorkoutSessionStatus
from app.models.exercise import Exercise
from app.schemas.workout import (
    ExerciseLogCreate,
    ExerciseLogResponse,
    WorkoutAdaptationRequest,
    WorkoutAdaptationResponse,
    ExerciseSubstitutionRequest,
    ExerciseSubstitutionResponse,
)
from app.services.workout_service import WorkoutService

router = APIRouter()
workout_service = WorkoutService()

def serialize_plan(plan: WorkoutPlan, db: Session) -> dict:
    sessions_data = []
    sessions = db.query(WorkoutSession).filter(
        WorkoutSession.workout_plan_id == plan.id
    ).order_by(WorkoutSession.scheduled_date).all()
    
    for s in sessions:
        exercises_data = []
        session_exercises = db.query(SessionExercise).filter(
            SessionExercise.workout_session_id == s.id
        ).order_by(SessionExercise.order_index).all()
        
        for se in session_exercises:
            exercise = db.query(Exercise).filter(Exercise.id == se.exercise_id).first()
            exercises_data.append({
                "id": se.id,
                "exercise_id": se.exercise_id,
                "sets": se.sets,
                "reps": se.reps,
                "rest_seconds": se.rest_seconds,
                "order_index": se.order_index,
                "exercise": {
                    "id": exercise.id,
                    "name": exercise.name,
                    "muscle_group": exercise.muscle_group.value,
                    "equipment": exercise.equipment.value,
                    "difficulty": exercise.difficulty.value,
                    "instructions": exercise.instructions,
                } if exercise else None,
            })
        
        sessions_data.append({
            "id": s.id,
            "workout_plan_id": s.workout_plan_id,
            "day_of_week": s.day_of_week,
            "focus": s.focus,
            "scheduled_date": s.scheduled_date.isoformat() if s.scheduled_date else None,
            "status": s.status.value if s.status else "pending",
            "session_exercises": exercises_data,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })
    
    return {
        "id": plan.id,
        "user_id": plan.user_id,
        "goal_snapshot": plan.goal_snapshot,
        "status": plan.status.value,
        "version": plan.version,
        "sessions": sessions_data,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
    }

@router.post("/workouts/generate")
async def generate_workout_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        plan = workout_service.generate_workout_plan(db=db, user_id=current_user.id)
        return serialize_plan(plan, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/workouts/active")
async def get_active_workout_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = workout_service.get_active_plan(db=db, user_id=current_user.id)
    if not plan:
        return None
    return serialize_plan(plan, db)

@router.get("/workouts/today")
async def get_today_workout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = workout_service.get_today_workout(db=db, user_id=current_user.id)
    if not session:
        return None
    
    exercises_data = []
    session_exercises = db.query(SessionExercise).filter(
        SessionExercise.workout_session_id == session.id
    ).order_by(SessionExercise.order_index).all()
    
    for se in session_exercises:
        exercise = db.query(Exercise).filter(Exercise.id == se.exercise_id).first()
        exercises_data.append({
            "id": se.id,
            "exercise_id": se.exercise_id,
            "sets": se.sets,
            "reps": se.reps,
            "rest_seconds": se.rest_seconds,
            "order_index": se.order_index,
            "exercise": {
                "id": exercise.id,
                "name": exercise.name,
                "muscle_group": exercise.muscle_group.value,
                "equipment": exercise.equipment.value,
                "difficulty": exercise.difficulty.value,
                "instructions": exercise.instructions,
            } if exercise else None,
        })
    
    return {
        "id": session.id,
        "workout_plan_id": session.workout_plan_id,
        "day_of_week": session.day_of_week,
        "focus": session.focus,
        "scheduled_date": session.scheduled_date.isoformat() if session.scheduled_date else None,
        "status": session.status.value,
        "session_exercises": exercises_data,
        "created_at": session.created_at.isoformat() if session.created_at else None,
    }

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

@router.post("/workouts/exercises/{session_exercise_id}/log")
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
        return {"id": log.id, "message": "Exercício registrado!"}
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

@router.post("/workouts/sessions/{session_id}/adapt")
async def adapt_workout(
    session_id: int,
    request: WorkoutAdaptationRequest,
    current_user: User = Depends(get_current_user),
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

@router.post("/workouts/exercises/{session_exercise_id}/substitute")
async def substitute_exercise(
    session_exercise_id: int,
    current_user: User = Depends(get_current_user),
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
