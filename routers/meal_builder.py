from fastapi import APIRouter, Depends, HTTPException
from database import db_manager
import utils.auth as auth
from typing import List
from utils.meal_functions import (
    clean_ingredients,
    get_matched_ingredients,
    calculate_nutrients_for_filtered_ingredients,
    calculate_meal_nutriscore
)

router = APIRouter(prefix="/meal-builder", tags=["Meal Builder"])


@router.post("")
async def find_meals_with_nutrition(
    ingredients: List[str],
    current_user: dict = Depends(auth.get_current_user)
):
    if not ingredients:
        raise HTTPException(status_code=400, detail="Proporciona ingredientes")

    ingredients_clean = clean_ingredients(ingredients)
    if not ingredients_clean:
        raise HTTPException(status_code=400, detail="Ingredientes inválidos")

    meals_col = db_manager.db["themealdb_clean"]
    products_col = db_manager.db["openfoodfacts_clean"]

    all_meal_ids: set[int] = set()

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

    results = []

    for meal_id in list(all_meal_ids)[:15]:
        meal_ingredients = await meals_col.find({"mealID": meal_id}).to_list(length=None)
        if not meal_ingredients:
            continue

        meal_data = meal_ingredients[0]

        matched_ingredients = get_matched_ingredients(
            meal_ingredients,
            ingredients_clean
        )

        nutrients, used = await calculate_nutrients_for_filtered_ingredients(
            meal_ingredients,
            ingredients_clean,
            products_col
        )

        if used == 0:
            continue

        nutrition_score = calculate_meal_nutriscore(nutrients)

        results.append({
            "meal_id": meal_id,
            "name": meal_data.get("name", "Unknown"),
            "country": meal_data.get("country", "Unknown"),
            "image": meal_data.get("imageURL"),
            "match_percentage": round(
                (len(matched_ingredients) / len(ingredients_clean)) * 100, 1
            ),
            "matched_ingredients": matched_ingredients,
            "nutrition_score": nutrition_score,
            "calories": round(nutrients["energy_kcal"], 0),
            "protein": round(nutrients["proteins"], 1)
        })

    results.sort(
        key=lambda x: (x["match_percentage"], x["nutrition_score"]),
        reverse=True
    )

    return {
        "count": len(results),
        "results": results
    }
