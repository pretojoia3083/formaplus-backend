from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_plan_type
from app.models.user import User
from app.models.nutrition import MealPlan, Meal, MealItem, Food, MealLog
from app.services.nutrition_service import NutritionService

router = APIRouter()
nutrition_service = NutritionService()

def serialize_meal_plan(plan: MealPlan, db: Session) -> dict:
    meals_data = []
    meals = db.query(Meal).filter(Meal.meal_plan_id == plan.id).all()
    
    for m in meals:
        items_data = []
        meal_items = db.query(MealItem).filter(MealItem.meal_id == m.id).order_by(MealItem.order_index).all()
        
        for mi in meal_items:
            food = db.query(Food).filter(Food.id == mi.food_id_or_recipe_id).first() if not mi.is_recipe else None
            items_data.append({
                "id": mi.id,
                "food_id_or_recipe_id": mi.food_id_or_recipe_id,
                "is_recipe": mi.is_recipe,
                "quantity_g": mi.quantity_g,
                "order_index": mi.order_index,
                "food": {
                    "id": food.id,
                    "name": food.name,
                    "calories_per_100g": food.calories_per_100g,
                    "protein_g": food.protein_g,
                    "carbs_g": food.carbs_g,
                    "fat_g": food.fat_g,
                    "category": food.category.value if food.category else None,
                } if food else None,
            })
        
        meals_data.append({
            "id": m.id,
            "meal_plan_id": m.meal_plan_id,
            "meal_type": m.meal_type.value if m.meal_type else None,
            "day_of_week": m.day_of_week,
            "meal_items": items_data,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        })
    
    return {
        "id": plan.id,
        "user_id": plan.user_id,
        "daily_calorie_target": plan.daily_calorie_target,
        "macros_target": plan.macros_target,
        "version": plan.version,
        "meals": meals_data,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
    }

@router.post("/nutrition/generate")
async def generate_meal_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        plan = nutrition_service.generate_meal_plan(db=db, user_id=current_user.id)
        return serialize_meal_plan(plan, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/nutrition/active")
async def get_active_meal_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = nutrition_service.get_active_plan(db=db, user_id=current_user.id)
    if not plan:
        return None
    return serialize_meal_plan(plan, db)

@router.get("/nutrition/today")
async def get_today_meals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    meals = nutrition_service.get_today_meals(db=db, user_id=current_user.id)
    result = []
    for m in meals:
        items_data = []
        meal_items = db.query(MealItem).filter(MealItem.meal_id == m.id).order_by(MealItem.order_index).all()
        for mi in meal_items:
            food = db.query(Food).filter(Food.id == mi.food_id_or_recipe_id).first() if not mi.is_recipe else None
            items_data.append({
                "id": mi.id,
                "food_id_or_recipe_id": mi.food_id_or_recipe_id,
                "is_recipe": mi.is_recipe,
                "quantity_g": mi.quantity_g,
                "order_index": mi.order_index,
                "food": {
                    "id": food.id,
                    "name": food.name,
                    "calories_per_100g": food.calories_per_100g,
                    "protein_g": food.protein_g,
                    "carbs_g": food.carbs_g,
                    "fat_g": food.fat_g,
                } if food else None,
            })
        result.append({
            "id": m.id,
            "meal_plan_id": m.meal_plan_id,
            "meal_type": m.meal_type.value if m.meal_type else None,
            "day_of_week": m.day_of_week,
            "meal_items": items_data,
        })
    return result

@router.post("/nutrition/log")
async def log_meal(
    log_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        log = nutrition_service.log_meal(
            db=db,
            user_id=current_user.id,
            meal_id=log_data.get("meal_id"),
            meal_type=log_data.get("meal_type"),
            freeform_description=log_data.get("freeform_description"),
            photo_url=log_data.get("photo_url"),
            estimated_calories=log_data.get("estimated_calories"),
            estimated_macros=log_data.get("estimated_macros"),
            confirmed_by_user=log_data.get("confirmed_by_user", False)
        )
        return {"id": log.id, "message": "Refeição registrada!"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/nutrition/estimate-meal")
async def estimate_meal_from_photo(
    description: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = nutrition_service.estimate_meal_from_photo(
            db=db,
            image_description=description
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/nutrition/daily-progress")
async def get_daily_calorie_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        progress = nutrition_service.get_daily_calorie_progress(
            db=db,
            user_id=current_user.id
        )
        return progress
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/nutrition/history")
async def get_meal_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 30,
    offset: int = 0
):
    logs = db.query(MealLog).filter(
        MealLog.user_id == current_user.id
    ).order_by(
        MealLog.logged_at.desc()
    ).offset(offset).limit(limit).all()
    
    return {"total": len(logs), "logs": logs}

@router.delete("/nutrition/delete")
async def delete_meal_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = db.query(MealPlan).filter(
        MealPlan.user_id == current_user.id
    ).order_by(MealPlan.created_at.desc()).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Nenhum plano alimentar encontrado")
    
    meals = db.query(Meal).filter(Meal.meal_plan_id == plan.id).all()
    for m in meals:
        db.query(MealItem).filter(MealItem.meal_id == m.id).delete()
        db.delete(m)
    
    db.delete(plan)
    db.commit()
    return {"detail": "Plano alimentar excluído com sucesso"}
