from fastapi import APIRouter, Depends
from database import db_manager
import utils.auth as auth
import re

router = APIRouter(prefix="/filters", tags=["Nutrient Filters"])

# ============================
# EXTRACT GRAMS
# ============================
def extract_grams(measure) -> float | None:
    """
    Extrae gramos numéricos:
    '100' -> 100
    '50 g' -> 50
    '30' -> 30
    '1 tablespoon' -> None
    """
    if not measure:
        return None

    if isinstance(measure, (int, float)):
        return float(measure)

    measure = str(measure).lower()

    match = re.search(r"(\d+(\.\d+)?)", measure)
    if not match:
        return None

    return float(match.group(1))


# ============================
# CALCULATE NUTRIENTES OF A PLATE
# ============================
async def calculate_meal_nutrients(meal_id: int) -> dict | None:
    meals_col = db_manager.db["themealdb_clean"]
    products_col = db_manager.db["openfoodfacts_clean"]

    ingredients_docs = await meals_col.find(
        {"mealID": meal_id}
    ).to_list(1000)

    if not ingredients_docs:
        return None

    totals = {
        "energy_kcal": 0.0,
        "fat": 0.0,
        "carbohydrates": 0.0,
        "proteins": 0.0,
        "salt": 0.0
    }

    used_ingredients = 0

    for doc in ingredients_docs:
        ingredient = doc.get("ingredient")
        measure = doc.get("measure")

        if not ingredient:
            continue

        grams = extract_grams(measure)
        if not grams:
            continue

        product = await products_col.find_one({
            "search_term": ingredient.strip().lower()
        })

        if not product:
            continue

        factor = grams / 100

        totals["energy_kcal"] += (product.get("energy_kcal_100g", 0) or 0) * factor
        totals["fat"] += (product.get("fat_100g", 0) or 0) * factor
        totals["carbohydrates"] += (product.get("carbohydrates_100g", 0) or 0) * factor
        totals["proteins"] += (product.get("proteins_100g", 0) or 0) * factor
        totals["salt"] += (product.get("salt_100g", 0) or 0) * factor

        used_ingredients += 1

    if used_ingredients == 0:
        return None

    return {
        "mealID": meal_id,
        "name": ingredients_docs[0]["name"],
        "country": ingredients_docs[0]["country"],
        "image": ingredients_docs[0]["imageURL"],
        "nutrients": {
            k: round(v, 2) for k, v in totals.items()
        },
        "ingredients_used": used_ingredients
    }


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
        meal = await calculate_meal_nutrients(meal_id)
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
