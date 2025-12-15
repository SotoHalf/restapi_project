from fastapi import APIRouter, Depends, HTTPException
from database import db_manager
import utils.auth as auth
from typing import List

router = APIRouter(prefix="/meal-builder", tags=["Meal Builder"])

# =========================
# ENDPOINT with nutriscore
# =========================
@router.post("")
async def find_meals_with_nutrition(
    ingredients: List[str],
    current_user: dict = Depends(auth.get_current_user)
):
    if not ingredients:
        raise HTTPException(status_code=400, detail="Proporciona ingredientes")
    
    ingredients_clean = [ing.strip().lower() for ing in ingredients if ing.strip()]
    
    meals_col = db_manager.db["themealdb_clean"]
    products_col = db_manager.db["openfoodfacts_clean"]
    
    # Find
    all_meal_ids = set()
    
    for ingredient in ingredients_clean:
        matching = await meals_col.find({
            "ingredient": {"$regex": ingredient, "$options": "i"}
        }).to_list(length=30)
        
        for meal in matching:
            meal_id = meal.get("mealID")
            if meal_id:
                all_meal_ids.add(meal_id)
    
    if not all_meal_ids:
        return {"count": 0, "results": []}
    
    # Procces
    results = []
    
    for meal_id in list(all_meal_ids)[:15]:
        meal_ingredients = await meals_col.find({"mealID": meal_id}).to_list(length=None)
        
        if not meal_ingredients:
            continue
        
        meal_data = meal_ingredients[0]
        
        matched_ingredients = []
        for meal_ing in meal_ingredients:
            meal_ing_name = meal_ing.get("ingredient", "").lower()
            for search_ing in ingredients_clean:
                if search_ing in meal_ing_name and search_ing not in matched_ingredients:
                    matched_ingredients.append(search_ing)
        
        total_calories = 0
        total_protein = 0
        
        for meal_ing in meal_ingredients:
            ingredient_name = meal_ing.get("ingredient", "").lower()
            measure = meal_ing.get("measure")
            
            # Search
            should_search = any(search_ing in ingredient_name for search_ing in ingredients_clean)
            
            if should_search:
                product = await products_col.find_one({
                    "search_term": ingredient_name
                })
                if product:
                    grams = 100
                    if isinstance(measure, (int, float)):
                        grams = float(measure)

                    factor = grams / 100
                    total_calories += (product.get("energy_kcal_100g", 0) or 0) * factor
                    total_protein += (product.get("proteins_100g", 0) or 0) * factor
        
        nutrition_score = 50
        
        if total_calories > 0:
            if total_calories < 500:
                nutrition_score += 20
            elif total_calories < 800:
                nutrition_score += 10
        
        if total_protein > 0:
            if total_protein > 30:
                nutrition_score += 20
            elif total_protein > 20:
                nutrition_score += 10
        
        nutrition_score = max(1, min(100, nutrition_score))
        
        results.append({
            "meal_id": meal_id,
            "name": meal_data.get("name", "Unknown"),
            "country": meal_data.get("country", "Unknown"),
            "image": meal_data.get("imageURL"),
            "match_percentage": round((len(matched_ingredients) / len(ingredients_clean)) * 100, 1),
            "matched_ingredients": matched_ingredients,
            "nutrition_score": nutrition_score,
            "calories": round(total_calories, 0),
            "protein": round(total_protein, 1)
        })
    
    # Order
    results.sort(key=lambda x: (x["match_percentage"], x["nutrition_score"]), reverse=True)
    
    return {
        "count": len(results),
        "results": results
    }