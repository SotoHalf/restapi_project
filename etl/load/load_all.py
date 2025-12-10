
import os
from etl.load.loader import MongoLoader
from etl.utils.config_loader import Config
import pandas as pd
from pathlib import Path

def load_all():
    loader = MongoLoader()

    base_path = Path(Config.get_export_path())

    apis_available = list(Config.get_apis().keys())

    for api_folder in base_path.iterdir():
        print(api_folder)
        if not api_folder.is_dir():
            continue

        if os.path.basename(api_folder) not in apis_available:
            continue

        api_name = api_folder.name

        # RAW
        for raw_file in (api_folder/"raw").glob("*.csv"):
            df = pd.read_csv(raw_file)
            loader.load(df, api_name, "raw")

        # CLEAN
        for clean_file in (api_folder/"clean").glob("*.csv"):
            df = pd.read_csv(clean_file)
            loader.load(df, api_name, "clean")

if __name__ == "__main__":
    load_all()
