from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware

from fastapi.templating import Jinja2Templates
from fastapi import Request
from routers import auth_routes, protected_routes

from datetime import timedelta, datetime
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
import models, schemas, utils.auth as auth, database
from utils.logging_config import setup_logging
import logging
from pathlib import Path
import certifi
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from routers import auth_routes, protected_routes, health_map, versus, filters, meal_builder, mystats

def print_time():
    """job to print time every minute."""
    logger = logging.getLogger(__name__)
    logger.info(f"Current time: {datetime.now()}")


# LIFECYCLE EVENTS

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup Logic
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting up: Connecting to MongoDB...")
    database.db_manager.client = AsyncIOMotorClient(
        database.MONGO_URL,
        tls=True,
        tlsCAFile=certifi.where()
    )
    database.db_manager.db = database.db_manager.client[database.DB_NAME]
    
    # Create unique index for username to ensure no duplicates
    await database.db_manager.db["users"].create_index("username", unique=True)
    logger.info("MongoDB connected and index created.")

    # Start Scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(print_time, 'interval', seconds=60)
    scheduler.start()
    
    # The application runs while this yield is active
    yield
    
    # Shutdown Logic
    scheduler.shutdown()
    if database.db_manager.client:
        database.db_manager.client.close()
    logger.info("Shutting down: MongoDB connection closed.")

app = FastAPI(
    title="Sample FastAPI auth project",
    description="Distributed System Node Registry with OAuth2 + MongoDB Atlas",
    version="2.0.1",
    lifespan=lifespan
)

templates = Jinja2Templates(directory="html")

# CORS Configuration
# This is necessary when the frontend runs on a different port or origin.
# We set allow_origins=["*"] for development simplicity, allowing any origin
# to connect to the API. In production, you would replace "*" with your 
# specific frontend domain (e.g., "https://yourfrontend.com").
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# ROUTES IMPORT
app.include_router(auth_routes.router)
app.include_router(protected_routes.router)
app.include_router(health_map.router)
app.include_router(versus.router)
app.include_router(filters.router)
app.include_router(meal_builder.router)
app.include_router(mystats.router)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Serves index.html from the html/ folder.
    """
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        print(f"ERROR: {e}")
        return HTMLResponse(
            "<h1>Error: index.html not found or could not be rendered.</h1>", 
            status_code=404
        )

@app.get("/home", response_class=HTMLResponse)
async def get_home(request: Request):
    """
    Serves home.html after login
    """
    try:
        return templates.TemplateResponse("home.html", {"request": request})
    except Exception as e:
        return HTMLResponse(f"<h1>Error loading home.html: {e}</h1>", status_code=404)

@app.get("/admin", response_class=HTMLResponse)
async def get_admin(request: Request):
    """
    Serves admin.html for admins
    """
    try:
        return templates.TemplateResponse("admin.html", {"request": request})
    except Exception as e:
        return HTMLResponse(f"<h1>Error loading admin.html: {e}</h1>", status_code=404)
