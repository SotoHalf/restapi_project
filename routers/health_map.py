from fastapi import APIRouter, Depends, HTTPException
from database import db_manager
import utils.auth as auth
from utils.meal_functions import calculate_nutrients_for_ingredients, calculate_meal_nutriscore

router = APIRouter(prefix="/health-map", tags=["Health Map"])


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
        nutrients, used = await calculate_nutrients_for_ingredients(ingredients, products_col)

        if used == 0:
            continue

        meal_score = calculate_meal_nutriscore(nutrients)
        country_scores.setdefault(country, []).append(meal_score)

    result = [
        {
            "country": country,
            "avg_nutriscore": round(sum(scores) / len(scores), 2),
            "meals_count": len(scores)
        }
        for country, scores in country_scores.items()
    ]

    result.sort(key=lambda x: x["avg_nutriscore"], reverse=True)

    await result_col.delete_many({})
    if result:
        await result_col.insert_many(result)

    return {"status": "ok", "countries": len(result)}


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
