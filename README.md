# Render 

https://restapi-udl-nutriscore.onrender.com/

# Github

https://github.com/SotoHalf/restapi_project

# Food & Meal ETL API with MongoDB and JWT Authentication

This project is an API for extracting, transforming, and loading (ETL) food data from different sources (`OpenFoodFacts` and `TheMealDB`) into MongoDB, along with JWT-based authentication to access different dashboards and protected routes.

---

## Project Structure

```
.
├── api_extractions/          # ETL output: raw and cleaned CSV files
├── crontab_sh/               # Scripts to run ETLs and load data into MongoDB
├── database.py               # General database connection
├── etl/                      # ETL logic (Extract, Transform, Load)
├── html/                     # HTML templates (login, home, admin)
├── logs/                     # ETL execution logs
├── main.py                   # Main entry point of the API
├── models.py                 # Data models (minimally used)
├── mongo/                    # Logic for loading documents into MongoDB
├── routers/                  # API routes
├── schemas.py                # Pydantic schemas (minimally used)
├── utils/                    # Auxiliary functions and utilities
├── requirements.txt          # Project dependencies
```

### Main Components

* **ETL (`etl/`)**: Handles extraction, transformation, and cleaning of data before loading into MongoDB.

  * `extract/`: Extractors for each source (`OpenFoodFacts` and `TheMealDB`)
  * `pipelines/`: Source-specific ETL pipelines and a runner for all pipelines
  * `utils/`: Helper functions

* **Mongo (`mongo/`)**: Contains all logic for loading documents into MongoDB (sync and async).

* **Routes (`routers/`)**: Implements API endpoints, including authentication, filters, statistics, and meal-building functionality.

* **Utils (`utils/`)**: Helper functions for JWT authentication, process management, logging, and log verification.

* **HTML (`html/`)**:

  * `index.html`: Login page
  * `home.html`: User dashboard
  * `admin.html`: Admin dashboard

* **JWT Authentication**:

  * Protected routes (`role=user` for home, `role=admin` for admin)
  * Login via `index.html` generates JWT tokens

---

## Initial Setup

### 1. Prerequisites

* Python 3.8+
* MongoDB Atlas or local MongoDB instance
* `virtualenv` for dependency management

### 2. Installation

```bash
git clone <repository>
cd <project_name>
python -m venv venv
source venv/bin/activate 
pip install -r requirements.txt
```

### 3. Configure `.env`

Create a `.env` file with:

```env
MONGODB_URI=="mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority"
DB_NAME="your_database_name"
SECRET_KEY="your_super_secret_key"
```

---

## Running the Project

### 1. Export CSVs from APIs

Run the ETL scripts:

```bash
sh crontab_sh/run_etl_api1.sh
sh crontab_sh/run_etl_api2.sh
```

This will generate raw and cleaned CSV files under `api_extractions/`.

### 2. Load CSVs into MongoDB

```bash
sh crontab_sh/run_etl_mongo.sh
```

This script loads the CSV files generated in the previous step into MongoDB.

### 3. Start the API

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### 4. API Documentation

* Swagger UI: `http://127.0.0.1:8000/docs`
* ReDoc: `http://127.0.0.1:8000/redoc`

---

## Usage

1. **Login:**

   * Access `index.html` and authenticate.
   * Normal users (`role=user`) -> `home.html`
   * Admins (`role=admin`) -> `admin.html`

2. **Protected Routes:**

   * All API routes require JWT tokens.

3. **ETL Review:**

   * Generated CSVs are in `api_extractions/`
   * Logs are in `logs/`

