import pandas as pd
from pymongo import MongoClient
from etl.utils.config_loader import Config

class MongoLoader:

    def __init__(self, uri=Config.get_mongo_uri(), db_name=Config.get_mongo_database()):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    def load(self, df: pd.DataFrame, api: str, mode="raw"):
        collection_name = f"{api}_{mode}"
        collection = self.db[collection_name]
        records = df.to_dict(orient="records")
        collection.insert_many(records)