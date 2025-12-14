from pymongo import MongoClient
import logging
from pymongo.errors import BulkWriteError

logger = logging.getLogger(__name__)

class MongoLoaderSync:

    def __init__(self, uri, db_name):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    def insert(self, records, collection):
        if not records:
            return
        try:
            self.db[collection].insert_many(records, ordered=False)
            logger.info(f"[sync] Inserted {len(records)} docs into {collection}")
        except BulkWriteError as e:
            # Filtra los errores de duplicado
            dup_errors = [err for err in e.details['writeErrors'] if err['code'] == 11000]
            inserted_count = len(records) - len(dup_errors)
            logger.info(f"[sync] Inserted {inserted_count} docs into {collection} (duplicates ignored)")

    def exists_in_db(self, collection, _id):
        try:
            doc = self.db[collection].find_one({"_id": _id})
        except Exception:
            return False
        return doc is not None

    def get_client(self):
        return self.client
    
    def close(self):
        self.client.close()
        logger.info("MongoDB client connection closed")
