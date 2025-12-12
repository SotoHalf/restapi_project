from fastapi import APIRouter, Query
from typing import List, Optional
import random

router = APIRouter(prefix="/api/food", tags=["food"])

# Datos simulados para OpenFoodFacts
MOCK_FOOD_PRODUCTS = [
    {
        "id": "3017620422003",
        "product_name": "Organic Whole Wheat Bread",
        "brands": "Nature's Own",
        "categories": "en:breads",
        "nutriments": {
            "energy-kcal_100g": 250,
            "proteins_100g": 9.0,
            "carbohydrates_100g": 45.0,
            "fat_100g": 2.5,
            "fiber_100g": 7.0,
            "sugars_100g": 5.0,
            "salt_100g": 0.8
        },
        "nutri_score": "A",
        "nova_group": 1,
        "ecoscore": "B",
        "health_score": 85
    },
    # Añade más productos...
]

@router.get("/products/search")
async def search_food_products(
    query: str = Query("", description="Search for food products"),
    category: Optional[str] = None,
    min_nutri_score: Optional[str] = None,
    max_nova_group: Optional[int] = None
):
    """Buscar productos alimenticios"""
    filtered = MOCK_FOOD_PRODUCTS
    
    if query:
        filtered = [p for p in filtered if query.lower() in p.get("product_name", "").lower()]
    
    if category:
        filtered = [p for p in filtered if category in p.get("categories", "")]
    
    if min_nutri_score:
        # Nutri-Score: A > B > C > D > E
        score_order = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1}
        min_val = score_order.get(min_nutri_score.upper(), 0)
        filtered = [p for p in filtered if score_order.get(p.get("nutri_score", "E"), 0) >= min_val]
    
    if max_nova_group:
        filtered = [p for p in filtered if p.get("nova_group", 4) <= max_nova_group]
    
    return {
        "products": filtered[:50],  # Limitar resultados
        "count": len(filtered),
        "query": query
    }

@router.get("/ingredients/healthiest")
async def get_healthiest_ingredients(limit: int = Query(10, ge=1, le=50)):
    """Obtener ingredientes más saludables"""
    # Simular análisis de ingredientes
    ingredients = [
        {"name": "Spinach", "health_score": 95, "nutrients": {"iron": "high", "vitamin_k": "high"}},
        {"name": "Salmon", "health_score": 90, "nutrients": {"omega_3": "high", "protein": "high"}},
        {"name": "Avocado", "health_score": 88, "nutrients": {"healthy_fats": "high", "fiber": "high"}},
        {"name": "Quinoa", "health_score": 87, "nutrients": {"protein": "high", "fiber": "high"}},
        {"name": "Blueberries", "health_score": 92, "nutrients": {"antioxidants": "very high"}},
        {"name": "Almonds", "health_score": 85, "nutrients": {"vitamin_e": "high", "healthy_fats": "high"}},
        {"name": "Broccoli", "health_score": 91, "nutrients": {"vitamin_c": "high", "fiber": "high"}},
        {"name": "Greek Yogurt", "health_score": 84, "nutrients": {"protein": "very high", "calcium": "high"}},
        {"name": "Sweet Potato", "health_score": 86, "nutrients": {"vitamin_a": "very high", "fiber": "high"}},
        {"name": "Eggs", "health_score": 82, "nutrients": {"protein": "high", "choline": "high"}},
    ]
    
    return sorted(ingredients, key=lambda x: x["health_score"], reverse=True)[:limit]