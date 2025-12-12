import asyncio
import database
from motor.motor_asyncio import AsyncIOMotorClient
import certifi
import os
from dotenv import load_dotenv

load_dotenv()

async def check_logs():
    print("Connecting to MongoDB...")
    client = AsyncIOMotorClient(
        os.getenv("MONGODB_URI"),
        tls=True,
        tlsCAFile=certifi.where()
    )
    db = client[os.getenv("DB_NAME")]
    
    print("Checking logs collection...")
    count = await db["logs"].count_documents({})
    print(f"Total logs found: {count}")
    
    if count > 0:
        print("Latest 5 logs:")
        async for log in db["logs"].find().sort("timestamp", -1).limit(5):
            print(f"- {log['timestamp']} [{log['level']}] {log['message']}")
    else:
        print("No logs found.")

if __name__ == "__main__":
    asyncio.run(check_logs())
