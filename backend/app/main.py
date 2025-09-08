import json
import logging
import os
import threading
import time
import traceback
from datetime import datetime, timedelta

from app.config import (
    ALLOWED_ORIGINS,
    TRADING_CONFIG,
    UPDATE_FREQUENCY,
    get_base_model_configs,
)
from app.news_data import update_news_data
from app.routers import models, news, social, system
from app.social_data import update_social_data
from app.system_data import update_system_status
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Live Trade Bench API",
    description="API for the Live Trade Bench platform",
    version="1.0.0",
)

allowed_origins = list(ALLOWED_ORIGINS)

frontend_url = os.environ.get("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(models.router)
app.include_router(news.router)
app.include_router(social.router)
app.include_router(system.router)

def run_initial_tasks():
    print("🚀 Kicking off initial background tasks...")
    from .models_data import generate_models_data, run_backend_backtest

    generate_models_data()
    run_backend_backtest()
    print("✅ Initial background tasks finished.")


def schedule_background_tasks(scheduler: BackgroundScheduler):
    from .models_data import generate_models_data

    scheduler.add_job(
        generate_models_data,
        "interval",
        minutes=UPDATE_FREQUENCY["trading_cycle"],
        id="generate_models_data",
        replace_existing=True,
    )

    scheduler.add_job(
        update_news_data,
        "interval",
        minutes=UPDATE_FREQUENCY["news_social"],
        id="update_news_data",
        replace_existing=True,
    )
    scheduler.add_job(
        update_social_data,
        "interval",
        minutes=UPDATE_FREQUENCY["news_social"],
        id="update_social_data",
        replace_existing=True,
    )
    scheduler.add_job(
        update_system_status,
        "interval",
        seconds=UPDATE_FREQUENCY["system_status"],
        id="update_system_status",
        replace_existing=True,
    )
    print("✅ All background jobs scheduled.")

@app.on_event("startup")
def startup_event():
    logger.info("🚀 FastAPI app starting up...")

    threading.Thread(target=run_initial_tasks, daemon=True).start()

    scheduler = BackgroundScheduler()
    schedule_background_tasks(scheduler)
    scheduler.start()

    logger.info("✅ Background scheduler started.")

@app.get("/health")
def health_check():
    return {"status": "ok"}

static_files_path = os.path.join(
    os.path.dirname(__file__), "..", "..", "frontend", "build", "static"
)
if os.path.exists(static_files_path):
    app.mount(
        "/static",
        StaticFiles(directory=static_files_path),
        name="static",
    )

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    index_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend", "build", "index.html"
    )

    if not os.path.exists(index_path):
        raise HTTPException(
            status_code=404,
            detail="Frontend not found. Make sure to build the frontend first.",
        )

    return FileResponse(index_path)
