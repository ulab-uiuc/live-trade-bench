import logging
from datetime import datetime
import os
import threading

from .config import ALLOWED_ORIGINS, UPDATE_FREQUENCY
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from live_trade_bench.mock.mock_system import (
    MockAgentFetcherPolymarketSystem,
    MockAgentFetcherStockSystem,
    MockAgentPolymarketSystem,
    MockAgentStockSystem,
    MockFetcherPolymarketSystem,
    MockFetcherStockSystem,
)
from live_trade_bench.systems import PolymarketPortfolioSystem, StockPortfolioSystem

from .config import (
    POLYMARKET_MOCK_MODE,
    STOCK_MOCK_MODE,
    MockMode,
    get_base_model_configs,
)
from .models_data import generate_models_data
from .news_data import update_news_data
from .routers import models, news, social, system
from .social_data import update_social_data
from .system_data import update_system_status

# Global system instances - Initialize immediately
stock_system = None
polymarket_system = None

# System class mappings
STOCK_SYSTEMS = {
    MockMode.NONE: StockPortfolioSystem,
    MockMode.MOCK_AGENTS: MockAgentStockSystem,
    MockMode.MOCK_FETCHERS: MockFetcherStockSystem,
    MockMode.MOCK_AGENTS_AND_FETCHERS: MockAgentFetcherStockSystem,
}

POLYMARKET_SYSTEMS = {
    MockMode.NONE: PolymarketPortfolioSystem,
    MockMode.MOCK_AGENTS: MockAgentPolymarketSystem,
    MockMode.MOCK_FETCHERS: MockFetcherPolymarketSystem,
    MockMode.MOCK_AGENTS_AND_FETCHERS: MockAgentFetcherPolymarketSystem,
}

# Initialize systems immediately when module loads
stock_system = STOCK_SYSTEMS[STOCK_MOCK_MODE].get_instance()
polymarket_system = POLYMARKET_SYSTEMS[POLYMARKET_MOCK_MODE].get_instance()

# Add agents for real systems
if STOCK_MOCK_MODE == MockMode.NONE:
    for display_name, model_id in get_base_model_configs():
        stock_system.add_agent(display_name, 1000.0, model_id)

if POLYMARKET_MOCK_MODE == MockMode.NONE:
    for display_name, model_id in get_base_model_configs():
        polymarket_system.add_agent(display_name, 500.0, model_id)

stock_system.initialize_for_live()
polymarket_system.initialize_for_live()


def get_stock_system():
    """Get the current stock system instance (real or mock)."""
    global stock_system
    return stock_system


def get_polymarket_system():
    """Get the current polymarket system instance (real or mock)."""
    global polymarket_system
    return polymarket_system


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

app.include_router(models.router, prefix="/api")
app.include_router(news.router, prefix="/api")
app.include_router(social.router, prefix="/api")
app.include_router(system.router, prefix="/api")


@app.get("/api")
async def api_root():
    """API information endpoint."""
    return {
        "message": "Live Trade Bench API",
        "version": "1.0.0",
        "endpoints": {
            "models": "/api/models",
            "news": "/api/news",
            "social": "/api/social",
            "system": "/api/system",
            "docs": "/docs",
            "redoc": "/redoc",
        },
    }


def schedule_background_tasks(scheduler: BackgroundScheduler):
    scheduler.add_job(
        lambda: generate_models_data(stock_system, polymarket_system),
        "interval",
        seconds=UPDATE_FREQUENCY["trading_cycle"],
        id="generate_models_data",
        replace_existing=True,
    )
    scheduler.add_job(
        update_news_data,
        "interval",
        seconds=UPDATE_FREQUENCY["news_social"],
        id="update_news_data",
        replace_existing=True,
        next_run_time=datetime.now(),  # run immediately once
    )
    scheduler.add_job(
        update_social_data,
        "interval",
        seconds=UPDATE_FREQUENCY["news_social"],
        id="update_social_data",
        replace_existing=True,
        next_run_time=datetime.now(),  # run immediately once
    )
    scheduler.add_job(
        update_system_status,
        "interval",
        seconds=UPDATE_FREQUENCY["system_status"],
        id="update_system_status",
        replace_existing=True,
        next_run_time=datetime.now(),  # run immediately once
    )


@app.on_event("startup")
def startup_event():
    logger.info("🚀 FastAPI app starting up...")

    # Run initial data generation in background thread
    threading.Thread(
        target=lambda: generate_models_data(stock_system, polymarket_system),
        daemon=True,
    ).start()

    # Run initial news and social data updates immediately
    update_news_data()
    update_social_data()

    # Start background scheduler
    global scheduler
    executors = {"default": ThreadPoolExecutor(max_workers=1)}
    scheduler = BackgroundScheduler(executors=executors)
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
