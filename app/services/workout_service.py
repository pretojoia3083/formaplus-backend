import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.workout import (
    WorkoutPlan,
    WorkoutSession,
    SessionExercise,
    ExerciseLog,
    WorkoutPlanStatus,
    WorkoutSessionStatus,
    DifficultyFeedback,
)
from app.models.exercise import Exercise
from app.models.user import User
from app.models.goal import Goal, GoalType
from app.models.preference import Preference
from app.models.profile import Profile, ExperienceLevel
from app.services.ai_engine import AIEngine

logger = logging.getLogger(__name__)

class WorkoutService:
    def __init__(self):
        self.ai_engine = AIEngine()
    
    def generate_workout_plan(
        self,
        db: Session,
        user_id: int
    ) -> WorkoutPlan:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("Usuário não encontrado")
        
        goal = db.query(Goal).filter(Goal.user_id == user_id).first()
        preferences = db.query(Preference).filter(Preference.user_id == user_id).first()
        
        if not goal:
            goal = Goal(user_id=user_id, goal_type=GoalType.GAIN_MUSCLE)
            db.add(goal)
            db.flush()
        if not preferences:
            preferences = Preference(user_id=user_id, training_days_per_week=3, session_duration_min=45)
            db.add(preferences)
            db.flush()
        
        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        if not profile:
            profile = Profile(user_id=user_id, experience_level=ExperienceLevel.BEGINNER)
            db.add(profile)
            db.flush()
        
        exercises = db.query(Exercise).all()
        available_exercises = [
            {
                "id": ex.id,
                "name": ex.name,
                "muscle_group": ex.muscle_group.value,
                "equipment": ex.equipment.value,
                "difficulty": ex.difficulty.value,
                "instructions": ex.instructions
            }
            for ex in exercises
        ]
        
        user_data = {
            "goal": goal.goal_type.value,
            "experience_level": user.profile.experience_level.value if user.profile else "beginner",
            "training_days": preferences.training_days_per_week or 3,
            "session_duration": preferences.session_duration_min or 45,
            "location": preferences.location.value if preferences.location else "gym",
            "available_equipment": preferences.available_equipment or [],
            "restrictions": []
        }
        
        ai_result = self.ai_engine.generate_workout_plan(
            db=db,
            user_data=user_data,
            available_exercises=available_exercises
        )
        
        workout_plan = WorkoutPlan(
            user_id=user_id,
            goal_snapshot={
                "goal_type": goal.goal_type.value,
                "target_weight_kg": goal.target_weight_kg,
                "target_date": str(goal.target_date) if goal.target_date else None,
                "preferences": {
                    "training_days": preferences.training_days_per_week,
                    "session_duration": preferences.session_duration_min,
                    "location": preferences.location.value if preferences.location else None,
                    "available_equipment": preferences.available_equipment
                }
            },
            status=WorkoutPlanStatus.ACTIVE,
            version=1
        )
        db.add(workout_plan)
        db.flush()
        
        day_mapping = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2,
            "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
        }
        
        for day_data in ai_result.get("workout", []):
            day_name = day_data.get("day", "Monday")
            focus = day_data.get("focus", "Full Body")
            
            today = datetime.now()
            days_ahead = (day_mapping.get(day_name, 0) - today.weekday()) % 7
            scheduled_date = today + timedelta(days=days_ahead)
            if days_ahead == 0 and today.hour > 12:
                scheduled_date += timedelta(days=7)
            
            workout_session = WorkoutSession(
                workout_plan_id=workout_plan.id,
                day_of_week=day_name,
                focus=focus,
                scheduled_date=scheduled_date,
                status=WorkoutSessionStatus.PENDING
            )
            db.add(workout_session)
            db.flush()
            
            for idx, exercise_data in enumerate(day_data.get("exercises", [])):
                exercise_id = exercise_data.get("exercise_id")
                if not exercise_id:
                    continue
                
                exercise_exists = db.query(Exercise).filter(Exercise.id == exercise_id).first()
                if not exercise_exists:
                    logger.warning(f"Exercício {exercise_id} não encontrado, pulando...")
                    continue
                
                session_exercise = SessionExercise(
                    workout_session_id=workout_session.id,
                    exercise_id=exercise_id,
                    sets=exercise_data.get("sets", 3),
                    reps=exercise_data.get("reps", 10),
                    rest_seconds=exercise_data.get("rest_seconds", 90),
                    order_index=idx
                )
                db.add(session_exercise)
        
        db.commit()
        db.refresh(workout_plan)
        
        logger.info(f"Plano de treino gerado para usuário {user_id}, ID: {workout_plan.id}")
        return workout_plan
    
    def get_active_plan(
        self,
        db: Session,
        user_id: int
    ) -> Optional[WorkoutPlan]:
        return db.query(WorkoutPlan).filter(
            WorkoutPlan.user_id == user_id,
            WorkoutPlan.status == WorkoutPlanStatus.ACTIVE
        ).first()
    
    def get_today_workout(
        self,
        db: Session,
        user_id: int
    ) -> Optional[WorkoutSession]:
        today_name = datetime.now().strftime("%A")
        today_date = datetime.now().date()
        
        active_plan = self.get_active_plan(db, user_id)
        if not active_plan:
            return None
        
        session = db.query(WorkoutSession).filter(
            WorkoutSession.workout_plan_id == active_plan.id,
            WorkoutSession.day_of_week == today_name,
            WorkoutSession.status.in_([WorkoutSessionStatus.PENDING, WorkoutSessionStatus.IN_PROGRESS])
        ).first()
        
        if not session:
            session = db.query(WorkoutSession).filter(
                WorkoutSession.workout_plan_id == active_plan.id,
                WorkoutSession.scheduled_date.cast == today_date,
                WorkoutSession.status.in_([WorkoutSessionStatus.PENDING, WorkoutSessionStatus.IN_PROGRESS])
            ).first()
        
        if session:
            db.refresh(session)
        
        return session
    
    def start_workout(
        self,
        db: Session,
        session_id: int,
        user_id: int
    ) -> WorkoutSession:
        session = db.query(WorkoutSession).filter(
            WorkoutSession.id == session_id,
            WorkoutSession.workout_plan.has(user_id=user_id)
        ).first()
        
        if not session:
            raise ValueError("Sessão não encontrada")
        
        if session.status != WorkoutSessionStatus.PENDING:
            raise ValueError(f"Status atual: {session.status}, não pode iniciar")
        
        session.status = WorkoutSessionStatus.IN_PROGRESS
        db.commit()
        db.refresh(session)
        
        return session
    
    def log_exercise(
        self,
        db: Session,
        session_exercise_id: int,
        user_id: int,
        weight_kg: Optional[float] = None,
        reps_done: Optional[int] = None,
        difficulty_feedback: Optional[str] = None
    ) -> ExerciseLog:
        session_exercise = db.query(SessionExercise).filter(
            SessionExercise.id == session_exercise_id
        ).first()
        
        if not session_exercise:
            raise ValueError("Exercício não encontrado")
        
        workout_session = db.query(WorkoutSession).filter(
            WorkoutSession.id == session_exercise.workout_session_id
        ).first()
        
        if not workout_session or workout_session.workout_plan.user_id != user_id:
            raise ValueError("Este exercício não pertence ao usuário")
        
        log = ExerciseLog(
            session_exercise_id=session_exercise_id,
            weight_kg=weight_kg,
            reps_done=reps_done,
            difficulty_feedback=DifficultyFeedback(difficulty_feedback) if difficulty_feedback else None
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        
        return log
    
    def finish_workout(
        self,
        db: Session,
        session_id: int,
        user_id: int
    ) -> WorkoutSession:
        session = db.query(WorkoutSession).filter(
            WorkoutSession.id == session_id,
            WorkoutSession.workout_plan.has(user_id=user_id)
        ).first()
        
        if not session:
            raise ValueError("Sessão não encontrada")
        
        if session.status not in [WorkoutSessionStatus.IN_PROGRESS, WorkoutSessionStatus.PENDING]:
            raise ValueError(f"Status atual: {session.status}, não pode finalizar")
        
        session.status = WorkoutSessionStatus.COMPLETED
        db.commit()
        db.refresh(session)
        
        return session
    
    def adapt_workout(
        self,
        db: Session,
        session_id: int,
        available_minutes: int,
        user_id: int
    ) -> Dict[str, Any]:
        session = db.query(WorkoutSession).filter(
            WorkoutSession.id == session_id,
            WorkoutSession.workout_plan.has(user_id=user_id)
        ).first()
        
        if not session:
            raise ValueError("Sessão não encontrada")
        
        session_exercises = db.query(SessionExercise).filter(
            SessionExercise.workout_session_id == session_id
        ).order_by(SessionExercise.order_index).all()
        
        original_session = {
            "day": session.day_of_week,
            "focus": session.focus,
            "exercises": [
                {
                    "exercise_id": se.exercise_id,
                    "sets": se.sets,
                    "reps": se.reps,
                    "rest_seconds": se.rest_seconds
                }
                for se in session_exercises
            ]
        }
        
        exercises = db.query(Exercise).all()
        available_exercises = [
            {
                "id": ex.id,
                "name": ex.name,
                "muscle_group": ex.muscle_group.value,
                "equipment": ex.equipment.value
            }
            for ex in exercises
        ]
        
        adapted = self.ai_engine.adapt_workout(
            original_session=original_session,
            available_minutes=available_minutes,
            available_exercises=available_exercises,
            session_focus=session.focus or "Full Body"
        )
        
        for se in session_exercises:
            db.delete(se)
        
        for idx, exercise_data in enumerate(adapted.get("exercises", [])):
            exercise_id = exercise_data.get("exercise_id")
            if not exercise_id:
                continue
            
            new_se = SessionExercise(
                workout_session_id=session_id,
                exercise_id=exercise_id,
                sets=exercise_data.get("sets", 3),
                reps=exercise_data.get("reps", 10),
                rest_seconds=exercise_data.get("rest_seconds", 60),
                order_index=idx
            )
            db.add(new_se)
        
        db.commit()
        
        return {
            "adapted_session": adapted,
            "message": f"Treino adaptado para {available_minutes} minutos!"
        }
    
    def substitute_exercise(
        self,
        db: Session,
        session_exercise_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        session_exercise = db.query(SessionExercise).filter(
            SessionExercise.id == session_exercise_id
        ).first()
        
        if not session_exercise:
            raise ValueError("Exercício não encontrado")
        
        workout_session = db.query(WorkoutSession).filter(
            WorkoutSession.id == session_exercise.workout_session_id
        ).first()
        
        if not workout_session or workout_session.workout_plan.user_id != user_id:
            raise ValueError("Este exercício não pertence ao usuário")
        
        original_exercise = db.query(Exercise).filter(
            Exercise.id == session_exercise.exercise_id
        ).first()
        
        if not original_exercise:
            raise ValueError("Exercício original não encontrado")
        
        preferences = db.query(Preference).filter(Preference.user_id == user_id).first()
        equipment = preferences.available_equipment if preferences else []
        
        experience = "beginner"
        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        if profile and profile.experience_level:
            experience = profile.experience_level.value
        
        available_exercises = db.query(Exercise).filter(
            Exercise.id != original_exercise.id,
            Exercise.muscle_group == original_exercise.muscle_group,
            Exercise.difficulty.in_(["beginner", experience])
        ).all()
        
        if not available_exercises:
            raise ValueError("Nenhum exercício substituto disponível")
        
        available_list = [
            {
                "id": ex.id,
                "name": ex.name,
                "muscle_group": ex.muscle_group.value,
                "equipment": ex.equipment.value,
                "difficulty": ex.difficulty.value
            }
            for ex in available_exercises
        ]
        
        substitution = self.ai_engine.substitute_exercise(
            exercise_id=original_exercise.id,
            exercise_name=original_exercise.name,
            muscle_group=original_exercise.muscle_group.value,
            available_equipment=equipment or [],
            experience_level=experience,
            available_exercises=available_list
        )
        
        replacement_id = substitution.get("replacement_exercise_id")
        if not replacement_id:
            raise ValueError("IA não encontrou substituto válido")
        
        session_exercise.exercise_id = replacement_id
        db.commit()
        db.refresh(session_exercise)
        
        new_exercise = db.query(Exercise).filter(Exercise.id == replacement_id).first()
        
        return {
            "replacement_exercise_id": replacement_id,
            "new_exercise_name": new_exercise.name if new_exercise else "Exercício",
            "reason": substitution.get("reason", "Exercício substituído com sucesso!")
        }
