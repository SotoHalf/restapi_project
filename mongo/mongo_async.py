import math
from pymongo.errors import BulkWriteError

from etl.utils.log_etl import log_write 

class MongoLoaderAsync:

    def __init__(self, client, db_name):
        self.db = client[db_name]
        self.last_insert = ""

    @staticmethod
    def clean_nan(records):
        def clean_value(value):
            if isinstance(value, float):
                if math.isnan(value) or math.isinf(value):
                    return None
                return value
            elif isinstance(value, dict):
                return {k: clean_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [clean_value(v) for v in value]
            else:
                return value

        return [clean_value(record) for record in records]

    async def insert(self, records, collection):
        if not records:
            return
        
        records = MongoLoaderAsync.clean_nan(records)

        try:
            result = await self.db[collection].insert_many(records, ordered=False)
            self.last_insert = f"[async] Inserted {len(result.inserted_ids)} docs into {collection}"
            log_write("mongo", self.last_insert)
        except BulkWriteError as e:
            # Filter 11000 dup error
            dup_errors = [err for err in e.details['writeErrors'] if err['code'] == 11000]
            inserted_count = len(records) - len(dup_errors)
            self.last_insert = f"[async] Inserted {inserted_count} docs into {collection} (duplicates ignored)"
            log_write("mongo", self.last_insert)

    def get_last_insert(self):
        return self.last_insert

