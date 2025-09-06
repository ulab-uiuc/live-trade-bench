import logging
import os
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict

from app.routers import models, news, social, system
from app.models_data import get_models_data
from app.news_data import update_news_data
from app.social_data import update_social_data
from app.system_data import update_system_status

# Removed complex trading system - now just simple data provider
from fastapi import FastAPI, HTTPException, Request
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


# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next: Callable[[Request], Any]) -> Any:
    start_time = time.time()

    # Log incoming request
    logger.info(f"→ {request.method} {request.url.path}")

    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Log response with status code and time
    status_emoji = (
        "✅"
        if response.status_code == 200
        else "❌"
        if response.status_code >= 400
        else "⚠️"
    )
    logger.info(
        f"{status_emoji} {response.status_code} {request.method} {request.url.path} - {process_time:.3f}s"
    )

    return response


allowed_origins = [
    "http://localhost:3000",  # React dev server
    "https://localhost:3000",  # React dev server with HTTPS
]

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

# Global background fetcher control
_parallel_fetcher_running = False
_parallel_fetcher_thread = None


def _parallel_background_fetcher():
    """Background thread that fetches news and social media data in parallel"""
    global _parallel_fetcher_running

    while _parallel_fetcher_running:
        try:
            print("🔄 Starting parallel background data fetch...")
            start_time = time.time()

            # Use a simpler approach - trigger the endpoints that will do parallel fetching
            import requests

            # Use ThreadPoolExecutor for parallel endpoint calls
            with ThreadPoolExecutor(max_workers=4) as executor:
                # Submit all fetch tasks in parallel via HTTP calls
                futures = [
                    executor.submit(
                        lambda: requests.get(
                            "http://localhost:5001/api/news/stock?limit=15", timeout=60
                        )
                    ),
                    executor.submit(
                        lambda: requests.get(
                            "http://localhost:5001/api/news/polymarket?limit=15",
                            timeout=60,
                        )
                    ),
                    executor.submit(
                        lambda: requests.get(
                            "http://localhost:5001/api/social/stock?limit=15",
                            timeout=60,
                        )
                    ),
                    executor.submit(
                        lambda: requests.get(
                            "http://localhost:5001/api/social/polymarket?limit=15",
                            timeout=60,
                        )
                    ),
                ]

                # Wait for all tasks to complete
                results = []
                for i, future in enumerate(futures):
                    try:
                        response = future.result(
                            timeout=70
                        )  # 70 second timeout per task
                        if response.status_code == 200:
                            data = response.json()
                            results.append(data)
                            task_names = [
                                "Stock News",
                                "Polymarket News",
                                "Stock Social",
                                "Polymarket Social",
                            ]
                            print(f"   ✅ {task_names[i]}: {len(data)} items")
                        else:
                            task_names = [
                                "Stock News",
                                "Polymarket News",
                                "Stock Social",
                                "Polymarket Social",
                            ]
                            print(
                                f"   ❌ {task_names[i]} failed: HTTP {response.status_code}"
                            )
                            results.append([])
                    except Exception as e:
                        task_names = [
                            "Stock News",
                            "Polymarket News",
                            "Stock Social",
                            "Polymarket Social",
                        ]
                        print(f"   ❌ {task_names[i]} failed: {e}")
                        results.append([])

            elapsed = time.time() - start_time
            total_items = sum(len(r) for r in results)
            print(f"🎉 Parallel fetch completed: {total_items} items in {elapsed:.2f}s")

            # Wait 30 minutes before next fetch
            time.sleep(30 * 60)

        except Exception as e:
            print(f"❌ Parallel background fetcher error: {e}")
            import traceback

            traceback.print_exc()
            time.sleep(5 * 60)  # Wait 5 minutes on error


def start_parallel_background_fetchers():
    """Start the parallel background fetcher"""
    global _parallel_fetcher_running, _parallel_fetcher_thread

    if _parallel_fetcher_running:
        return

    _parallel_fetcher_running = True
    _parallel_fetcher_thread = threading.Thread(
        target=_parallel_background_fetcher, daemon=True
    )
    _parallel_fetcher_thread.start()
    print("🚀 Parallel background data fetcher started")


def stop_parallel_background_fetchers():
    """Stop the parallel background fetcher"""
    global _parallel_fetcher_running
    _parallel_fetcher_running = False
    print("⏹️ Parallel background data fetcher stopped")


# Background trading task
_trading_cycle_running = False
_trading_cycle_thread = None


def _background_trading_cycle_runner():
    """Background thread that periodically runs the trading cycle."""
    global _trading_cycle_running
    print("🚀 Background trading cycle runner started")

    while _trading_cycle_running:
        try:
            print("AUTOMATION: 🤖 Triggering 15-minute automatic trading cycle...")
            from app.models_data import trigger_cycle

            trigger_cycle()
            print("AUTOMATION: ✅ Trading cycle finished. Waiting for 15 minutes.")

            # Wait for 15 minutes, but check for shutdown every second
            for _ in range(15 * 60):
                if not _trading_cycle_running:
                    break
                time.sleep(1)

        except Exception as e:
            print(f"AUTOMATION: ❌ Error in background trading cycle: {e}")
            import traceback

            traceback.print_exc()
            # Wait 5 minutes on error before retrying
            time.sleep(5 * 60)


def start_background_trader():
    """Start the background trading cycle runner."""
    global _trading_cycle_running, _trading_cycle_thread
    if _trading_cycle_running:
        return
    _trading_cycle_running = True
    _trading_cycle_thread = threading.Thread(
        target=_background_trading_cycle_runner, daemon=True
    )
    _trading_cycle_thread.start()


def stop_background_trader():
    """Stop the background trading cycle runner."""
    global _trading_cycle_running
    if _trading_cycle_running:
        _trading_cycle_running = False
        print("⏹️ Background trading cycle runner stopped")


def run_background_updates():
    """Periodically run all background data updates."""
    while True:
        # Update models data every minute
        print("--- [BACKGROUND] Triggering model data update ---")
        try:
            get_models_data()
            print("--- [BACKGROUND] Model data update finished ---")
        except Exception:
            print("--- [BACKGROUND] Error in model update ---")
            traceback.print_exc()
        
        # Update system status every minute
        print("--- [BACKGROUND] Triggering system status update ---")
        try:
            update_system_status()
            print("--- [BACKGROUND] System status update finished ---")
        except Exception:
            print("--- [BACKGROUND] Error in system status update ---")
            traceback.print_exc()
        
        # Update news and social data every 10 minutes (check cycle count)
        cycle_count = getattr(run_background_updates, 'cycle_count', 0)
        if cycle_count % 10 == 0:  # Every 10th cycle (10 minutes)
            print("--- [BACKGROUND] Triggering news data update ---")
            try:
                update_news_data()
                print("--- [BACKGROUND] News data update finished ---")
            except Exception:
                print("--- [BACKGROUND] Error in news update ---")
                traceback.print_exc()
            
            print("--- [BACKGROUND] Triggering social data update ---")
            try:
                update_social_data()
                print("--- [BACKGROUND] Social data update finished ---")
            except Exception:
                print("--- [BACKGROUND] Error in social update ---")
                traceback.print_exc()
        
        run_background_updates.cycle_count = cycle_count + 1
        time.sleep(60) # Wait for 60 seconds


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Live Trade Bench API")
    try:
        start_background_trader()
        logger.info("🚀 Automatic trading cycle enabled (15-minute interval)")
    except Exception as e:
        logger.warning(f"Failed to start background trader: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Live Trade Bench API")
    try:
        stop_background_trader()
        logger.info("Background trader stopped")
    except Exception as e:
        logger.warning(f"Failed to stop background trader cleanly: {e}")


@app.get("/api")
async def api_root() -> Dict[str, Any]:
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


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {"status": "healthy", "message": "API is running"}


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize API on startup."""
    logger.info("Starting Live Trade Bench API")

    # Disable background fetchers completely for now
    try:
        # start_parallel_background_fetchers()  # Completely disabled
        logger.info("Background fetchers completely disabled")
    except Exception as e:
        logger.warning(f"Failed to start background fetchers: {e}")

    # Start the background task
    thread = threading.Thread(target=run_background_updates, daemon=True)
    thread.start()
    print("Background update thread started.")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup on shutdown."""
    logger.info("Shutting down API")

    # Stop parallel background data fetcher
    try:
        stop_parallel_background_fetchers()
        logger.info("Parallel background data fetcher stopped")
    except Exception as e:
        logger.warning(f"Failed to stop background fetchers: {e}")


frontend_build_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "..", "frontend", "build"
)

# Serve static files
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(frontend_build_path, "static")),
    name="static",
)


# Catch-all route for React Router (must be last)
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str) -> Any:
    """Serve React frontend for all non-API routes."""
    # Don't serve frontend for API routes
    if (
        full_path.startswith("api/")
        or full_path.startswith("docs")
        or full_path.startswith("redoc")
    ):
        raise HTTPException(status_code=404, detail="API endpoint not found")

    # Serve index.html for React Router
    index_file = os.path.join(frontend_build_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    else:
        raise HTTPException(status_code=404, detail="Frontend not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5001)
