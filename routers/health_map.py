from fastapi import APIRouter, Depends, HTTPException
from database import db_manager
import utils.auth as auth
import re

router = APIRouter(prefix="/health-map", tags=["Health Map"])


# =========================
# ESXTRACT GRAMOS
# =========================
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


# =========================
# NUTRISCORE OF A PLATE
# =========================
def calculate_meal_nutriscore(nutrients: dict) -> float:
    score = (
        nutrients["proteins"] * 4
        - nutrients["fat"] * 2
        - nutrients["salt"] * 3
        - nutrients["energy_kcal"] * 0.05
    )

    score *= 10
    return max(1, min(100, round(score, 2)))


# =========================
# RECALCULCULATE MAP
# =========================
@router.post("/recalculate", status_code=202)
async def recalculate_health_map(
    current_user: dict = Depends(auth.get_current_user)
):
    if current_user["role"] != "role_admin":
        raise HTTPException(status_code=403, detail="Admin only")

    meals_col = db_manager.db["themealdb_clean"]
    products_col = db_manager.db["openfoodfacts_clean"]
    result_col = db_manager.db["precalculated_health_map"]

    meals = await meals_col.find().to_list(length=None)

    meals_by_id = {}
    for m in meals:
        meals_by_id.setdefault(m["mealID"], []).append(m)

    country_scores = {}

    for ingredients in meals_by_id.values():
        country = ingredients[0]["country"]

        nutrients = {
            "energy_kcal": 0.0,
            "fat": 0.0,
            "carbohydrates": 0.0,
            "proteins": 0.0,
            "salt": 0.0
        }

        used = 0

        for ing in ingredients:
            grams = extract_grams(ing.get("measure"))
            name = ing.get("ingredient")

            if not grams or not name:
                continue

            product = await products_col.find_one({
                "search_term": {"$regex": f"^{name.lower()}", "$options": "i"}
            })

            if not product:
                continue

            factor = grams / 100

            nutrients["energy_kcal"] += (product.get("energy_kcal_100g", 0) or 0) * factor
            nutrients["fat"] += (product.get("fat_100g", 0) or 0) * factor
            nutrients["carbohydrates"] += (product.get("carbohydrates_100g", 0) or 0) * factor
            nutrients["proteins"] += (product.get("proteins_100g", 0) or 0) * factor
            nutrients["salt"] += (product.get("salt_100g", 0) or 0) * factor

            used += 1

        if used == 0:
            continue

        meal_score = calculate_meal_nutriscore(nutrients)
        country_scores.setdefault(country, []).append(meal_score)

    # RESULTS
    result = []
    for country, scores in country_scores.items():
        result.append({
            "country": country,
            "avg_nutriscore": round(sum(scores) / len(scores), 2),
            "meals_count": len(scores)
        })

    result.sort(key=lambda x: x["avg_nutriscore"], reverse=True)

    await result_col.delete_many({})
    if result:
        await result_col.insert_many(result)

    return {"status": "ok", "countries": len(result)}


# =========================
# GET MAP
# =========================
@router.get("/")
async def get_health_map():
    col = db_manager.db["precalculated_health_map"]
    data = await col.find().to_list(length=None)

    for d in data:
        d["_id"] = str(d["_id"])

    return {
        "count": len(data),
        "data": data
    }
