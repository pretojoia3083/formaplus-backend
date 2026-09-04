import json
import logging
from typing import Dict, Any, List, Optional
from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.prompts import (
    WORKOUT_GENERATION_PROMPT,
    MEAL_PLAN_GENERATION_PROMPT,
    COACH_PROMPT,
    WORKOUT_ADAPTATION_PROMPT,
    EXERCISE_SUBSTITUTION_PROMPT,
    MEAL_ESTIMATION_PROMPT,
    PROGRESS_SUMMARY_PROMPT,
)
from app.models.exercise import Exercise
from app.models.nutrition import Food, Recipe

logger = logging.getLogger(__name__)

class AIEngine:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o"
    
    def generate_workout_plan(
        self,
        db: Session,
        user_data: Dict[str, Any],
        available_exercises: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        try:
            prompt = WORKOUT_GENERATION_PROMPT
            for key, value in user_data.items():
                prompt = prompt.replace(f"{{{{{key}}}}}", str(value))
            
            prompt = prompt.replace(
                "{{available_exercises}}",
                json.dumps(available_exercises, ensure_ascii=False)
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "Gere o plano de treino personalizado."}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            validated_workout = self._validate_workout_exercises(db, result)
            
            return validated_workout
            
        except Exception as e:
            logger.error(f"Erro ao gerar plano de treino: {e}")
            raise
    
    def _validate_workout_exercises(self, db: Session, workout_data: Dict[str, Any]) -> Dict[str, Any]:
        if "workout" not in workout_data:
            return workout_data
        
        valid_exercise_ids = set(
            e[0] for e in db.query(Exercise.id).all()
        )
        
        for day in workout_data.get("workout", []):
            for exercise in day.get("exercises", []):
                exercise_id = exercise.get("exercise_id")
                if exercise_id not in valid_exercise_ids:
                    logger.warning(f"Exercise ID {exercise_id} não encontrado no banco")
                    exercise["exercise_id"] = None
        
        return workout_data
    
    def generate_meal_plan(
        self,
        db: Session,
        user_data: Dict[str, Any],
        available_foods: List[Dict[str, Any]],
        available_recipes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        try:
            prompt = MEAL_PLAN_GENERATION_PROMPT
            for key, value in user_data.items():
                prompt = prompt.replace(f"{{{{{key}}}}}", str(value))
            
            prompt = prompt.replace(
                "{{available_foods}}",
                json.dumps(available_foods, ensure_ascii=False)
            ).replace(
                "{{available_recipes}}",
                json.dumps(available_recipes, ensure_ascii=False)
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "Gere o plano alimentar personalizado."}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            validated_plan = self._validate_meal_plan_items(db, result)
            
            return validated_plan
            
        except Exception as e:
            logger.error(f"Erro ao gerar plano alimentar: {e}")
            raise
    
    def _validate_meal_plan_items(self, db: Session, meal_data: Dict[str, Any]) -> Dict[str, Any]:
        valid_food_ids = set(f[0] for f in db.query(Food.id).all())
        valid_recipe_ids = set(r[0] for r in db.query(Recipe.id).all())
        
        for meal in meal_data.get("meals", []):
            for meal_type in ["breakfast", "lunch", "snack", "dinner"]:
                item = meal.get(meal_type)
                if item:
                    food_id = item.get("food_id")
                    recipe_id = item.get("recipe_id")
                    
                    if food_id and food_id not in valid_food_ids:
                        logger.warning(f"Food ID {food_id} não encontrado no banco")
                        item["food_id"] = None
                    
                    if recipe_id and recipe_id not in valid_recipe_ids:
                        logger.warning(f"Recipe ID {recipe_id} não encontrado no banco")
                        item["recipe_id"] = None
        
        return meal_data
    
    def get_coach_response(
        self,
        user_message: str,
        context: Dict[str, Any]
    ) -> str:
        try:
            prompt = COACH_PROMPT
            for key, value in context.items():
                prompt = prompt.replace(f"{{{{{key}}}}}", str(value))
            
            prompt = prompt.replace("{{user_message}}", user_message)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erro no Coach: {e}")
            return "Desculpe, estou tendo um momento de reflexão. Pode repetir? 😅"
    
    def adapt_workout(
        self,
        original_session: Dict[str, Any],
        available_minutes: int,
        available_exercises: List[Dict[str, Any]],
        session_focus: str
    ) -> Dict[str, Any]:
        try:
            prompt = WORKOUT_ADAPTATION_PROMPT
            prompt = prompt.replace("{{original_session_json}}", json.dumps(original_session))
            prompt = prompt.replace("{{available_minutes}}", str(available_minutes))
            prompt = prompt.replace("{{available_exercises}}", json.dumps(available_exercises))
            prompt = prompt.replace("{{session_focus}}", session_focus)
            prompt = prompt.replace("{{day}}", original_session.get("day", "Today"))
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Adapte o treino para {available_minutes} minutos."}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Erro na adaptação de treino: {e}")
            raise
    
    def substitute_exercise(
        self,
        exercise_id: int,
        exercise_name: str,
        muscle_group: str,
        available_equipment: List[str],
        experience_level: str,
        available_exercises: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        try:
            prompt = EXERCISE_SUBSTITUTION_PROMPT
            prompt = prompt.replace("{{exercise_id}}", str(exercise_id))
            prompt = prompt.replace("{{exercise_name}}", exercise_name)
            prompt = prompt.replace("{{muscle_group}}", muscle_group)
            prompt = prompt.replace("{{available_equipment}}", json.dumps(available_equipment))
            prompt = prompt.replace("{{experience_level}}", experience_level)
            prompt = prompt.replace("{{available_exercises}}", json.dumps(available_exercises))
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Encontre um substituto para {exercise_name}."}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Erro na substituição de exercício: {e}")
            raise
    
    def estimate_meal_from_photo(
        self,
        image_description: str,
        available_foods: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        try:
            prompt = MEAL_ESTIMATION_PROMPT
            prompt = prompt.replace("{{available_foods}}", json.dumps(available_foods))
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Analise esta refeição: {image_description}"}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            if "disclaimer" not in result:
                result["disclaimer"] = "Estimativa — confirme as porções para maior precisão."
            
            return result
            
        except Exception as e:
            logger.error(f"Erro na estimativa de refeição: {e}")
            return {
                "identified_items": [],
                "estimated_calories": 0,
                "estimated_macros": {"protein_g": 0, "carbs_g": 0, "fat_g": 0},
                "disclaimer": "Não foi possível estimar a refeição. Tente novamente."
            }
    
    def generate_progress_summary(
        self,
        weight_history: List[Dict],
        measurements_history: List[Dict],
        workout_adherence_pct: float,
        avg_difficulty_feedback: str
    ) -> Dict[str, Any]:
        try:
            prompt = PROGRESS_SUMMARY_PROMPT
            prompt = prompt.replace("{{weight_history}}", json.dumps(weight_history))
            prompt = prompt.replace("{{measurements_history}}", json.dumps(measurements_history))
            prompt = prompt.replace("{{workout_adherence_pct}}", str(workout_adherence_pct))
            prompt = prompt.replace("{{avg_difficulty_feedback}}", avg_difficulty_feedback)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "Resuma minha evolução."}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Erro no resumo de evolução: {e}")
            return {
                "summary_text": "Ainda estamos coletando dados para avaliar sua evolução. Continue consistente! 💪",
                "trend": "insufficient_data"
            }
