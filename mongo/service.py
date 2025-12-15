from mongo.csv_iterator import iter_csvs
from pathlib import Path

def df_to_records(df):
    records = df.to_dict(orient="records")
    return records if records else None

def mark_uploaded(csv_file: Path):
    new_name = csv_file.with_name(
        csv_file.stem + "_uploaded" + csv_file.suffix
    )
    csv_file.rename(new_name)

# --- SYNC ---
def load_all_sync(loader, base_path=None):
    for df, api_name, mode, csv_file in iter_csvs(base_path):
        records = df_to_records(df)
        loader.insert(records, f"{api_name}_{mode}")
        mark_uploaded(csv_file)
    
    return loader.get_last_insert()

# --- ASYNC ---
async def load_all_async(loader, base_path=None):
    for df, api_name, mode, csv_file in iter_csvs(base_path):
        records = df_to_records(df)
        await loader.insert(records, f"{api_name}_{mode}")
        mark_uploaded(csv_file)

    return loader.get_last_insert()

