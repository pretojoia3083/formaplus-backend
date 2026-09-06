from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, JSON, Float, Enum as SAEnum, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class FoodCategory(str, enum.Enum):
    PROTEIN = "protein"
    CARB = "carb"
    FAT = "fat"
    VEGETABLE = "vegetable"
    FRUIT = "fruit"
    DAIRY = "dairy"
    GRAIN = "grain"
    BEVERAGE = "beverage"
    OTHER = "other"

class MealType(str, enum.Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    SNACK = "snack"
    DINNER = "dinner"

class Food(Base):
    __tablename__ = "foods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    calories_per_100g = Column(Float, nullable=False)
    protein_g = Column(Float, nullable=False)
    carbs_g = Column(Float, nullable=False)
    fat_g = Column(Float, nullable=False)
    category = Column(SAEnum(FoodCategory, native_enum=False), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    instructions = Column(Text, nullable=True)
    prep_time_min = Column(Integer, nullable=True)
    foods = Column(JSON, nullable=False)
    image_url = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class MealPlan(Base):
    __tablename__ = "meal_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    daily_calorie_target = Column(Float, nullable=False)
    macros_target = Column(JSON, nullable=False)
    version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="meal_plans")
    meals = relationship("Meal", back_populates="meal_plan")

class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    meal_plan_id = Column(Integer, ForeignKey("meal_plans.id"), nullable=False)
    meal_type = Column(SAEnum(MealType, native_enum=False), nullable=False)
    day_of_week = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    meal_plan = relationship("MealPlan", back_populates="meals")
    meal_items = relationship("MealItem", back_populates="meal")

class MealItem(Base):
    __tablename__ = "meal_items"

    id = Column(Integer, primary_key=True, index=True)
    meal_id = Column(Integer, ForeignKey("meals.id"), nullable=False)
    food_id_or_recipe_id = Column(Integer, nullable=False)
    is_recipe = Column(Boolean, default=False)
    quantity_g = Column(Float, nullable=False)
    order_index = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    meal = relationship("Meal", back_populates="meal_items")
    food = relationship("Food", primaryjoin="foreign(MealItem.food_id_or_recipe_id) == Food.id", viewonly=True)

class MealLog(Base):
    __tablename__ = "meal_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    meal_id = Column(Integer, ForeignKey("meals.id"), nullable=True)
    meal_type = Column(SAEnum(MealType, native_enum=False), nullable=True)
    freeform_description = Column(String(512), nullable=True)
    photo_url = Column(String(512), nullable=True)
    estimated_calories = Column(Float, nullable=True)
    estimated_macros = Column(JSON, nullable=True)
    confirmed_by_user = Column(Boolean, default=False)
    logged_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="meal_logs")
