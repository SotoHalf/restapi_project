from pathlib import Path
import pandas as pd
from etl.utils.config_loader import Config

def iter_csvs(base_path=None):
    base_path = Path(base_path or Config.get_export_path())
    apis_available = set(Config.get_apis().keys())

    for api_folder in base_path.iterdir():
        if not api_folder.is_dir() or api_folder.name not in apis_available:
            continue

        api_name = api_folder.name

        for mode in ("raw", "clean"):
            mode_folder = api_folder / mode
            if not mode_folder.exists():
                continue

            for csv_file in mode_folder.glob("*.csv"):
                if "uploaded" in csv_file.name:
                    continue

                df = pd.read_csv(csv_file)
                yield df, api_name, mode, csv_file

