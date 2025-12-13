#!/bin/bash

# Go to main project directory
cd "$(dirname "$0")/.."

source ./venv/bin/activate

python3 -m etl.pipelines.themealdb_pipeline >> logs/etl_api1.log 2>&1

#00 7 1 * * /crontab_sh/run_etl_mongo.sh
# EVERY 1 of the month