import logging
from pymongo.errors import BulkWriteError


logger = logging.getLogger(__name__)

class MongoLoaderAsync:

    def __init__(self, client, db_name):
        self.db = client[db_name]

    async def insert(self, records, collection):
        if not records:
            return
        try:
            result = await self.db[collection].insert_many(records, ordered=False)
            logger.info(f"[async] Inserted {len(result.inserted_ids)} docs into {collection}")
        except BulkWriteError as e:
            # Filtra los errores de duplicado (código 11000)
            dup_errors = [err for err in e.details['writeErrors'] if err['code'] == 11000]
            inserted_count = len(records) - len(dup_errors)
            logger.info(f"[async] Inserted {inserted_count} docs into {collection} (duplicates ignored)")

