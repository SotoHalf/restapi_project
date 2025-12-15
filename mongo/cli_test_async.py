import os
import asyncio
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient  # Cliente async para Mongo
from mongo.mongo_async import MongoLoaderAsync
from mongo.service import load_all_async
from etl.utils.config_loader import Config

load_dotenv()


MONGO_URI = os.getenv("MONGODB_URI") or Config.get_mongo_uri()
DB_NAME = os.getenv("DB_NAME") or Config.get_mongo_database()

client = AsyncIOMotorClient(MONGO_URI)

LOADER = MongoLoaderAsync(client, DB_NAME)

async def main():    
    await load_all_async(LOADER)

def get_mongo_manager():
    return LOADER

if __name__ == "__main__":
    asyncio.run(main())
