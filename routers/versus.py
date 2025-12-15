from fastapi import APIRouter, Depends, HTTPException
from database import db_manager
import utils.auth as auth
import re

router = APIRouter(prefix="/versus", tags=["Versus"])


# ============================
# EXTRACT GRAMS
# ============================
def extract_grams(measure) -> float | None:
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
# CALCULATE NUTRISCORE OF A PLATE
# ============================
def calculate_meal_nutriscore(nutrients: dict) -> float:
    """
    NutriScore inventado (1–100)
    """
    score = (
        nutrients["proteins"] * 5
        - nutrients["fat"] * 2
        - nutrients["salt"] * 3
        - (nutrients["energy_kcal"] * 0.05)
    )

    return round(max(1, min(100, score)), 2)


# ============================
# CALCULATE NUTRIENTES OF A PLATE
# ============================
async def calculate_meal(meal_id: int) -> dict | None:
    meals_col = db_manager.db["themealdb_clean"]
    products_col = db_manager.db["openfoodfacts_clean"]

    docs = await meals_col.find({"mealID": meal_id}).to_list(1000)
    if not docs:
        return None

    totals = {
        "energy_kcal": 0.0,
        "fat": 0.0,
        "carbohydrates": 0.0,
        "proteins": 0.0,
        "salt": 0.0
    }

    used = 0

    for d in docs:
        ingredient = d.get("ingredient")
        grams = extract_grams(d.get("measure"))

        if not ingredient or not grams:
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

        used += 1

    if used == 0:
        return None

    nutriscore = calculate_meal_nutriscore(totals)

    return {
        "mealID": meal_id,
        "name": docs[0]["name"],
        "country": docs[0]["country"],
        "image": docs[0]["imageURL"],
        "nutrients": {k: round(v, 2) for k, v in totals.items()},
        "nutriscore": nutriscore,
        "ingredients_used": used
    }


# ============================
# ENDPOINT VERSUS
# ============================
@router.get("/compare")
async def compare_meals(
    meal1_id: int,
    meal2_id: int,
    current_user: dict = Depends(auth.get_current_user)
):
    meal1 = await calculate_meal(meal1_id)
    meal2 = await calculate_meal(meal2_id)

    if not meal1 or not meal2:
        raise HTTPException(status_code=404, detail="Meal not found or no valid ingredients")

    if meal1["nutriscore"] > meal2["nutriscore"]:
        winner = meal1["name"]
    elif meal2["nutriscore"] > meal1["nutriscore"]:
        winner = meal2["name"]
    else:
        winner = "Tie"

    return {
        "meal_1": meal1,
        "meal_2": meal2,
        "winner": winner
    }
