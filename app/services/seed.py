from sqlalchemy.orm import Session
from app.models.exercise import Exercise, MuscleGroup, Equipment, Difficulty
from app.models.nutrition import Food, FoodCategory

def seed_exercises(db: Session):
    exercises = [
        {
            "name": "Supino Reto com Barra",
            "muscle_group": MuscleGroup.CHEST,
            "equipment": Equipment.BARBELL,
            "difficulty": Difficulty.INTERMEDIATE,
            "instructions": "Deite no banco, segure a barra com pegada pronada, desça até o peito e estenda os braços.",
        },
        {
            "name": "Agachamento Livre",
            "muscle_group": MuscleGroup.LEGS,
            "equipment": Equipment.BARBELL,
            "difficulty": Difficulty.INTERMEDIATE,
            "instructions": "Posicione a barra nos ombros, desça agachando até 90° e suba.",
        },
        {
            "name": "Flexão de Braço",
            "muscle_group": MuscleGroup.CHEST,
            "equipment": Equipment.BODYWEIGHT,
            "difficulty": Difficulty.BEGINNER,
            "instructions": "Em posição de prancha, desça o peito até o chão e suba.",
        },
        {
            "name": "Puxada na Frente",
            "muscle_group": MuscleGroup.BACK,
            "equipment": Equipment.MACHINE,
            "difficulty": Difficulty.INTERMEDIATE,
            "instructions": "Sente na máquina, segure a barra com pegada pronada, puxe até o peito.",
        },
        {
            "name": "Desenvolvimento com Halteres",
            "muscle_group": MuscleGroup.SHOULDERS,
            "equipment": Equipment.DUMBBELL,
            "difficulty": Difficulty.INTERMEDIATE,
            "instructions": "Em pé, segure halteres na altura dos ombros, estenda os braços para cima.",
        },
    ]
    
    for ex in exercises:
        if not db.query(Exercise).filter(Exercise.name == ex["name"]).first():
            db.add(Exercise(**ex))
    db.commit()

def seed_foods(db: Session):
    foods = [
        {"name": "Frango", "calories_per_100g": 165, "protein_g": 31, "carbs_g": 0, "fat_g": 3.6, "category": FoodCategory.PROTEIN},
        {"name": "Arroz Branco", "calories_per_100g": 130, "protein_g": 2.7, "carbs_g": 28, "fat_g": 0.3, "category": FoodCategory.CARB},
        {"name": "Ovo", "calories_per_100g": 155, "protein_g": 13, "carbs_g": 1.1, "fat_g": 11, "category": FoodCategory.PROTEIN},
        {"name": "Batata Doce", "calories_per_100g": 86, "protein_g": 1.6, "carbs_g": 20, "fat_g": 0.1, "category": FoodCategory.CARB},
        {"name": "Brócolis", "calories_per_100g": 34, "protein_g": 2.8, "carbs_g": 7, "fat_g": 0.4, "category": FoodCategory.VEGETABLE},
        {"name": "Abacate", "calories_per_100g": 160, "protein_g": 2, "carbs_g": 9, "fat_g": 15, "category": FoodCategory.FAT},
        {"name": "Leite Integral", "calories_per_100g": 61, "protein_g": 3.3, "carbs_g": 4.8, "fat_g": 3.3, "category": FoodCategory.DAIRY},
        {"name": "Pão Integral", "calories_per_100g": 265, "protein_g": 13, "carbs_g": 43, "fat_g": 4, "category": FoodCategory.GRAIN},
    ]
    
    for food in foods:
        if not db.query(Food).filter(Food.name == food["name"]).first():
            db.add(Food(**food))
    db.commit()
