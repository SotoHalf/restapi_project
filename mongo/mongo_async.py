import logging

logger = logging.getLogger(__name__)

class MongoLoaderAsync:

    def __init__(self, client, db_name):
        self.db = client[db_name]

    async def insert(self, records, collection):
        if not records:
            return
        result = await self.db[collection].insert_many(records, ordered=False)
        logger.info(f"[async] Inserted {len(result.inserted_ids)} docs into {collection}")

