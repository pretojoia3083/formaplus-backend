from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.models.user import User, UserStatus, PlanType
from app.models.profile import Profile, Sex, ActivityLevel, ExperienceLevel
from app.models.goal import Goal, GoalType
from app.models.preference import Preference, Location
from app.schemas.user import UserCreate, UserResponse, Token, LoginRequest

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

@router.get("/me")
async def get_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    goal = db.query(Goal).filter(Goal.user_id == user_id).first()
    preference = db.query(Preference).filter(Preference.user_id == user_id).first()
    
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "plan_type": user.plan_type.value if user.plan_type else "free",
        "has_profile": profile is not None,
        "has_goal": goal is not None,
        "has_preference": preference is not None,
        "onboarding_complete": profile is not None and goal is not None and preference is not None,
    }

@router.post("/onboarding")
async def save_onboarding(
    data: dict,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Save profile
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        profile = Profile(user_id=user_id)
        db.add(profile)
    
    profile.age = data.get("age")
    profile.sex = data.get("sex", "male")
    profile.height_cm = data.get("height_cm")
    profile.weight_kg = data.get("weight_kg")
    profile.activity_level = data.get("activity_level", "moderately_active")
    profile.experience_level = data.get("experience_level", "beginner")
    
    # Save goal
    goal = db.query(Goal).filter(Goal.user_id == user_id).first()
    if not goal:
        goal = Goal(user_id=user_id)
        db.add(goal)
    
    goal.goal_type = data.get("goal_type", "gain_muscle")
    
    # Save preference
    preference = db.query(Preference).filter(Preference.user_id == user_id).first()
    if not preference:
        preference = Preference(user_id=user_id)
        db.add(preference)
    
    preference.training_days_per_week = data.get("training_days_per_week", 3)
    preference.session_duration_min = data.get("session_duration_min", 45)
    preference.location = data.get("location", "gym")
    
    db.commit()
    
    return {"detail": "Onboarding complete!", "onboarding_complete": True}

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email,
            password_hash=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            plan_type=PlanType.FREE,
            status=UserStatus.ACTIVE
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Register error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login/json", response_model=Token)
async def login_json(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
    }

@router.post("/reset-account")
async def reset_account(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    from app.models.workout import WorkoutPlan, WorkoutSession, SessionExercise, ExerciseLog
    from app.models.nutrition import MealPlan, Meal, MealItem, MealLog
    from app.models.progress import WeightLog, Measurement, WaterLog, StepLog
    from app.models.ai import AIConversation, AIMessage
    from app.models.profile import Profile
    from app.models.goal import Goal
    from app.models.preference import Preference
    
    for model in [ExerciseLog, SessionExercise, WorkoutSession, WorkoutPlan,
                  MealLog, MealItem, Meal, MealPlan,
                  WeightLog, Measurement, WaterLog, StepLog,
                  AIMessage, AIConversation,
                  Profile, Goal, Preference]:
        db.query(model).filter(model.user_id == user_id).delete(synchronize_session=False)
    
    db.commit()
    return {"detail": "Account data reset successfully"}

@router.delete("/delete-account")
async def delete_account(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        from sqlalchemy import text
        db.execute(text("DELETE FROM exercise_logs WHERE session_exercise_id IN (SELECT se.id FROM session_exercises se JOIN workout_sessions ws ON se.workout_session_id = ws.id JOIN workout_plans wp ON ws.workout_plan_id = wp.id WHERE wp.user_id = :uid)"), {"uid": user_id})
        db.execute(text("DELETE FROM session_exercises WHERE workout_session_id IN (SELECT ws.id FROM workout_sessions ws JOIN workout_plans wp ON ws.workout_plan_id = wp.id WHERE wp.user_id = :uid)"), {"uid": user_id})
        db.execute(text("DELETE FROM workout_sessions WHERE workout_plan_id IN (SELECT id FROM workout_plans WHERE user_id = :uid)"), {"uid": user_id})
        db.execute(text("DELETE FROM workout_plans WHERE user_id = :uid"), {"uid": user_id})
        db.execute(text("DELETE FROM meal_items WHERE meal_id IN (SELECT m.id FROM meals m JOIN meal_plans mp ON m.meal_plan_id = mp.id WHERE mp.user_id = :uid)"), {"uid": user_id})
        db.execute(text("DELETE FROM meal_logs WHERE user_id = :uid"), {"uid": user_id})
        db.execute(text("DELETE FROM meals WHERE meal_plan_id IN (SELECT id FROM meal_plans WHERE user_id = :uid)"), {"uid": user_id})
        db.execute(text("DELETE FROM meal_plans WHERE user_id = :uid"), {"uid": user_id})
        db.execute(text("DELETE FROM weight_logs WHERE user_id = :uid"), {"uid": user_id})
        db.execute(text("DELETE FROM measurements WHERE user_id = :uid"), {"uid": user_id})
        db.execute(text("DELETE FROM water_logs WHERE user_id = :uid"), {"uid": user_id})
        db.execute(text("DELETE FROM step_logs WHERE user_id = :uid"), {"uid": user_id})
        db.execute(text("DELETE FROM ai_messages WHERE conversation_id IN (SELECT id FROM ai_conversations WHERE user_id = :uid)"), {"uid": user_id})
        db.execute(text("DELETE FROM ai_conversations WHERE user_id = :uid"), {"uid": user_id})
        db.execute(text("DELETE FROM profiles WHERE user_id = :uid"), {"uid": user_id})
        db.execute(text("DELETE FROM goals WHERE user_id = :uid"), {"uid": user_id})
        db.execute(text("DELETE FROM preferences WHERE user_id = :uid"), {"uid": user_id})
        db.execute(text("DELETE FROM payments WHERE subscription_id IN (SELECT id FROM subscriptions WHERE user_id = :uid)"), {"uid": user_id})
        db.execute(text("DELETE FROM subscriptions WHERE user_id = :uid"), {"uid": user_id})
        db.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
    return {"detail": "Conta excluída com sucesso"}

@router.post("/refresh", response_model=Token)
async def refresh_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    new_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    return {"access_token": new_token, "token_type": "bearer"}
