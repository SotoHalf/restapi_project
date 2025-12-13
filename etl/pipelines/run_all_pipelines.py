from etl.pipelines.themealdb_pipeline import run as api1_run
from etl.pipelines.openfoodfacts_pipeline import run as api2_run

def run_all():
    pipelines = [api1_run, api2_run]

    for pipe in pipelines:
        pipe()

if __name__ == "__main__":
    run_all()
