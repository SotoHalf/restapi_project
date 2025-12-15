from fastapi import APIRouter, Depends
from database import db_manager
import utils.auth as auth
from utils.meal_functions import calculate_meal_from_docs  # importas las funciones de meal_functions

router = APIRouter(prefix="/filters", tags=["Nutrient Filters"])


# ============================
# ENDPOINT GET FILTERS
# ============================
@router.get("/meals")
async def filter_meals(
    max_calories: float | None = None,
    min_protein: float | None = None,
    max_fat: float | None = None,
    max_carbs: float | None = None,
    current_user: dict = Depends(auth.get_current_user)
):
    meals_col = db_manager.db["themealdb_clean"]
    meal_ids = await meals_col.distinct("mealID")

    results = []

    for meal_id in meal_ids:
        docs = await meals_col.find({"mealID": meal_id}).to_list(1000)
        meal = await calculate_meal_from_docs(docs, db_manager.db["openfoodfacts_clean"])
        if not meal:
            continue

        n = meal["nutrients"]

        if max_calories is not None and n["energy_kcal"] > max_calories:
            continue
        if min_protein is not None and n["proteins"] < min_protein:
            continue
        if max_fat is not None and n["fat"] > max_fat:
            continue
        if max_carbs is not None and n["carbohydrates"] > max_carbs:
            continue

        results.append(meal)

    return {
        "filters": {
            "max_calories": max_calories,
            "min_protein": min_protein,
            "max_fat": max_fat,
            "max_carbs": max_carbs
        },
        "matches": len(results),
        "meals": results
    }
