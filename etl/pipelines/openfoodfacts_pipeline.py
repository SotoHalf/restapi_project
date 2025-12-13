from etl.utils.config_loader import Config
from etl.utils.log_etl import log_write

def run():
    mExtractor = Config.get_extractor_class("openfoodfacts")
    extractor = mExtractor()
    raw_file, clean_file = extractor.run()
    log_write("openfoodfacts", f"{raw_file} created")
    log_write("openfoodfacts", f"{clean_file} created")

if __name__ == "__main__":
    run()