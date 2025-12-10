from etl.utils.config_loader import Config

def run():
    mExtractor = Config.get_extractor_class("themealdb")
    extractor = mExtractor()
    raw_file, clean_file = extractor.run()
    return raw_file, clean_file

if __name__ == "__main__":
    run()