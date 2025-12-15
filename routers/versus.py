from fastapi import APIRouter, Depends, HTTPException
from database import db_manager
import utils.auth as auth
from utils.meal_functions import calculate_meal_from_docs

router = APIRouter(prefix="/versus", tags=["Versus"])


async def calculate_meal(meal_id: int) -> dict | None:
    meals_col = db_manager.db["themealdb_clean"]
    products_col = db_manager.db["openfoodfacts_clean"]
    print(meal_id)
    docs = await meals_col.find({"mealID": meal_id}).to_list(1000)
    return await calculate_meal_from_docs(docs, products_col)


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
