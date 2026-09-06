from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict
from app.models.nutrition import FoodCategory, MealType

class FoodResponse(BaseModel):
    id: int
    name: str
    calories_per_100g: float
    protein_g: float
    carbs_g: float
    fat_g: float
    category: Optional[FoodCategory] = None
    
    class Config:
        from_attributes = True

class RecipeResponse(BaseModel):
    id: int
    name: str
    instructions: Optional[str] = None
    prep_time_min: Optional[int] = None
    foods: Dict
    image_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class MealItemResponse(BaseModel):
    id: int
    food_id_or_recipe_id: int
    is_recipe: bool
    quantity_g: float
    order_index: int
    food: Optional[FoodResponse] = None
    
    class Config:
        from_attributes = True

class MealResponse(BaseModel):
    id: int
    meal_plan_id: int
    meal_type: MealType
    day_of_week: str
    meal_items: List[MealItemResponse] = []
    created_at: datetime
    
    class Config:
        from_attributes = True

class MealPlanCreate(BaseModel):
    daily_calorie_target: float = Field(..., ge=1000, le=10000)
    macros_target: Dict[str, float]
    version: int = 1

class MealPlanResponse(BaseModel):
    id: int
    user_id: int
    daily_calorie_target: float
    macros_target: Dict[str, float]
    version: int
    meals: List[MealResponse] = []
    created_at: datetime
    
    class Config:
        from_attributes = True

class MealLogCreate(BaseModel):
    meal_id: Optional[int] = None
    meal_type: Optional[MealType] = None
    freeform_description: Optional[str] = None
    photo_url: Optional[str] = None
    estimated_calories: Optional[float] = None
    estimated_macros: Optional[Dict[str, float]] = None
    confirmed_by_user: bool = False

class MealLogResponse(BaseModel):
    id: int
    user_id: int
    meal_id: Optional[int] = None
    meal_type: Optional[MealType] = None
    freeform_description: Optional[str] = None
    photo_url: Optional[str] = None
    estimated_calories: Optional[float] = None
    estimated_macros: Optional[Dict[str, float]] = None
    confirmed_by_user: bool
    logged_at: datetime
    
    class Config:
        from_attributes = True

class MealPlanGenerationRequest(BaseModel):
    user_id: int
    goal: str
    daily_calorie_target: float
    macros_target: Dict[str, float]
    dietary_restrictions: List[str]
    disliked_foods: List[str]
    liked_foods: List[str]
    weekly_budget: Optional[float] = None

class MealPlanGenerationResponse(BaseModel):
    meal_plan: dict
    message: Optional[str] = None
