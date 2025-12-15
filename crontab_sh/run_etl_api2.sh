#!/bin/bash

# Go to main project directory
cd "$(dirname "$0")/.."

source ./venv/bin/activate

python3 -m etl.pipelines.openfoodfacts_pipeline


#00 6 * * 1 /crontab_sh/run_etl_mongo.sh
# EVERY MONDAY AT & AM