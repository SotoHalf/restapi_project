import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import certifi
import logging

# Load environment variables from a .env file
load_dotenv()

# --- CONFIGURATION ---
# In production, this MUST be an environment variable.
# Example: "mongodb+srv://<user>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority"
# For local testing without Atlas, use: "mongodb://localhost:27017"
MONGO_URL = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_manager = Database()

async def get_db():
    """
    Dependency that returns the database object.
    Note: Motor handles connection pooling efficiently, so we don't need 
    to open/close connections per request like we do with SQL sessions.
    """
    if db_manager.db is None:
        logger = logging.getLogger(__name__)
        logger.info("Initializing MongoDB connection...")
        # Lazy initialization if needed, though main.py usually handles startup
        db_manager.client = AsyncIOMotorClient(
            MONGO_URL,
            tls=True,
            tlsCAFile=certifi.where()
        )
        db_manager.db = db_manager.client[DB_NAME]
    return db_manager.db
