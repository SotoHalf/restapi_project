from etl.extract.base_extractor import BaseExtractor
import time
import pandas as pd

class TheMealDBExtractor(BaseExtractor):

    MAX_INGREDIENTS = 40
    CONVERSION_TO_GRAMS = {
        "g": 1,
        "gram": 1,
        "grams": 1,
        "kg": 1000,
        "lb": 453.592,
        "lbs": 453.592,
        "pound": 453.592,
        "pounds": 453.592,
        "oz": 28.3495,
        "ounce": 28.3495,
        "ounces": 28.3495,
        "ml": 1,
        "milliliters": 1,
        "l": 1000,
        "litre": 1000,
        "litres": 1000,
        "tsp": 5,
        "teaspoon": 5,
        "teaspoons": 5,
        "tbs": 15,
        "tablespoon": 15,
        "tablespoons": 15,
        "tblsp": 15,
        "tbls": 15,
        "cup": 240,
        "cups": 240,
        "handful": 40,
        '_missing_': 100
    }

    def __init__(self):
        super().__init__("themealdb")

    def get_data_by_country(self):
        
        url_list_countries = "https://www.themealdb.com/api/json/v1/1/list.php"
        params = {
            'a': 'list'
        }
        countries_raw = self.get(url_list_countries, params=params)
        countries = [
            country.get('strArea')
            for country in countries_raw.get('meals',[])
        ]

        list_recipies_by_country = {}

        for i, cc in enumerate(countries, start=1):
            self.log(f"Retrieving recipes for country: {cc} - {i}/{len(countries)} - {round(float(i)/len(countries)*100)}%")
            url_recipies = "www.themealdb.com/api/json/v1/1/filter.php"
            params = {
                'a': cc
            }
            recepies_raw = self.get(url_recipies, params=params)
            for meals in recepies_raw.get('meals',[]):
                list_recipies_by_country.setdefault(cc,[]).append(meals)
            
        return list_recipies_by_country
            
    
    def get_data_by_id(self, id_meal):
        params = {
            'i': id_meal,
        }
        url_data = "https://www.themealdb.com/api/json/v1/1/lookup.php"

        meal_data = self.get(url_data, params=params)
        meal = meal_data.get('meals',[{}])[0]

        if meal:
            result = {
                'instructions': meal.get('strInstructions', '').strip()
            }

            for i in range(1, TheMealDBExtractor.MAX_INGREDIENTS+1):
                ingredient = meal.get(f'strIngredient{i}')
                measure = meal.get(f'strMeasure{i}')
                if ingredient and ingredient.strip(): 
                    result[f'ingredient_{i}'] = ingredient.strip()
                    result[f'measure_{i}'] = (measure or '').strip()

            return result
        else:
            return {}

    def extract_raw(self):
        data_by_country = self.get_data_by_country()
        rows = []
        for i, (cc, meals) in enumerate(data_by_country.items(), start=1):
            self.log(
                f"Retrieving meals data for country: {cc} - {i}/{len(data_by_country)}"
            )
            for meal in meals:
                id_meal = meal.get('idMeal',None)
                if not id_meal: continue
                
                #Check if already exists
                if self.exists_in_db(f"{self.api_name}_raw",id_meal): 
                    continue

                meal_data = self.get_data_by_id(id_meal)

                if not meal_data: continue
                row = {
                    "_id" : id_meal,
                    "country" : cc,
                    "name" : meal["strMeal"],
                    "imageURL" : meal["strMealThumb"],
                }

                for k,v in meal_data.items():
                    row[k] = v
                
                rows.append(row)

        fieldnames = [
            "_id",
            "name",
            "country",
            "imageURL",
            "instructions"
        ] 

        for i in range(1,TheMealDBExtractor.MAX_INGREDIENTS+1):
            fieldnames.append(f"ingredient_{i}")
            fieldnames.append(f"measure_{i}")

        df = pd.DataFrame(rows, columns=fieldnames, index=None)
        return df
    
    def get_num_and_units(self, measure):
        def extract_num(tokens):
            for t in tokens:
                t = t.strip()

                try:
                    return float(t)
                except ValueError:
                    pass
                
                # support for fractions "1/2"
                if '/' in t:
                    try:
                        numerator, denominator = t.split('/')
                        return float(numerator) / float(denominator)
                    except (ValueError, ZeroDivisionError):
                        pass                
            
                num = 0
                for n in t:
                    try:
                        n = float(n)
                        num = num*10 + n
                    except ValueError:
                        break

                return float(num)
                
            return 0
                
        def remove_nums(tokens):
            news_tokens = []
            for token in tokens:
                n_s = ""
                for c in token:
                    try:
                        float(c)
                    except ValueError:
                        n_s += c
                news_tokens.append(n_s)
            return news_tokens
                
        tokens = measure.split()
        num = extract_num(tokens)
        tokens = remove_nums(tokens)

        clean_tokens = []
        for t in tokens:
            if t.lower() in TheMealDBExtractor.CONVERSION_TO_GRAMS.keys():
                clean_tokens.append(t)
        
        units = clean_tokens[0] if clean_tokens else None

        if not num and not units:
            return 100, 'g'
        if num and not units:
            return num, '_missing_'
        if not num and units:
            return 100, units

        return num, units
    
    def normalize_to_grams(self, measure):
        num, units = self.get_num_and_units(measure)
        value = num*TheMealDBExtractor.CONVERSION_TO_GRAMS[units.lower()]
        final_value = f'{round(value,2)}'
        return final_value
    
    def transform(self, df):
        # WE TRY TO NORMALIZE EVERYTHING to Grams - it's not perfect
        df = df.drop(columns=["instructions"])
            
        for i in range(1, TheMealDBExtractor.MAX_INGREDIENTS + 1):
            col = f"measure_{i}"
            if col in df.columns:
                df[col] = df[col].fillna('')
                df[col] = df[col].apply(self.normalize_to_grams)


        # create pairs, we want mealId+Ingridient
        rows = []
        for _, row in df.iterrows():
            meal_id = row["_id"]
            name = row["name"]
            country = row["country"]
            image_url = row["imageURL"]

            for i in range(1, TheMealDBExtractor.MAX_INGREDIENTS + 1):
                ingredient = row.get(f"ingredient_{i}")
                measure = row.get(f"measure_{i}")

                if pd.isna(ingredient) or ingredient == "":
                    continue

                #generated_id = f"{meal_id}_{i}{meal_id + len(str(ingredient))}"
                generated_id = f"{meal_id}_{i}{str(int(meal_id) + len(str(ingredient)))}"

                rows.append({
                    "_id": generated_id,
                    "mealID": meal_id,
                    "name": name,
                    "country": country,
                    "imageURL": image_url,
                    "ingredient": ingredient,
                    "measure_g": measure
                })

        df = pd.DataFrame(rows)

        return df

if __name__ == "__main__":
    extractor = TheMealDBExtractor()

    # TEST PROCESS
    extractor.extract_raw()
    extractor.run()

    # TEST TRANSFORM
    """
    from datetime import datetime
    _date = datetime(2025,12,13)
    df = pd.read_csv(extractor.raw_path / f"{_date.strftime("%Y-%m-%d")}.csv")
    df_clean = extractor.transform(df)
    extractor.save_df(df_clean, extractor.clean_path / f"{_date.strftime("%Y-%m-%d")}.csv")
    """
    
    #www.themealdb.com/api/json/v1/1/lookup.php?i=52772
