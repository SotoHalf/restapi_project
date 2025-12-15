import re
import math

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
# CALCULATE MEAL NUTRISCORE
# ============================

def calculate_meal_nutriscore(nutrients):
    # 0 - 100
    energy = nutrients.get("energy_kcal", 0)
    fat = nutrients.get("fat", 0)
    carbs = nutrients.get("carbohydrates", 0)
    salt = nutrients.get("salt", 0)
    proteins = nutrients.get("proteins", 0)
    
    neg_energy = math.log1p(energy)
    neg_fat = math.log1p(fat)
    neg_salt = math.log1p(salt)
    pos_proteins = math.log1p(proteins)
    pos_carbs = math.log1p(carbs)
    
    w_energy = 1.0
    w_fat = 2.5
    w_salt = 3.0
    w_proteins = 4.0
    w_carbs = 2.0
    
    negative_score = w_energy*neg_energy + w_fat*neg_fat + w_salt*neg_salt
    positive_score = w_proteins*pos_proteins + w_carbs*pos_carbs
    
    score = positive_score - negative_score
    
    normalized = 50 + score * 10
    normalized = max(0, min(100, normalized))
    
    return round(normalized)


# ============================
# BASE NUTRIENT CALCULATOR
# ============================
async def _calculate_nutrients(
    ingredients: list,
    products_col,
    ingredient_filter: list[str] | None = None
) -> tuple[dict, int]:
    totals = {
        "energy_kcal": 0.0,
        "fat": 0.0,
        "carbohydrates": 0.0,
        "proteins": 0.0,
        "salt": 0.0
    }
    used = 0

    for ing in ingredients:
        name = (ing.get("ingredient") or "").lower()
        grams = extract_grams(ing.get("measure"))

        if not name or not grams:
            continue

        if ingredient_filter and not any(f in name for f in ingredient_filter):
            continue

        product = await products_col.find_one({
            "search_term": {"$regex": f"^{name}", "$options": "i"}
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

    return totals, used


# ============================
# PUBLIC WRAPPERS
# ============================
async def calculate_nutrients_for_ingredients(ingredients: list, products_col):
    return await _calculate_nutrients(ingredients, products_col)


async def calculate_nutrients_for_filtered_ingredients(
    meal_ingredients: list,
    search_ingredients: list[str],
    products_col
):
    return await _calculate_nutrients(
        meal_ingredients,
        products_col,
        ingredient_filter=search_ingredients
    )


# ============================
# MEAL FROM DOCS
# ============================
async def calculate_meal_from_docs(docs: list, products_col) -> dict | None:
    if not docs:
        return None

    totals, used = await calculate_nutrients_for_ingredients(docs, products_col)

    if used == 0:
        return None

    return {
        "mealID": docs[0]["mealID"],
        "name": docs[0]["name"],
        "country": docs[0]["country"],
        "image": docs[0]["imageURL"],
        "nutrients": {k: round(v, 2) for k, v in totals.items()},
        "nutriscore": calculate_meal_nutriscore(totals),
        "ingredients_used": used
    }


# ============================
# HELPERS
# ============================
def clean_ingredients(ingredients: list[str]) -> list[str]:
    return [ing.strip().lower() for ing in ingredients if ing and ing.strip()]


def get_matched_ingredients(
    meal_ingredients: list,
    search_ingredients: list[str]
) -> list[str]:
    matched = set()

    for meal_ing in meal_ingredients:
        name = (meal_ing.get("ingredient") or "").lower()
        for s in search_ingredients:
            if s in name:
                matched.add(s)

    return list(matched)
