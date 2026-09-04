import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.ai import AIConversation, AIMessage, ContextType, Role
from app.services.ai_engine import AIEngine
from app.services.risk_classifier import RiskClassifier

logger = logging.getLogger(__name__)

class CoachService:
    def __init__(self):
        self.ai_engine = AIEngine()
        self.risk_classifier = RiskClassifier()
    
    def process_message(
        self,
        db: Session,
        user_id: int,
        user_message: str,
        conversation_id: Optional[int] = None
    ) -> Dict[str, Any]:
        classification = self.risk_classifier.classify(user_message)
        
        conversation = self._get_or_create_conversation(db, user_id, conversation_id)
        
        user_message_obj = AIMessage(
            conversation_id=conversation.id,
            role=Role.USER,
            content=user_message,
            flagged_reason=classification.get("reason") if classification.get("category") != "safe" else None
        )
        db.add(user_message_obj)
        db.commit()
        
        if self.risk_classifier.is_safe(classification):
            context = self._build_coach_context(db, user_id)
            response_content = self.ai_engine.get_coach_response(user_message, context)
        else:
            response_content = self.risk_classifier.get_risk_response(classification)
        
        assistant_message = AIMessage(
            conversation_id=conversation.id,
            role=Role.ASSISTANT,
            content=response_content
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        
        return {
            "response": response_content,
            "conversation_id": conversation.id,
            "message_id": assistant_message.id
        }
    
    def _get_or_create_conversation(
        self,
        db: Session,
        user_id: int,
        conversation_id: Optional[int] = None
    ) -> AIConversation:
        if conversation_id:
            conversation = db.query(AIConversation).filter(
                AIConversation.id == conversation_id,
                AIConversation.user_id == user_id
            ).first()
            if conversation:
                return conversation
        
        conversation = AIConversation(
            user_id=user_id,
            context_type=ContextType.COACH
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation
    
    def _build_coach_context(self, db: Session, user_id: int) -> Dict[str, Any]:
        from app.models.workout import WorkoutPlan, WorkoutSession, ExerciseLog
        from app.models.nutrition import MealPlan
        from app.models.progress import WeightLog
        from app.models.profile import Profile
        from app.models.user import User
        
        user = db.query(User).filter(User.id == user_id).first()
        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        
        current_workout = db.query(WorkoutPlan).filter(
            WorkoutPlan.user_id == user_id,
            WorkoutPlan.status == "active"
        ).first()
        
        workout_summary = "Nenhum plano ativo"
        if current_workout:
            sessions = db.query(WorkoutSession).filter(
                WorkoutSession.workout_plan_id == current_workout.id
            ).all()
            workout_summary = f"{len(sessions)} sessões por semana"
        
        current_meal = db.query(MealPlan).filter(
            MealPlan.user_id == user_id
        ).order_by(MealPlan.created_at.desc()).first()
        
        meal_summary = "Nenhum plano ativo"
        if current_meal:
            meal_summary = f"{current_meal.daily_calorie_target:.0f} kcal/dia"
        
        recent_logs = db.query(ExerciseLog).join(
            ExerciseLog.session_exercise
        ).filter(
            ExerciseLog.difficulty_feedback.isnot(None)
        ).order_by(
            ExerciseLog.completed_at.desc()
        ).limit(5).all()
        
        difficulty_feedback = [log.difficulty_feedback for log in recent_logs if log.difficulty_feedback]
        
        streak = 0
        last_weight = db.query(WeightLog).filter(
            WeightLog.user_id == user_id
        ).order_by(WeightLog.logged_at.desc()).first()
        
        return {
            "current_workout_summary": workout_summary,
            "current_meal_plan_summary": meal_summary,
            "recent_difficulty_feedback": ", ".join(difficulty_feedback) if difficulty_feedback else "Nenhum feedback recente",
            "current_streak": str(streak),
            "last_weight_log": f"{last_weight.weight_kg:.1f} kg" if last_weight else "Não registrado"
        }
