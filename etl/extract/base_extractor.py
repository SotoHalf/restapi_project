from abc import ABC, abstractmethod
from curl_cffi import requests
from datetime import datetime
from pathlib import Path
import pandas as pd
import time

from etl.utils.config_loader import Config
from etl.utils.log_etl import log_write
import mongo.cli as mongo_cli

# ABSTRACT CLASS
class BaseExtractor(ABC):

    def __init__(self, api_name: str):
        self.api_name = api_name
        self.today = f"{datetime.now().strftime(Config.get_date_format())}_{int(time.time())}"
        self.base_path = Path(f"{Config.get_export_path()}/{api_name}")
        # path concatenation
        self._raw_path = self.base_path / "raw"
        self._clean_path = self.base_path / "clean"
        # create in case it doesn't exists
        self._raw_path.mkdir(parents=True, exist_ok=True)
        self._clean_path.mkdir(parents=True, exist_ok=True)

    def exists_in_db(self, collection, key, value):
        mongo_sync = mongo_cli.get_mongo_manager()
        return mongo_sync.exists_in_db(collection, key, value)
    
    @property
    def raw_path(self):
        return self._raw_path

    @property
    def clean_path(self):
        return self._clean_path

    def get(self, url, headers=None, retries=3,  timeout=30000, retry_delay=10, **kwargs):
        #curl_cffi enables simulate a true navegator
        for attempt in range(1, retries + 1):
            try:
                resp = requests.get(
                    url,
                    headers=headers or {},
                    impersonate="chrome101",
                    timeout=timeout,
                    **kwargs
                )
                resp.raise_for_status()
                return resp.json()
            
            except KeyboardInterrupt:
                self.log("Process interrupted by user (Ctrl+C)")
                raise

            except requests.exceptions.RequestException as e:
                self.log(f"Attempt {attempt}/{retries} failed: {e}")
                if attempt == retries:
                    break
                time.sleep(retry_delay)

            except requests.exceptions.Timeout as e:
                self.log(
                    f"Timeout on attempt {attempt}/{retries} "
                    f"after {timeout}s: {e}"
                )
                if attempt == retries:
                    break
                time.sleep(retry_delay)
            
            except Exception as e:
                self.log(f"Unexpected error: {e}")
                if attempt == retries:
                    break
                time.sleep(retry_delay)

        return None

    def log(self, message):
        log_write(self.api_name,message)

    @abstractmethod
    def extract_raw(self) -> pd.DataFrame:
        # expects to return a parsed DataFrame (pandas)
        pass

    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        # expects to return a parsed DataFrame (pandas) 
        # but with the data clean
        pass

    def save_df(self, df, path: Path):
        df.to_csv(path, index=False)

    def run(self):
        # Extract
        df_raw = self.extract_raw()
        raw_file = self._raw_path / f"{self.today}.csv"
        if df_raw is not None:
            if not df_raw.empty:
                self.save_df(df_raw, raw_file)

        # Transform
        df_clean = self.transform(df_raw)
        clean_file = self._clean_path / f"{self.today}.csv"
        if df_clean is not None:
            if not df_clean.empty:
                self.save_df(df_clean, clean_file)

        return raw_file, clean_file
