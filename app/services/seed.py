from sqlalchemy.orm import Session
from app.models.exercise import Exercise, MuscleGroup, Equipment, Difficulty
from app.models.nutrition import Food, FoodCategory

def seed_exercises(db: Session):
    if db.query(Exercise).count() > 0:
        return
    
    exercises = [
        # PEITO
        {"name": "Supino Reto com Barra", "muscle_group": MuscleGroup.CHEST, "equipment": Equipment.BARBELL, "difficulty": Difficulty.INTERMEDIATE, "instructions": "Deite no banco, segure a barra, desça até o peito e estenda."},
        {"name": "Supino Reto com Halteres", "muscle_group": MuscleGroup.CHEST, "equipment": Equipment.DUMBBELL, "difficulty": Difficulty.INTERMEDIATE, "instructions": "Deite no banco, segure halteres, desça até o peito e estenda."},
        {"name": "Supino Inclinado com Barra", "muscle_group": MuscleGroup.CHEST, "equipment": Equipment.BARBELL, "difficulty": Difficulty.INTERMEDIATE, "instructions": "No banco inclinado, desça a barra até o peito superior e estenda."},
        {"name": "Supino Inclinado com Halteres", "muscle_group": MuscleGroup.CHEST, "equipment": Equipment.DUMBBELL, "difficulty": Difficulty.INTERMEDIATE, "instructions": "No banco inclinado, desça halteres até o peito e estenda."},
        {"name": "Crucifixo com Halteres", "muscle_group": MuscleGroup.CHEST, "equipment": Equipment.DUMBBELL, "difficulty": Difficulty.BEGINNER, "instructions": "Deite, abra os braços em arco e feche sobre o peito."},
        {"name": "Crossover", "muscle_group": MuscleGroup.CHEST, "equipment": Equipment.CABLE, "difficulty": Difficulty.INTERMEDIATE, "instructions": "Em pé entre os cabos, junte as mãos à frente do peito."},
        {"name": "Flexão de Braço", "muscle_group": MuscleGroup.CHEST, "equipment": Equipment.BODYWEIGHT, "difficulty": Difficulty.BEGINNER, "instructions": "Em prancha, desça o peito até o chão e suba. Exercício caseiro, sem equipamento."},
        {"name": "Supino Máquina", "muscle_group": MuscleGroup.CHEST, "equipment": Equipment.MACHINE, "difficulty": Difficulty.BEGINNER, "instructions": "Sente na máquina, empurre as alças à frente."},
        
        # COSTAS
        {"name": "Puxada na Frente", "muscle_group": MuscleGroup.BACK, "equipment": Equipment.MACHINE, "difficulty": Difficulty.INTERMEDIATE, "instructions": "Sente na máquina, puxe a barra até o peito."},
        {"name": "Puxada na Frente com Pegada Fechada", "muscle_group": MuscleGroup.BACK, "equipment": Equipment.MACHINE, "difficulty": Difficulty.INTERMEDIATE, "instructions": "Sente, puxe com pegada fechada até o peito."},
        {"name": "Remada Curvada com Barra", "muscle_group": MuscleGroup.BACK, "equipment": Equipment.BARBELL, "difficulty": Difficulty.INTERMEDIATE, "instructions": "Incline o torso, puxe a barra até o abdômen."},
        {"name": "Remada Unilateral com Halter", "muscle_group": MuscleGroup.BACK, "equipment": Equipment.DUMBBELL, "difficulty": Difficulty.BEGINNER, "instructions": "Apoie joelho e mão no banco, puxe o halter até o quadril."},
        {"name": "Remada na Máquina", "muscle_group": MuscleGroup.BACK, "equipment": Equipment.MACHINE, "difficulty": Difficulty.BEGINNER, "instructions": "Sente na máquina, puxe as alças até o abdômen."},
        {"name": "Pulldown", "muscle_group": MuscleGroup.BACK, "equipment": Equipment.CABLE, "difficulty": Difficulty.INTERMEDIATE, "instructions": "Sente, puxe a barra até o peito com controle."},
        {"name": "Barra Fixa (Pull-up)", "muscle_group": MuscleGroup.BACK, "equipment": Equipment.BODYWEIGHT, "difficulty": Difficulty.ADVANCED, "instructions": "Segure a barra e suba o corpo até o queixo passar da barra."},
        
        # PERNAS
        {"name": "Agachamento Livre", "muscle_group": MuscleGroup.LEGS, "equipment": Equipment.BARBELL, "difficulty": Difficulty.INTERMEDIATE, "instructions": "Barra nos ombros, desça agachando até 90° e suba."},
        {"name": "Agachamento no Smith", "muscle_group": MuscleGroup.LEGS, "equipment": Equipment.MACHINE, "difficulty": Difficulty.BEGINNER, "instructions": "Na máquina smith, desça agachando e suba."},
        {"name": "Leg Press 45°", "muscle_group": MuscleGroup.LEGS, "equipment": Equipment.MACHINE, "difficulty": Difficulty.BEGINNER, "instructions": "Sente na máquina, empurre a plataforma com os pés."},
        {"name": "Cadeira Extensora", "muscle_group": MuscleGroup.LEGS, "equipment": Equipment.MACHINE, "difficulty": Difficulty.BEGINNER, "instructions": "Sente, estenda os joelhos e volte devagar."},
        {"name": "Cadeira Flexora", "muscle_group": MuscleGroup.LEGS, "equipment": Equipment.MACHINE, "difficulty": Difficulty.BEGINNER, "instructions": "Sente de bruços, flexione os joelhos."},
        {"name": "Stiff com Barra", "muscle_group": MuscleGroup.LEGS, "equipment": Equipment.BARBELL, "difficulty": Difficulty.INTERMEDIATE, "instructions": "Em pé, desça a barra pela frente das pernas flexionando os quadris."},
        {"name": "Avanço com Halteres", "muscle_group": MuscleGroup.LEGS, "equipment": Equipment.DUMBBELL, "difficulty": Difficulty.BEGINNER, "instructions": "Dê um passo à frente e agache o joelho de trás."},
        {"name": "Panturrilha em Pé", "muscle_group": MuscleGroup.LEGS, "equipment": Equipment.MACHINE, "difficulty": Difficulty.BEGINNER, "instructions": "Em pé na máquina, suba nas pontas dos pés."},
        {"name": "Elevação Pélvica", "muscle_group": MuscleGroup.GLUTES, "equipment": Equipment.BARBELL, "difficulty": Difficulty.INTERMEDIATE, "instructions": "Deite, coloque barra no quadril, suba o quadril contraindo glúteos."},
        
        # OMBROS
        {"name": "Desenvolvimento com Halteres", "muscle_group": MuscleGroup.SHOULDERS, "equipment": Equipment.DUMBBELL, "difficulty": Difficulty.INTERMEDIATE, "instructions": "Em pé, estenda halteres acima da cabeça."},
        {"name": "Desenvolvimento com Barra", "muscle_group": MuscleGroup.SHOULDERS, "equipment": Equipment.BARBELL, "difficulty": Difficulty.INTERMEDIATE, "instructions": "Em pé, empurre a barra acima da cabeça."},
        {"name": "Elevação Lateral", "muscle_group": MuscleGroup.SHOULDERS, "equipment": Equipment.DUMBBELL, "difficulty": Difficulty.BEGINNER, "instructions": "Em pé, eleve os halteres lateralmente até a altura dos ombros."},
        {"name": "Elevação Frontal", "muscle_group": MuscleGroup.SHOULDERS, "equipment": Equipment.DUMBBELL, "difficulty": Difficulty.BEGINNER, "instructions": "Em pé, eleve os halteres à frente até a altura dos ombros."},
        {"name": "Face Pull", "muscle_group": MuscleGroup.SHOULDERS, "equipment": Equipment.CABLE, "difficulty": Difficulty.BEGINNER, "instructions": "Puxe o cabo até o rosto, abrindo os cotovelos."},
        {"name": "Encolhimento com Halteres", "muscle_group": MuscleGroup.SHOULDERS, "equipment": Equipment.DUMBBELL, "difficulty": Difficulty.BEGINNER, "instructions": "Em pé, eleve os ombros contraindo os trapecios."},
        
        # BÍCEPS
        {"name": "Rosca Direta com Barra", "muscle_group": MuscleGroup.BICEPS, "equipment": Equipment.BARBELL, "difficulty": Difficulty.BEGINNER, "instructions": "Em pé, flexione os cotovelos subindo a barra."},
        {"name": "Rosca Alternada com Halteres", "muscle_group": MuscleGroup.BICEPS, "equipment": Equipment.DUMBBELL, "difficulty": Difficulty.BEGINNER, "instructions": "Em pé, alterne flexionando os cotovelos."},
        {"name": "Rosca Martelo", "muscle_group": MuscleGroup.BICEPS, "equipment": Equipment.DUMBBELL, "difficulty": Difficulty.BEGINNER, "instructions": "Em pé, flexione com pegada neutra (martelo)."},
        {"name": "Rosca no Banco Scott", "muscle_group": MuscleGroup.BICEPS, "equipment": Equipment.BARBELL, "difficulty": Difficulty.INTERMEDIATE, "instructions": "Apoie os braços no banco e flexione os cotovelos."},
        {"name": "Rosca Concentrada", "muscle_group": MuscleGroup.BICEPS, "equipment": Equipment.DUMBBELL, "difficulty": Difficulty.BEGINNER, "instructions": "Sentado, apoie o cotovelo na coxa e flexione."},
        
        # TRÍCEPS
        {"name": "Tríceps Testa com Barra", "muscle_group": MuscleGroup.TRICEPS, "equipment": Equipment.BARBELL, "difficulty": Difficulty.INTERMEDIATE, "instructions": "Deite, flexione os cotovelos levando a barra à testa."},
        {"name": "Tríceps Corda no Pulley", "muscle_group": MuscleGroup.TRICEPS, "equipment": Equipment.CABLE, "difficulty": Difficulty.BEGINNER, "instructions": "Em pé, empurre a corda para baixo estendendo os cotovelos."},
        {"name": "Mergulho entre Bancos", "muscle_group": MuscleGroup.TRICEPS, "equipment": Equipment.BODYWEIGHT, "difficulty": Difficulty.BEGINNER, "instructions": "Apoie as mãos no banco, desça flexionando e suba."},
        {"name": "Tríceps French Press", "muscle_group": MuscleGroup.TRICEPS, "equipment": Equipment.DUMBBELL, "difficulty": Difficulty.INTERMEDIATE, "instructions": "Deite, flexione o cotovelo levando o halter atrás da cabeça."},
        {"name": "Tríceps Coice", "muscle_group": MuscleGroup.TRICEPS, "equipment": Equipment.DUMBBELL, "difficulty": Difficulty.BEGINNER, "instructions": "Incline o torso, estenda o braço para trás."},
        
        # ABDÔMEN
        {"name": "Abdominal Crunch", "muscle_group": MuscleGroup.CORE, "equipment": Equipment.BODYWEIGHT, "difficulty": Difficulty.BEGINNER, "instructions": "Deite, contraia o abdômen elevando os ombros."},
        {"name": "Prancha", "muscle_group": MuscleGroup.CORE, "equipment": Equipment.BODYWEIGHT, "difficulty": Difficulty.BEGINNER, "instructions": "Mantenha o corpo reto apoiado nos antebraços."},
        {"name": "Elevação de Pernas", "muscle_group": MuscleGroup.CORE, "equipment": Equipment.BODYWEIGHT, "difficulty": Difficulty.INTERMEDIATE, "instructions": "Deite, eleve as pernas até 90° e desça devagar."},
        {"name": "Russian Twist", "muscle_group": MuscleGroup.CORE, "equipment": Equipment.BODYWEIGHT, "difficulty": Difficulty.BEGINNER, "instructions": "Sentado, rotacione o torso de um lado para o outro."},
        {"name": "Abdominal Infra", "muscle_group": MuscleGroup.CORE, "equipment": Equipment.BODYWEIGHT, "difficulty": Difficulty.INTERMEDIATE, "instructions": "Deite, eleve o quadril do chão contraindo o abdômen."},
    ]
    
    for ex in exercises:
        db.add(Exercise(**ex))
    db.commit()

def seed_foods(db: Session):
    if db.query(Food).count() > 0:
        return
    
    foods = [
        {"name": "Frango", "calories_per_100g": 165, "protein_g": 31, "carbs_g": 0, "fat_g": 3.6, "category": FoodCategory.PROTEIN},
        {"name": "Arroz Branco", "calories_per_100g": 130, "protein_g": 2.7, "carbs_g": 28, "fat_g": 0.3, "category": FoodCategory.CARB},
        {"name": "Ovo", "calories_per_100g": 155, "protein_g": 13, "carbs_g": 1.1, "fat_g": 11, "category": FoodCategory.PROTEIN},
        {"name": "Batata Doce", "calories_per_100g": 86, "protein_g": 1.6, "carbs_g": 20, "fat_g": 0.1, "category": FoodCategory.CARB},
        {"name": "Brócolis", "calories_per_100g": 34, "protein_g": 2.8, "carbs_g": 7, "fat_g": 0.4, "category": FoodCategory.VEGETABLE},
        {"name": "Abacate", "calories_per_100g": 160, "protein_g": 2, "carbs_g": 9, "fat_g": 15, "category": FoodCategory.FAT},
        {"name": "Leite Integral", "calories_per_100g": 61, "protein_g": 3.3, "carbs_g": 4.8, "fat_g": 3.3, "category": FoodCategory.DAIRY},
        {"name": "Pão Integral", "calories_per_100g": 265, "protein_g": 13, "carbs_g": 43, "fat_g": 4, "category": FoodCategory.GRAIN},
        {"name": "Banana", "calories_per_100g": 89, "protein_g": 1.1, "carbs_g": 23, "fat_g": 0.3, "category": FoodCategory.FRUIT},
        {"name": "Aveia", "calories_per_100g": 389, "protein_g": 16.9, "carbs_g": 66, "fat_g": 6.9, "category": FoodCategory.GRAIN},
        {"name": "Café com Leite", "calories_per_100g": 50, "protein_g": 2, "carbs_g": 5, "fat_g": 2.5, "category": FoodCategory.BEVERAGE},
        {"name": "Peixe Grelhado", "calories_per_100g": 136, "protein_g": 20, "carbs_g": 0, "fat_g": 6, "category": FoodCategory.PROTEIN},
        {"name": "Macarrão Integral", "calories_per_100g": 124, "protein_g": 5, "carbs_g": 27, "fat_g": 0.5, "category": FoodCategory.GRAIN},
        {"name": "Queijo Cottage", "calories_per_100g": 98, "protein_g": 11, "carbs_g": 3.4, "fat_g": 4.3, "category": FoodCategory.DAIRY},
        {"name": "Whey Protein", "calories_per_100g": 352, "protein_g": 80, "carbs_g": 8, "fat_g": 1.5, "category": FoodCategory.PROTEIN},
        {"name": "Castanha do Paraná", "calories_per_100g": 656, "protein_g": 14, "carbs_g": 12, "fat_g": 66, "category": FoodCategory.FAT},
        {"name": "Tomate", "calories_per_100g": 18, "protein_g": 0.9, "carbs_g": 3.9, "fat_g": 0.2, "category": FoodCategory.VEGETABLE},
        {"name": "Cenoura", "calories_per_100g": 41, "protein_g": 0.9, "carbs_g": 10, "fat_g": 0.2, "category": FoodCategory.VEGETABLE},
        {"name": "Iogurte Grego", "calories_per_100g": 59, "protein_g": 10, "carbs_g": 3.6, "fat_g": 0.7, "category": FoodCategory.DAIRY},
        {"name": "Melancia", "calories_per_100g": 30, "protein_g": 0.6, "carbs_g": 8, "fat_g": 0.2, "category": FoodCategory.FRUIT},
        {"name": "Salmão", "calories_per_100g": 208, "protein_g": 20, "carbs_g": 0, "fat_g": 13, "category": FoodCategory.PROTEIN},
        {"name": "Atum em Lata", "calories_per_100g": 116, "protein_g": 26, "carbs_g": 0, "fat_g": 1, "category": FoodCategory.PROTEIN},
        {"name": "Feijão Preto", "calories_per_100g": 127, "protein_g": 8.7, "carbs_g": 23, "fat_g": 0.5, "category": FoodCategory.PROTEIN},
        {"name": "Mandioca", "calories_per_100g": 160, "protein_g": 1.4, "carbs_g": 38, "fat_g": 0.2, "category": FoodCategory.CARB},
        {"name": "Mamão", "calories_per_100g": 43, "protein_g": 0.5, "carbs_g": 11, "fat_g": 0.3, "category": FoodCategory.FRUIT},
    ]
    
    for food in foods:
        db.add(Food(**food))
    db.commit()
