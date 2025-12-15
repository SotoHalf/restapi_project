from etl.extract.base_extractor import BaseExtractor
import pandas as pd
import time
import mongo.cli as mongo_cli

class OpenFoodFactsExtractor(BaseExtractor):

    SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
    PAGE_SIZE = 10

    def __init__(self):
        super().__init__("openfoodfacts")

    #get unique ingredients from themealdb
    def get_unique_ingredients(self):
        mongo_sync = mongo_cli.get_mongo_manager()
        collection = mongo_sync.db["themealdb_clean"]

        ingredients = collection.distinct("ingredient")
        ingredients = [
            i.strip().lower()
            for i in ingredients
            if isinstance(i, str) and i.strip()
        ]

        return sorted(set(ingredients))

    # Get products from OpenFoodFacts
    def search_products(self, ingredient):
        params = {
            "search_terms": ingredient,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            #"countries_tags": "spain",
            "page_size": OpenFoodFactsExtractor.PAGE_SIZE
        }

        data = self.get(OpenFoodFactsExtractor.SEARCH_URL, params=params)
        if data is None:
            self.log(f"Unable to retrieve the ingredient: {ingredient}")
            return []
        return data.get("products", [])

    
    def extract_raw(self):
        ingredients = self.get_unique_ingredients()
        self.log(f"Total obtained ingredients from db {len(ingredients)}")

        ingredients = [
            ingredient
            for ingredient in ingredients
            if not self.exists_in_db("openfoodfacts_clean", "search_term", ingredient)
        ]
        self.log(f"Need to get {len(ingredients)}")

        rows = []

        self.log(f"Found {len(ingredients)} unique ingredients")

        for i, ingredient in enumerate(ingredients, start=1):

            self.log(f"Searching OFF for '{ingredient}' ({i}/{len(ingredients)})")

            products = self.search_products(ingredient)
            #time.sleep(0.5) #wait to avoid block

            for p in products:
                code = p.get("code")
                if not code:
                    continue

                #avoid dups
                if self.exists_in_db("openfoodfacts_raw", "_id", code):
                    continue

                nutriments = p.get("nutriments", {})

                rows.append({
                    "_id": code,
                    "search_term": ingredient,
                    "product_name": p.get("product_name"),
                    "brands": p.get("brands"),
                    "countries": p.get("countries"),
                    "energy_kcal_100g": nutriments.get("energy-kcal_100g"),
                    "fat_100g": nutriments.get("fat_100g"),
                    "carbohydrates_100g": nutriments.get("carbohydrates_100g"),
                    "proteins_100g": nutriments.get("proteins_100g"),
                    "salt_100g": nutriments.get("salt_100g"),
                    "image_url": p.get("image_url")
                })

        df = pd.DataFrame(rows)
        return df

    def transform(self, df: pd.DataFrame):
        if df is None or df.empty:
            return df

        # Normalización básica
        numeric_cols = [
            "energy_kcal_100g",
            "fat_100g",
            "carbohydrates_100g",
            "proteins_100g",
            "salt_100g"
        ]

        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df["product_name"] = df["product_name"].fillna("").str.strip()
        df["brands"] = df["brands"].fillna("").str.strip()
        df["search_term"] = df["search_term"].str.lower()

        # remove products without enegy info
        df = df.dropna(subset=["energy_kcal_100g"], how="all")

        return df


if __name__ == "__main__":
    extractor = OpenFoodFactsExtractor()

    # TEST PROCESS
    #extractor.extract_raw()
    extractor.run()

    # TEST TRANSFORM
    """
    from datetime import datetime
    _date = datetime(2025,12,13)
    df = pd.read_csv(extractor.raw_path / f"{_date.strftime("%Y-%m-%d")}.csv")
    df_clean = extractor.transform(df)
    extractor.save_df(df_clean, extractor.clean_path / f"{_date.strftime("%Y-%m-%d")}.csv")
    """
    
    #https://wiki.openfoodfacts.org/API/Read/Search