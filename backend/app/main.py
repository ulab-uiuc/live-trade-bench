import logging
import os
import threading
import time

# 使用统一配置管理
from app.config import ALLOWED_ORIGINS, UPDATE_FREQUENCY
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
    2. Start background update threads
    """
    logger.info("🚀 FastAPI app starting up...")

    # 1. Initial data generation (if files don't exist)
    from app.models_data import get_models_data
    from app.news_data import update_news_data
    from app.social_data import update_social_data
    from app.system_data import update_system_status

    # Check for models.json, if not present, generate it
    if not os.path.exists("backend/models_data.json"):
        logger.info("models_data.json not found, generating initial data...")
        get_models_data()

    # Generate other data files if they don't exist
    if not os.path.exists("backend/news_data.json"):
        update_news_data()
    if not os.path.exists("backend/social_data.json"):
        update_social_data()
    if not os.path.exists("backend/system_data.json"):
        update_system_status()

    # 2. Start all background updates
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
