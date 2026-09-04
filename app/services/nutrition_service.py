import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.nutrition import (
    Food,
    Recipe,
    MealPlan,
    Meal,
    MealItem,
    MealLog,
    MealType,
)
from app.models.user import User
from app.models.goal import Goal
from app.models.preference import Preference
from app.models.profile import Profile
from app.services.ai_engine import AIEngine

logger = logging.getLogger(__name__)

class NutritionService:
    def __init__(self):
        self.ai_engine = AIEngine()
    
    def generate_meal_plan(
        self,
        db: Session,
        user_id: int
    ) -> MealPlan:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("Usuário não encontrado")
        
        goal = db.query(Goal).filter(Goal.user_id == user_id).first()
        preferences = db.query(Preference).filter(Preference.user_id == user_id).first()
        profile = db.query(Profile).filter(Profile.user_id == user_id).first()
        
        if not goal or not preferences:
            raise ValueError("Dados de perfil incompletos. Complete o onboarding.")
        
        calorie_target, macros_target = self._calculate_nutrition_targets(
            profile=profile,
            goal=goal,
            preferences=preferences
        )
        
        foods = db.query(Food).all()
        available_foods = [
            {
                "id": f.id,
                "name": f.name,
                "calories_per_100g": f.calories_per_100g,
                "protein_g": f.protein_g,
                "carbs_g": f.carbs_g,
                "fat_g": f.fat_g,
                "category": f.category.value if f.category else "other"
            }
            for f in foods
        ]
        
        recipes = db.query(Recipe).all()
        available_recipes = [
            {
                "id": r.id,
                "name": r.name,
                "instructions": r.instructions,
                "prep_time_min": r.prep_time_min,
                "foods": r.foods
            }
            for r in recipes
        ]
        
        user_data = {
            "goal": goal.goal_type.value,
            "daily_calorie_target": calorie_target,
            "macros_target": macros_target,
            "dietary_restrictions": preferences.dietary_restrictions or [],
            "disliked_foods": preferences.disliked_foods or [],
            "liked_foods": preferences.liked_foods or [],
            "weekly_budget": None
        }
        
        ai_result = self.ai_engine.generate_meal_plan(
            db=db,
            user_data=user_data,
            available_foods=available_foods,
            available_recipes=available_recipes
        )
        
        meal_plan = MealPlan(
            user_id=user_id,
            daily_calorie_target=calorie_target,
            macros_target=macros_target,
            version=1
        )
        db.add(meal_plan)
        db.flush()
        
        day_mapping = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2,
            "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
        }
        
        for meal_data in ai_result.get("meals", []):
            day = meal_data.get("day", "Monday")
            
            for meal_type_str in ["breakfast", "lunch", "snack", "dinner"]:
                item = meal_data.get(meal_type_str)
                if not item:
                    continue
                
                meal_type = self._map_meal_type(meal_type_str)
                food_id = item.get("food_id")
                recipe_id = item.get("recipe_id")
                quantity_g = item.get("quantity_g", 100)
                
                if not food_id and not recipe_id:
                    continue
                
                meal = Meal(
                    meal_plan_id=meal_plan.id,
                    meal_type=meal_type,
                    day_of_week=day
                )
                db.add(meal)
                db.flush()
                
                meal_item = MealItem(
                    meal_id=meal.id,
                    food_id_or_recipe_id=food_id or recipe_id,
                    is_recipe=bool(recipe_id),
                    quantity_g=quantity_g,
                    order_index=0
                )
                db.add(meal_item)
        
        db.commit()
        db.refresh(meal_plan)
        
        logger.info(f"Plano alimentar gerado para usuário {user_id}, ID: {meal_plan.id}")
        return meal_plan
    
    def _calculate_nutrition_targets(
        self,
        profile: Optional[Profile],
        goal: Goal,
        preferences: Preference
    ) -> tuple:
        if not profile:
            return 2000, {"protein_g": 150, "carbs_g": 200, "fat_g": 60}
        
        weight = profile.weight_kg or 70
        height = profile.height_cm or 170
        age = profile.age or 30
        
        if profile.sex == "male":
            bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
        else:
            bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
        
        activity_factors = {
            "sedentary": 1.2,
            "lightly_active": 1.375,
            "moderately_active": 1.55,
            "very_active": 1.725,
            "extra_active": 1.9
        }
        factor = activity_factors.get(profile.activity_level.value if profile.activity_level else "moderately_active", 1.55)
        
        tdee = bmr * factor
        
        if goal.goal_type == "lose_weight":
            calorie_target = tdee - 500
            protein_g = weight * 2.2
            fat_g = 0.3 * calorie_target / 9
            carbs_g = (calorie_target - (protein_g * 4) - (fat_g * 9)) / 4
        elif goal.goal_type == "gain_muscle":
            calorie_target = tdee + 300
            protein_g = weight * 2.2
            fat_g = 0.25 * calorie_target / 9
            carbs_g = (calorie_target - (protein_g * 4) - (fat_g * 9)) / 4
        else:
            calorie_target = tdee
            protein_g = weight * 1.8
            fat_g = 0.25 * calorie_target / 9
            carbs_g = (calorie_target - (protein_g * 4) - (fat_g * 9)) / 4
        
        calorie_target = max(calorie_target, 1200)
        protein_g = max(protein_g, 100)
        fat_g = max(fat_g, 40)
        carbs_g = max(carbs_g, 100)
        
        return int(calorie_target), {
            "protein_g": int(protein_g),
            "carbs_g": int(carbs_g),
            "fat_g": int(fat_g)
        }
    
    def _map_meal_type(self, meal_type_str: str) -> MealType:
        mapping = {
            "breakfast": MealType.BREAKFAST,
            "lunch": MealType.LUNCH,
            "snack": MealType.SNACK,
            "dinner": MealType.DINNER
        }
        return mapping.get(meal_type_str, MealType.SNACK)
    
    def get_active_plan(
        self,
        db: Session,
        user_id: int
    ) -> Optional[MealPlan]:
        return db.query(MealPlan).filter(
            MealPlan.user_id == user_id
        ).order_by(MealPlan.created_at.desc()).first()
    
    def get_today_meals(
        self,
        db: Session,
        user_id: int
    ) -> List[Meal]:
        today_name = datetime.now().strftime("%A")
        
        active_plan = self.get_active_plan(db, user_id)
        if not active_plan:
            return []
        
        meals = db.query(Meal).filter(
            Meal.meal_plan_id == active_plan.id,
            Meal.day_of_week == today_name
        ).all()
        
        for meal in meals:
            db.refresh(meal)
        
        return meals
    
    def log_meal(
        self,
        db: Session,
        user_id: int,
        meal_id: Optional[int] = None,
        meal_type: Optional[str] = None,
        freeform_description: Optional[str] = None,
        photo_url: Optional[str] = None,
        estimated_calories: Optional[float] = None,
        estimated_macros: Optional[Dict[str, float]] = None,
        confirmed_by_user: bool = False
    ) -> MealLog:
        meal_log = MealLog(
            user_id=user_id,
            meal_id=meal_id,
            meal_type=MealType(meal_type) if meal_type else None,
            freeform_description=freeform_description,
            photo_url=photo_url,
            estimated_calories=estimated_calories,
            estimated_macros=estimated_macros,
            confirmed_by_user=confirmed_by_user
        )
        db.add(meal_log)
        db.commit()
        db.refresh(meal_log)
        
        return meal_log
    
    def estimate_meal_from_photo(
        self,
        db: Session,
        image_description: str
    ) -> Dict[str, Any]:
        foods = db.query(Food).all()
        available_foods = [
            {
                "id": f.id,
                "name": f.name,
                "calories_per_100g": f.calories_per_100g,
                "protein_g": f.protein_g,
                "carbs_g": f.carbs_g,
                "fat_g": f.fat_g
            }
            for f in foods
        ]
        
        return self.ai_engine.estimate_meal_from_photo(
            image_description=image_description,
            available_foods=available_foods
        )
    
    def get_daily_calorie_progress(
        self,
        db: Session,
        user_id: int
    ) -> Dict[str, Any]:
        today = datetime.now().date()
        
        plan = self.get_active_plan(db, user_id)
        if not plan:
            return {"total_calories": 0, "target_calories": 2000, "progress": 0}
        
        logs = db.query(MealLog).filter(
            MealLog.user_id == user_id,
            MealLog.logged_at.cast == today
        ).all()
        
        total_calories = sum(log.estimated_calories or 0 for log in logs)
        target = plan.daily_calorie_target
        
        return {
            "total_calories": total_calories,
            "target_calories": target,
            "progress": min(100, (total_calories / target) * 100) if target > 0 else 0,
            "remaining": max(0, target - total_calories)
        }
