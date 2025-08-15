import atexit
import logging
import os
import time

from app.routers import (
    model_actions,
    models,
    news,
    polymarket,
    social,
    system_logs,
    trades,
)
from app.trading_system import start_trading_system, stop_trading_system
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Live Trade Bench API",
    description="FastAPI backend for trading dashboard with models, trades, and news data",
    version="1.0.0",
)


# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
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
app.include_router(trades.router)
app.include_router(news.router)
app.include_router(social.router)
app.include_router(system_logs.router)
app.include_router(model_actions.router)
app.include_router(polymarket.router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Live Trade Bench API",
        "version": "1.0.0",
        "endpoints": {
            "models": "/api/models",
            "model-actions": "/api/model-actions",
            "trades": "/api/trades",
            "news": "/api/news",
            "social": "/api/social",
            "system-log": "/api/system-log",
            "polymarket": "/api/polymarket",
            "docs": "/docs",
            "redoc": "/redoc",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "API is running"}


@app.on_event("startup")
async def startup_event():
    """Initialize trading system on startup."""
    logger.info("Starting Live Trade Bench API with AI trading system")
    start_trading_system()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down trading system")
    stop_trading_system()


# Register cleanup on exit
atexit.register(stop_trading_system)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
