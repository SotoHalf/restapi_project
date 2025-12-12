from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional, Dict
import random
from datetime import datetime, timedelta
from backend import auth

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Datos simulados para análisis
MOCK_COUNTRIES_HEALTH = [
    {"country": "Japan", "health_score": 92, "avg_calories": 1850, "common_dish": "Sushi"},
    {"country": "Italy", "health_score": 88, "avg_calories": 2100, "common_dish": "Mediterranean Salad"},
    {"country": "Greece", "health_score": 87, "avg_calories": 1950, "common_dish": "Greek Salad"},
    {"country": "Spain", "health_score": 85, "avg_calories": 2200, "common_dish": "Gazpacho"},
    {"country": "France", "health_score": 82, "avg_calories": 2250, "common_dish": "Ratatouille"},
    {"country": "USA", "health_score": 65, "avg_calories": 2650, "common_dish": "Hamburger"},
    {"country": "Mexico", "health_score": 78, "avg_calories": 2350, "common_dish": "Guacamole"},
    {"country": "India", "health_score": 80, "avg_calories": 2050, "common_dish": "Dal"},
    {"country": "China", "health_score": 83, "avg_calories": 2150, "common_dish": "Stir Fry"},
    {"country": "Brazil", "health_score": 76, "avg_calories": 2400, "common_dish": "Feijoada"},
]

MOCK_USER_MEALS = [
    {
        "id": "user_meal_001",
        "user_id": "usr_123",
        "date": "2024-03-15",
        "meal_type": "breakfast",
        "dish_name": "Greek Yogurt with Berries",
        "calories": 320,
        "protein": 25,
        "carbs": 35,
        "fat": 8,
        "health_score": 88,
        "ingredients": ["greek yogurt", "blueberries", "almonds", "honey"]
    },
    # Más comidas simuladas...
]

@router.get("/calorie-trends")
async def get_calorie_trends(
    current_user: dict = Depends(auth.get_current_user),
    days: int = Query(7, description="Número de días para analizar")
):
    """Obtener tendencias calóricas del usuario"""
    user_id = current_user.get("user_id", "demo_user")
    
    # Generar datos simulados para los últimos 'days' días
    trends = []
    for i in range(days, 0, -1):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        
        # Comidas del día
        daily_meals = [
            meal for meal in MOCK_USER_MEALS 
            if meal["date"] == date and meal["user_id"] == user_id
        ]
        
        total_calories = sum(meal["calories"] for meal in daily_meals)
        avg_health_score = sum(meal["health_score"] for meal in daily_meals) / len(daily_meals) if daily_meals else 0
        
        trends.append({
            "date": date,
            "total_calories": total_calories,
            "meal_count": len(daily_meals),
            "avg_health_score": round(avg_health_score, 1),
            "meals": daily_meals[:3]  # Primeras 3 comidas
        })
    
    # Calcular estadísticas
    calories_list = [day["total_calories"] for day in trends]
    avg_calories = sum(calories_list) / len(calories_list) if calories_list else 0
    max_calories = max(calories_list) if calories_list else 0
    min_calories = min(calories_list) if calories_list else 0
    
    return {
        "user_id": user_id,
        "period_days": days,
        "trends": trends,
        "statistics": {
            "average_calories": round(avg_calories),
            "max_calories": max_calories,
            "min_calories": min_calories,
            "total_meals": sum(day["meal_count"] for day in trends)
        }
    }

@router.get("/health-map")
async def get_health_map(
    min_score: int = Query(0, description="Puntuación mínima de salud"),
    max_score: int = Query(100, description="Puntuación máxima de salud"),
    limit: int = Query(20, description="Límite de resultados")
):
    """Obtener mapa de salud por países"""
    filtered_countries = [
        country for country in MOCK_COUNTRIES_HEALTH
        if min_score <= country["health_score"] <= max_score
    ]
    
    # Ordenar por puntuación de salud
    filtered_countries.sort(key=lambda x: x["health_score"], reverse=True)
    
    # Calcular estadísticas globales
    avg_health = sum(c["health_score"] for c in filtered_countries) / len(filtered_countries) if filtered_countries else 0
    avg_calories = sum(c["avg_calories"] for c in filtered_countries) / len(filtered_countries) if filtered_countries else 0
    
    return {
        "countries": filtered_countries[:limit],
        "statistics": {
            "total_countries": len(filtered_countries),
            "average_health_score": round(avg_health, 1),
            "average_calories": round(avg_calories),
            "healthiest_country": filtered_countries[0] if filtered_countries else None,
            "least_healthy_country": filtered_countries[-1] if filtered_countries else None
        }
    }

@router.post("/meal-builder/generate")
async def generate_meal(
    current_user: dict = Depends(auth.get_current_user),
    preferences: Optional[Dict] = None
):
    """Generar una comida saludable basada en preferencias"""
    if preferences is None:
        preferences = {}
    
    # Ingredientes saludables base
    healthy_ingredients = [
        {"name": "Spinach", "category": "vegetable", "health_score": 95},
        {"name": "Salmon", "category": "protein", "health_score": 90},
        {"name": "Quinoa", "category": "grain", "health_score": 87},
        {"name": "Avocado", "category": "fruit", "health_score": 88},
        {"name": "Sweet Potato", "category": "vegetable", "health_score": 86},
        {"name": "Chicken Breast", "category": "protein", "health_score": 85},
        {"name": "Brown Rice", "category": "grain", "health_score": 82},
        {"name": "Broccoli", "category": "vegetable", "health_score": 91},
        {"name": "Almonds", "category": "nuts", "health_score": 85},
        {"name": "Blueberries", "category": "fruit", "health_score": 92},
    ]
    
    # Filtrar por preferencias si existen
    if preferences.get("category"):
        healthy_ingredients = [
            ing for ing in healthy_ingredients 
            if ing["category"] == preferences["category"]
        ]
    
    # Seleccionar ingredientes aleatorios
    num_ingredients = min(len(healthy_ingredients), preferences.get("ingredient_count", 5))
    selected_ingredients = random.sample(healthy_ingredients, num_ingredients)
    
    # Calcular valores nutricionales estimados
    total_health_score = sum(ing["health_score"] for ing in selected_ingredients) / num_ingredients
    
    # Estimaciones nutricionales basadas en ingredientes
    estimated_nutrition = {
        "calories": num_ingredients * 120,  # Estimación simple
        "protein": num_ingredients * 8,
        "carbs": num_ingredients * 15,
        "fat": num_ingredients * 5,
        "fiber": num_ingredients * 3
    }
    
    # Sugerir nombre del plato basado en ingredientes
    main_ingredient = selected_ingredients[0]["name"] if selected_ingredients else "Healthy"
    dish_names = [
        f"{main_ingredient} Bowl",
        "Power Salad",
        "Healthy Medley",
        "Nutrition Boost Plate"
    ]
    
    return {
        "generated_meal": {
            "name": random.choice(dish_names),
            "ingredients": selected_ingredients,
            "estimated_nutrition": estimated_nutrition,
            "health_score": round(total_health_score),
            "preparation_time": f"{num_ingredients * 5} minutes",
            "difficulty": "Easy" if num_ingredients <= 3 else "Medium"
        },
        "suggestions": [
            "Add lemon juice for extra flavor",
            "Serve with whole grain bread",
            "Consider adding herbs for antioxidants"
        ]
    }

@router.get("/ingredient-comparison")
async def compare_ingredients(
    ingredient1: str = Query(..., description="Primer ingrediente"),
    ingredient2: str = Query(..., description="Segundo ingrediente")
):
    """Comparar dos ingredientes por saludabilidad"""
    # Base de datos simulada de ingredientes
    INGREDIENT_DB = {
        "spinach": {"health_score": 95, "nutrients": ["iron", "vitamin_k", "calcium"], "calories_per_100g": 23},
        "salmon": {"health_score": 90, "nutrients": ["omega_3", "protein", "vitamin_d"], "calories_per_100g": 208},
        "avocado": {"health_score": 88, "nutrients": ["healthy_fats", "fiber", "potassium"], "calories_per_100g": 160},
        "quinoa": {"health_score": 87, "nutrients": ["protein", "fiber", "magnesium"], "calories_per_100g": 120},
        "white_bread": {"health_score": 45, "nutrients": ["carbs", "gluten"], "calories_per_100g": 265},
        "soda": {"health_score": 20, "nutrients": ["sugar"], "calories_per_100g": 140},
        "broccoli": {"health_score": 91, "nutrients": ["vitamin_c", "fiber", "calcium"], "calories_per_100g": 34},
        "almonds": {"health_score": 85, "nutrients": ["vitamin_e", "healthy_fats", "magnesium"], "calories_per_100g": 575},
    }
    
    ing1_data = INGREDIENT_DB.get(ingredient1.lower())
    ing2_data = INGREDIENT_DB.get(ingredient2.lower())
    
    if not ing1_data or not ing2_data:
        missing = []
        if not ing1_data: missing.append(ingredient1)
        if not ing2_data: missing.append(ingredient2)
        raise HTTPException(
            status_code=404, 
            detail=f"Ingredients not found in database: {', '.join(missing)}"
        )
    
    # Determinar cuál es más saludable
    healthier = ingredient1 if ing1_data["health_score"] > ing2_data["health_score"] else ingredient2
    score_difference = abs(ing1_data["health_score"] - ing2_data["health_score"])
    
    return {
        "comparison": {
            "ingredient1": {
                "name": ingredient1,
                **ing1_data
            },
            "ingredient2": {
                "name": ingredient2,
                **ing2_data
            }
        },
        "analysis": {
            "healthier_ingredient": healthier,
            "health_score_difference": score_difference,
            "recommendation": f"Prefiere {healthier} sobre {'el otro' if score_difference > 20 else 'ambos' if score_difference < 5 else 'la otra opción'}",
            "calorie_difference": abs(ing1_data["calories_per_100g"] - ing2_data["calories_per_100g"])
        }
    }

@router.get("/nutrient-filters")
async def filter_by_nutrients(
    max_calories: Optional[int] = Query(None, description="Calorías máximas"),
    min_protein: Optional[int] = Query(None, description="Proteína mínima (g)"),
    max_carbs: Optional[int] = Query(None, description="Carbohidratos máximos (g)"),
    min_health_score: Optional[int] = Query(None, description="Puntuación mínima de salud")
):
    """Filtrar comidas por criterios nutricionales"""
    # Base de datos simulada de comidas
    MEALS_DB = [
        {"id": "1", "name": "Grilled Chicken Salad", "calories": 350, "protein": 35, "carbs": 15, "health_score": 85},
        {"id": "2", "name": "Salmon with Quinoa", "calories": 420, "protein": 28, "carbs": 40, "health_score": 88},
        {"id": "3", "name": "Vegetable Stir Fry", "calories": 280, "protein": 12, "carbs": 35, "health_score": 82},
        {"id": "4", "name": "Greek Yogurt Bowl", "calories": 320, "protein": 25, "carbs": 35, "health_score": 87},
        {"id": "5", "name": "Avocado Toast", "calories": 250, "protein": 8, "carbs": 30, "health_score": 80},
        {"id": "6", "name": "Protein Smoothie", "calories": 180, "protein": 20, "carbs": 25, "health_score": 84},
        {"id": "7", "name": "Mediterranean Wrap", "calories": 380, "protein": 18, "carbs": 45, "health_score": 79},
        {"id": "8", "name": "Berry Oatmeal", "calories": 210, "protein": 10, "carbs": 40, "health_score": 86},
    ]
    
    filtered_meals = MEALS_DB
    
    # Aplicar filtros
    if max_calories is not None:
        filtered_meals = [meal for meal in filtered_meals if meal["calories"] <= max_calories]
    
    if min_protein is not None:
        filtered_meals = [meal for meal in filtered_meals if meal["protein"] >= min_protein]
    
    if max_carbs is not None:
        filtered_meals = [meal for meal in filtered_meals if meal["carbs"] <= max_carbs]
    
    if min_health_score is not None:
        filtered_meals = [meal for meal in filtered_meals if meal["health_score"] >= min_health_score]
    
    # Ordenar por saludabilidad
    filtered_meals.sort(key=lambda x: x["health_score"], reverse=True)
    
    # Calcular estadísticas de los resultados
    if filtered_meals:
        avg_calories = sum(m["calories"] for m in filtered_meals) / len(filtered_meals)
        avg_protein = sum(m["protein"] for m in filtered_meals) / len(filtered_meals)
        avg_health = sum(m["health_score"] for m in filtered_meals) / len(filtered_meals)
    else:
        avg_calories = avg_protein = avg_health = 0
    
    return {
        "filters_applied": {
            "max_calories": max_calories,
            "min_protein": min_protein,
            "max_carbs": max_carbs,
            "min_health_score": min_health_score
        },
        "results": {
            "count": len(filtered_meals),
            "meals": filtered_meals,
            "averages": {
                "calories": round(avg_calories),
                "protein": round(avg_protein, 1),
                "health_score": round(avg_health, 1)
            }
        },
        "recommendations": [
            "Try adding more vegetables for fiber",
            "Consider lean protein sources",
            "Watch portion sizes for calorie control"
        ] if filtered_meals else ["No meals match your criteria"]
    }