from etl.extract.base_extractor import BaseExtractor
import pandas as pd

class OpenFoodFactsExtractor(BaseExtractor):

    def __init__(self):
        super().__init__("openfoodfacts")

    def extract_raw(self):
        url = "https://fake-api.com/data"
        data = self.get(url)
        return pd.DataFrame(data["result"])

    def transform(self, df):
        df_clean = df.rename(columns={
            "nombre": "name",
            "valor": "value"
        })
        df_clean["load_date"] = self.today
        return df_clean
