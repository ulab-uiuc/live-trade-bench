import logging
import os
import threading
import time
import traceback
import json
from datetime import datetime, timedelta

# 使用统一配置管理
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Live Trade Bench API",
    description="API for the Live Trade Bench platform",
    version="1.0.0",
)

# CORS configuration using centralized config
allowed_origins = list(ALLOWED_ORIGINS)  # 从配置文件获取

# Add production frontend URL from environment variable
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

# Include routers
app.include_router(models.router)
app.include_router(news.router)
app.include_router(social.router)
app.include_router(system.router)

# ============================================================================
# SIMPLE STARTUP BACKTEST - Use existing live_trade_bench interface
# ============================================================================


def run_startup_backtest():
    """Run backtest for past week on startup using existing system."""
    try:
        print("🔄 Running startup backtest...")

        # Use SINGLE source of truth for model configurations
        # Calculate past week dates - use historical data, not future data
        end_date = datetime.now() - timedelta(days=1)  # Yesterday
        start_date = end_date - timedelta(days=TRADING_CONFIG["backtest_days"])

        # 使用统一配置源
        base_models = get_base_model_configs()

        # Run parallel backtests for both markets
        from app.models_data import run_parallel_backtest

        backtest_results = run_parallel_backtest(
            models=base_models,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            stock_initial_cash=TRADING_CONFIG["initial_cash_stock"],
            polymarket_initial_cash=TRADING_CONFIG["initial_cash_polymarket"],
        )

        # Save results directly to models_data.json instead of separate file
        # backtest_results 已经是正确的格式了

        # Import here to avoid circular dependency
        from app.models_data import _save_backtest_data_to_models

        _save_backtest_data_to_models(backtest_results)

        stock_count = len(backtest_results.get("stock", {}))
        poly_count = len(backtest_results.get("polymarket", {}))

        print(
            f"✅ Startup backtest completed: {stock_count} stock, {poly_count} polymarket results"
        )

    except Exception as e:
        print(f"❌ Startup backtest failed: {e}")
        traceback.print_exc()


# ============================================================================
# BACKGROUND UPDATES - Simple, clean, no async complexity
# ============================================================================


def run_background_updates():
    """Run all background updates in separate threads."""

    def system_status_updates():
        """Update system status periodically."""
        while True:
            try:
                update_system_status()
            except Exception as e:
                logger.error(f"Error in system_status_updates: {e}")
            time.sleep(UPDATE_FREQUENCY["system_status"])

    def news_social_updates():
        """Update news and social data periodically."""
        while True:
            try:
                update_news_data()
                update_social_data()
            except Exception as e:
                logger.error(f"Error in news_social_updates: {e}")
            time.sleep(UPDATE_FREQUENCY["news_social"])

    def trading_cycle_updates():
        """Trigger trading cycle periodically."""
        # Import here to avoid circular dependency
        from app.models_data import trigger_cycle

        while True:
            try:
                logger.info("Triggering trading cycle...")
                trigger_cycle()
                logger.info("Trading cycle finished.")
            except Exception as e:
                logger.error(f"Error in trading_cycle_updates: {e}")
            time.sleep(UPDATE_FREQUENCY["trading_cycle"])

    # Start all update loops in daemon threads
    threading.Thread(target=system_status_updates, daemon=True).start()
    threading.Thread(target=news_social_updates, daemon=True).start()
    threading.Thread(target=trading_cycle_updates, daemon=True).start()

    logger.info("🚀 All background update threads started.")


# ============================================================================
# STARTUP EVENT - Clean and simple
# ============================================================================


@app.on_event("startup")
def startup_event():
    """
    Run startup tasks:
    1. Initial data generation (if needed)
    2. Backtest for the past week
    3. Start background update threads
    """
    logger.info("🚀 FastAPI app starting up...")

    from app.news_data import update_news_data
    from app.social_data import update_social_data
    from app.system_data import update_system_status
    from app.models_data import get_models_data

    def _write_json(path: str, data):
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write placeholder {path}: {e}")

    if not os.path.exists("backend/models_data.json"):
        _write_json("backend/models_data.json", [])
    if not os.path.exists("backend/news_data.json"):
        _write_json("backend/news_data.json", {"stock": [], "polymarket": []})
    if not os.path.exists("backend/social_data.json"):
        _write_json("backend/social_data.json", {"stock": [], "polymarket": []})
    if not os.path.exists("backend/system_data.json"):
        _write_json(
            "backend/system_data.json",
            {
                "running": True,
                "total_agents": 0,
                "stock_agents": 0,
                "polymarket_agents": 0,
                "last_updated": datetime.now().isoformat(),
                "uptime": "Active",
                "version": "1.0.0",
            },
        )

    def _kickoff_initial_updates():
        try:
            try:
                get_models_data()
            except Exception as e:
                logger.error(f"Initial get_models_data failed: {e}")
            try:
                update_news_data()
            except Exception as e:
                logger.error(f"Initial update_news_data failed: {e}")
            try:
                update_social_data()
            except Exception as e:
                logger.error(f"Initial update_social_data failed: {e}")
            try:
                update_system_status()
            except Exception as e:
                logger.error(f"Initial update_system_status failed: {e}")
        except Exception as e:
            logger.error(f"Initial updates setup failed: {e}")

    threading.Thread(target=_kickoff_initial_updates, daemon=True).start()
    threading.Thread(target=run_startup_backtest, daemon=True).start()
    run_background_updates()


# ============================================================================
# HEALTH CHECK - Simple endpoint
# ============================================================================


@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}


# ============================================================================
# FRONTEND SERVING - Serve React build files
# ============================================================================

# Mount static files from the build directory
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
    """Serve the React frontend for any path not caught by API routes."""
    # Construct the path to the index.html file
    index_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "frontend", "build", "index.html"
    )

    # Check if the file exists
    if not os.path.exists(index_path):
        raise HTTPException(
            status_code=404,
            detail="Frontend not found. Make sure to build the frontend first.",
        )

    # Always return index.html for any non-API path, letting React Router handle it
    return FileResponse(index_path)

