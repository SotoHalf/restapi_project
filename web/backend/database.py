import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None
        
    async def connect(self):
        """Conectar a MongoDB Atlas"""
        try:
            mongodb_uri = os.getenv("MONGODB_URI")
            db_name = os.getenv("DB_NAME")
            
            logger.info(f"Connecting to MongoDB: {mongodb_uri}")
            self.client = AsyncIOMotorClient(mongodb_uri)
            self.db = self.client[db_name]
            
            # Test connection
            await self.db.command("ping")
            logger.info("MongoDB connection successful")
            return True
            
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Desconectar de MongoDB"""
        if self.client:
            self.client.close()
            logger.info("MongoDB disconnected")
    
    async def check_connection(self):
        """Verificar conexión"""
        try:
            if self.db:
                await self.db.command("ping")
                return True
        except:
            pass
        return False

# Instancia global
db_manager = DatabaseManager()