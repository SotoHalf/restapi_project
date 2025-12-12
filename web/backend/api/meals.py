from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import httpx
from datetime import datetime, timedelta
import json

router = APIRouter(prefix="/api/meals", tags=["meals"])

# Datos simulados para TheMealDB (hasta que implementes la API real)
MOCK_MEALS = [
    {
        "id": "52772",
        "name": "Teriyaki Chicken Casserole",
        "category": "Chicken",
        "area": "Japanese",
        "calories": 450,
        "protein": 35,
        "carbs": 40,
        "fat": 15,
        "ingredients": ["chicken", "soy sauce", "ginger", "garlic", "rice"],
        "health_score": 78,
        "image": "https://www.themealdb.com/images/media/meals/wvpsxx1468256321.jpg"
    },
    {
        "id": "52773",
        "name": "Mediterranean Salad",
        "category": "Vegetarian",
        "area": "Mediterranean",
        "calories": 320,
        "protein": 12,
        "carbs": 25,
        "fat": 18,
        "ingredients": ["lettuce", "tomato", "cucumber", "olives", "feta"],
        "health_score": 92,
        "image": "https://www.themealdb.com/images/media/meals/wvpsxx1468256321.jpg"
    },
    # Añade más comidas simuladas...
]

@router.get("/search")
async def search_meals(
    query: str = Query("", description="Search term"),
    category: Optional[str] = None,
    max_calories: Optional[int] = None,
    min_health_score: Optional[int] = None
):
    """Buscar comidas con filtros"""
    filtered_meals = MOCK_MEALS
    
    if query:
        filtered_meals = [m for m in filtered_meals if query.lower() in m["name"].lower()]
    
    if category:
        filtered_meals = [m for m in filtered_meals if m["category"] == category]
    
    if max_calories:
        filtered_meals = [m for m in filtered_meals if m["calories"] <= max_calories]
    
    if min_health_score:
        filtered_meals = [m for m in filtered_meals if m["health_score"] >= min_health_score]
    
    return {
        "meals": filtered_meals,
        "count": len(filtered_meals),
        "query": query,
        "filters": {
            "category": category,
            "max_calories": max_calories,
            "min_health_score": min_health_score
        }
    }

@router.get("/{meal_id}")
async def get_meal_detail(meal_id: str):
    """Obtener detalles de una comida específica"""
    meal = next((m for m in MOCK_MEALS if m["id"] == meal_id), None)
    
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    
    # Añadir información nutricional simulada de OpenFoodFacts
    meal["nutrition"] = {
        "energy_kcal": meal["calories"],
        "protein_g": meal["protein"],
        "carbohydrates_g": meal["carbs"],
        "fat_g": meal["fat"],
        "fiber_g": round(meal["protein"] * 0.3, 1),
        "sugar_g": round(meal["carbs"] * 0.2, 1),
        "salt_g": 1.2,
        "nutri_score": "B" if meal["health_score"] > 80 else "C",
        "nova_group": 3  # Simulado
    }
    
    return meal

@router.get("/categories/stats")
async def get_categories_stats():
    """Estadísticas por categoría de comida"""
    categories = {}
    for meal in MOCK_MEALS:
        cat = meal["category"]
        if cat not in categories:
            categories[cat] = {
                "count": 0,
                "avg_calories": 0,
                "avg_health_score": 0,
                "total_protein": 0
            }
        
        categories[cat]["count"] += 1
        categories[cat]["avg_calories"] += meal["calories"]
        categories[cat]["avg_health_score"] += meal["health_score"]
        categories[cat]["total_protein"] += meal["protein"]
    
    # Calcular promedios
    for cat in categories:
        categories[cat]["avg_calories"] = round(categories[cat]["avg_calories"] / categories[cat]["count"])
        categories[cat]["avg_health_score"] = round(categories[cat]["avg_health_score"] / categories[cat]["count"])
    
    return categories