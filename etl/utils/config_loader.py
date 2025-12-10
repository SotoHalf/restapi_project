import importlib
import yaml
from pathlib import Path

class Config:
    _config_data = None

    @classmethod
    def load(cls):
        """ Load YAML file once """
        if cls._config_data is None:
            root = Path(__file__).resolve().parents[2]  # project root
            config_path = root / "etl" / "config.yaml"
            with open(config_path, "r") as f:
                cls._config_data = yaml.safe_load(f)
        return cls._config_data

    @classmethod
    def get_export_path(cls):
        return Path(cls.load()["etl"]["export_path"])

    @classmethod
    def get_date_format(cls):
        return cls.load()["etl"].get("date_format", "%Y-%m-%d")

    @classmethod
    def get_mongo_uri(cls):
        return cls.load()["mongo"]["uri"]

    @classmethod
    def get_mongo_database(cls):
        return cls.load()["mongo"]["database"]

    @classmethod
    def get_apis(cls, only_enabled=True):
        """
        return apis dictionary, only if it's enabled
        """
        apis = cls.load()["apis"]
        if only_enabled:
            apis = {k: v for k, v in apis.items() if v.get("enabled", False)}
        return apis

    @classmethod
    def get_api_config(cls, api_name):
        return cls.load()["apis"].get(api_name)
    
    @classmethod
    def get_extractor_class(cls, api_name):
        api_conf = cls.get_api_config(api_name)
        path = api_conf["extractor"]
        module_name, class_name = path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        ExtractorClass = getattr(module, class_name)
        return ExtractorClass
