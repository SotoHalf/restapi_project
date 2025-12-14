#!/bin/bash

# Go to main project directory
cd "$(dirname "$0")/.."

source ./venv/bin/activate

python3 -m mongo.cli >> logs/mongo_cli.log 2>&1


#00 8 * * * /crontab_sh/run_etl_mongo.sh
# EVERY DAY