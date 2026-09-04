import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date, timedelta
from collections import defaultdict

from app.models.progress import (
    WeightLog,
    Measurement,
    WaterLog,
    StepLog,
)
from app.models.workout import WorkoutSession, ExerciseLog, DifficultyFeedback
from app.models.user import User
from app.models.goal import Goal
from app.models.nutrition import MealLog
from app.services.ai_engine import AIEngine

logger = logging.getLogger(__name__)

class ProgressService:
    def __init__(self):
        self.ai_engine = AIEngine()
    
    def log_weight(
        self,
        db: Session,
        user_id: int,
        weight_kg: float
    ) -> WeightLog:
        weight_log = WeightLog(
            user_id=user_id,
            weight_kg=weight_kg
        )
        db.add(weight_log)
        db.commit()
        db.refresh(weight_log)
        
        return weight_log
    
    def get_weight_history(
        self,
        db: Session,
        user_id: int,
        days: int = 30
    ) -> List[WeightLog]:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        logs = db.query(WeightLog).filter(
            WeightLog.user_id == user_id,
            WeightLog.logged_at >= cutoff_date
        ).order_by(WeightLog.logged_at.asc()).all()
        
        return logs
    
    def get_latest_weight(
        self,
        db: Session,
        user_id: int
    ) -> Optional[WeightLog]:
        return db.query(WeightLog).filter(
            WeightLog.user_id == user_id
        ).order_by(WeightLog.logged_at.desc()).first()
    
    def log_measurements(
        self,
        db: Session,
        user_id: int,
        waist_cm: Optional[float] = None,
        hip_cm: Optional[float] = None,
        arm_cm: Optional[float] = None
    ) -> Measurement:
        measurement = Measurement(
            user_id=user_id,
            waist_cm=waist_cm,
            hip_cm=hip_cm,
            arm_cm=arm_cm
        )
        db.add(measurement)
        db.commit()
        db.refresh(measurement)
        
        return measurement
    
    def get_measurements_history(
        self,
        db: Session,
        user_id: int,
        days: int = 30
    ) -> List[Measurement]:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        logs = db.query(Measurement).filter(
            Measurement.user_id == user_id,
            Measurement.logged_at >= cutoff_date
        ).order_by(Measurement.logged_at.asc()).all()
        
        return logs
    
    def log_water(
        self,
        db: Session,
        user_id: int,
        amount_ml: float
    ) -> WaterLog:
        water_log = WaterLog(
            user_id=user_id,
            amount_ml=amount_ml
        )
        db.add(water_log)
        db.commit()
        db.refresh(water_log)
        
        return water_log
    
    def get_water_today(
        self,
        db: Session,
        user_id: int
    ) -> float:
        today = datetime.now().date()
        
        total = db.query(WaterLog).filter(
            WaterLog.user_id == user_id,
            WaterLog.logged_at.cast == today
        ).with_entities(
            func.sum(WaterLog.amount_ml)
        ).scalar()
        
        return total or 0.0
    
    def get_water_history(
        self,
        db: Session,
        user_id: int,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        results = db.query(
            func.date(WaterLog.logged_at).label('date'),
            func.sum(WaterLog.amount_ml).label('total')
        ).filter(
            WaterLog.user_id == user_id,
            WaterLog.logged_at >= cutoff_date
        ).group_by(
            func.date(WaterLog.logged_at)
        ).order_by(
            func.date(WaterLog.logged_at).asc()
        ).all()
        
        return [
            {"date": str(r.date), "total_ml": float(r.total or 0)}
            for r in results
        ]
    
    def log_steps(
        self,
        db: Session,
        user_id: int,
        steps: int,
        log_date: Optional[date] = None
    ) -> StepLog:
        if log_date is None:
            log_date = date.today()
        
        existing = db.query(StepLog).filter(
            StepLog.user_id == user_id,
            StepLog.date == log_date
        ).first()
        
        if existing:
            existing.steps = steps
            db.commit()
            db.refresh(existing)
            return existing
        
        step_log = StepLog(
            user_id=user_id,
            steps=steps,
            date=log_date
        )
        db.add(step_log)
        db.commit()
        db.refresh(step_log)
        
        return step_log
    
    def get_steps_today(
        self,
        db: Session,
        user_id: int
    ) -> int:
        today = date.today()
        
        log = db.query(StepLog).filter(
            StepLog.user_id == user_id,
            StepLog.date == today
        ).first()
        
        return log.steps if log else 0
    
    def calculate_streak(
        self,
        db: Session,
        user_id: int
    ) -> int:
        completed_sessions = db.query(WorkoutSession).filter(
            WorkoutSession.workout_plan.has(user_id=user_id),
            WorkoutSession.status == "completed"
        ).all()
        
        if not completed_sessions:
            return 0
        
        dates = set()
        for session in completed_sessions:
            if session.scheduled_date:
                dates.add(session.scheduled_date.date())
        
        if not dates:
            return 0
        
        sorted_dates = sorted(dates, reverse=True)
        
        streak = 0
        current_date = date.today()
        
        if current_date not in dates:
            last_date = sorted_dates[0]
            days_diff = (current_date - last_date).days
            if days_diff > 1:
                return 0
            current_date = last_date
        
        for d in sorted_dates:
            if d == current_date:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        
        return streak
    
    def get_dashboard_data(
        self,
        db: Session,
        user_id: int
    ) -> Dict[str, Any]:
        latest_weight = self.get_latest_weight(db, user_id)
        streak = self.calculate_streak(db, user_id)
        water_today = self.get_water_today(db, user_id)
        steps_today = self.get_steps_today(db, user_id)
        
        goal = db.query(Goal).filter(Goal.user_id == user_id).first()
        
        from app.services.workout_service import WorkoutService
        workout_service = WorkoutService()
        today_workout = workout_service.get_today_workout(db, user_id)
        
        from app.services.nutrition_service import NutritionService
        nutrition_service = NutritionService()
        calorie_progress = nutrition_service.get_daily_calorie_progress(db, user_id)
        
        weight_progress = None
        if goal and goal.target_weight_kg and latest_weight:
            initial_weight = db.query(WeightLog).filter(
                WeightLog.user_id == user_id
            ).order_by(WeightLog.logged_at.asc()).first()
            
            if initial_weight:
                total_change = initial_weight.weight_kg - goal.target_weight_kg
                current_change = initial_weight.weight_kg - latest_weight.weight_kg
                weight_progress = {
                    "initial": initial_weight.weight_kg,
                    "current": latest_weight.weight_kg,
                    "target": goal.target_weight_kg,
                    "progress_pct": min(100, (current_change / total_change) * 100) if total_change > 0 else 0
                }
        
        return {
            "greeting": self._get_greeting(),
            "streak": streak,
            "latest_weight": latest_weight.weight_kg if latest_weight else None,
            "weight_progress": weight_progress,
            "today_workout": {
                "has_workout": today_workout is not None,
                "session_id": today_workout.id if today_workout else None,
                "focus": today_workout.focus if today_workout else None,
                "status": today_workout.status.value if today_workout else None
            },
            "calorie_progress": calorie_progress,
            "water_today": water_today,
            "water_target": 2000,
            "steps_today": steps_today,
            "steps_target": 10000,
            "goal": {
                "type": goal.goal_type.value if goal else None,
                "target_weight": goal.target_weight_kg if goal else None
            }
        }
    
    def _get_greeting(self) -> str:
        hour = datetime.now().hour
        if hour < 12:
            return "Bom dia"
        elif hour < 18:
            return "Boa tarde"
        else:
            return "Boa noite"
    
    def generate_progress_summary(
        self,
        db: Session,
        user_id: int
    ) -> Dict[str, Any]:
        weight_logs = self.get_weight_history(db, user_id, days=30)
        measurements = self.get_measurements_history(db, user_id, days=30)
        
        completed_sessions = db.query(WorkoutSession).filter(
            WorkoutSession.workout_plan.has(user_id=user_id),
            WorkoutSession.status == "completed",
            WorkoutSession.scheduled_date >= datetime.now() - timedelta(days=28)
        ).count()
        
        total_sessions = db.query(WorkoutSession).filter(
            WorkoutSession.workout_plan.has(user_id=user_id),
            WorkoutSession.scheduled_date >= datetime.now() - timedelta(days=28)
        ).count()
        
        adherence = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        feedbacks = db.query(ExerciseLog.difficulty_feedback).join(
            ExerciseLog.session_exercise
        ).filter(
            ExerciseLog.completed_at >= datetime.now() - timedelta(days=28)
        ).all()
        
        avg_feedback = "normal"
        if feedbacks:
            feedback_counts = defaultdict(int)
            for f in feedbacks:
                if f.difficulty_feedback:
                    feedback_counts[f.difficulty_feedback.value] += 1
            if feedback_counts:
                avg_feedback = max(feedback_counts, key=feedback_counts.get)
        
        weight_history = [
            {"date": str(w.logged_at), "weight_kg": w.weight_kg}
            for w in weight_logs[-10:]
        ]
        
        measurements_history = [
            {"date": str(m.logged_at), "waist_cm": m.waist_cm, "hip_cm": m.hip_cm, "arm_cm": m.arm_cm}
            for m in measurements[-10:]
        ]
        
        summary = self.ai_engine.generate_progress_summary(
            weight_history=weight_history,
            measurements_history=measurements_history,
            workout_adherence_pct=adherence,
            avg_difficulty_feedback=avg_feedback
        )
        
        return summary
