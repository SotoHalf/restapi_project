import os
from dotenv import load_dotenv
from mongo.mongo_sync import MongoLoaderSync
from mongo.service import load_all_sync
from etl.utils.config_loader import Config

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI") or Config.get_mongo_uri()
DB_NAME = os.getenv("DB_NAME") or Config.get_mongo_database()
LOADER = MongoLoaderSync(MONGO_URI, DB_NAME)

def main():    
    load_all_sync(LOADER)

def get_mongo_manager():
    return LOADER

if __name__ == "__main__":
    main()

