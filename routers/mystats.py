from fastapi import APIRouter, Depends, HTTPException
from database import db_manager
import utils.auth as auth
from datetime import datetime, date
from utils.meal_functions import extract_grams, calculate_meal_nutriscore
import re

router = APIRouter(prefix="/mystats", tags=["My Stats"])

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

    return {
        "meal_id": meal_id,
        "meal_name": docs[0]["name"],
        "nutriscore": calculate_meal_nutriscore(totals)
    }


# =========================================================
# ADD FOOD FOR A USER
# =========================================================

@router.post("/add-meal")
async def add_meal_to_my_day(
    meal_id: int,
    current_user: dict = Depends(auth.get_current_user)
):
    meal = await calculate_meal(meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found or no valid ingredients")

    mystats_col = db_manager.db["mystats"]
    today = date.today().isoformat()

    user_id = get_user_id(current_user)

    await mystats_col.insert_one({
        "user_id": user_id,
        "meal_id": meal_id,
        "meal_name": meal["meal_name"],
        "nutriscore": meal["nutriscore"],
        "date": today,
        "created_at": datetime.utcnow()
    })

    return {
        "status": "ok",
        "user_id": user_id,
        "meal": meal["meal_name"],
        "nutriscore": meal["nutriscore"],
        "date": today
    }
    
def get_user_id(current_user: dict) -> str:
    for key in ("id", "sub", "user_id", "_id"):
        if key in current_user:
            return str(current_user[key])
    raise HTTPException(
        status_code=500,
        detail="User ID not found in token"
    )

@router.get("/all")
async def get_all_my_meals(current_user: dict = Depends(auth.get_current_user)):
    """
    Devuelve todos los registros de comidas guardadas por el usuario.
    """
    user_id = get_user_id(current_user)
    mystats_col = db_manager.db["mystats"]

    docs = await mystats_col.find({"user_id": user_id}).sort("created_at", -1).to_list(1000)

    results = [
        {
            "meal_id": d["meal_id"],
            "meal_name": d["meal_name"],
            "nutriscore": d["nutriscore"],
            "date": d.get("date"),
            "created_at": d.get("created_at")
        }
        for d in docs
    ]

    return {
        "user_id": user_id,
        "count": len(results),
        "meals": results
    }


@router.delete("/clear-all")
async def clear_all_meals(
    current_user: dict = Depends(auth.get_current_user)
):
    """
    Delete ALL logged meals for the current user
    """
    mystats_col = db_manager.db["mystats"]
    user_id = get_user_id(current_user)
    
    # Count n0 of meals
    meal_count = await mystats_col.count_documents({"user_id": user_id})
    
    if meal_count == 0:
        raise HTTPException(status_code=404, detail="No meals found to delete")
    
    # Delete user's meals
    result = await mystats_col.delete_many({"user_id": user_id})
    
    if result.deleted_count > 0:
        return {
            "status": "ok",
            "message": f"Successfully deleted {result.deleted_count} meal logs",
            "deleted_count": result.deleted_count
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to delete meal logs")

