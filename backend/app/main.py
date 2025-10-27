import json
import logging
import os
import shutil
from datetime import datetime

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
from live_trade_bench.systems import (
    BitMEXPortfolioSystem,
    PolymarketPortfolioSystem,
    StockPortfolioSystem,
)

from .config import (
    ALLOWED_ORIGINS,
    MODELS_DATA_FILE,
    MODELS_DATA_HIST_FILE,
    MODELS_DATA_INIT_FILE,
    POLYMARKET_MOCK_MODE,
    STOCK_MOCK_MODE,
    UPDATE_FREQUENCY,
    MockMode,
    get_base_model_configs,
    should_run_trading_cycle,
)
from .models_data import generate_models_data, load_historical_data_to_accounts
from .news_data import update_news_data
from .price_data import (
    get_next_price_update_time,
    update_bitmex_prices_and_values,
    update_polymarket_prices_and_values,
    update_stock_prices_and_values,
)
from .routers import models, news, social, system
from .social_data import update_social_data
from .system_data import update_system_status

# Global system instances - Initialize immediately
stock_system = None
polymarket_system = None
bitmex_system = None
# Background scheduler instance; assigned during startup to keep reference alive
scheduler = None

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
bitmex_system = BitMEXPortfolioSystem()

# Add agents for real systems
if STOCK_MOCK_MODE == MockMode.NONE:
    for display_name, model_id in get_base_model_configs():
        stock_system.add_agent(display_name, 1000.0, model_id)

if POLYMARKET_MOCK_MODE == MockMode.NONE:
    for display_name, model_id in get_base_model_configs():
        polymarket_system.add_agent(display_name, 500.0, model_id)

# Add BitMEX agents (paper trading with $10,000 each)
for display_name, model_id in get_base_model_configs():
    bitmex_system.add_agent(display_name, 10000.0, model_id)

# 🆕 加载历史数据到Account内存中
print("🔄 Loading historical data to account memory...")
load_historical_data_to_accounts(stock_system, polymarket_system, bitmex_system)
print("✅ Historical data loading completed")

stock_system.initialize_for_live()
polymarket_system.initialize_for_live()
bitmex_system.initialize_for_live()


def get_stock_system():
    """Get the current stock system instance (real or mock)."""
    global stock_system
    return stock_system


def get_polymarket_system():
    """Get the current polymarket system instance (real or mock)."""
    global polymarket_system
    return polymarket_system


def get_bitmex_system():
    """Get the BitMEX system instance."""
    global bitmex_system
    return bitmex_system


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


@app.get("/api/schedule/next-price-update")
def get_next_price_update():
    """Expose the next scheduled realtime price update."""
    stock_time = get_next_price_update_time("stock")
    poly_time = get_next_price_update_time("polymarket")

    response = {
        "stock": stock_time.isoformat() if stock_time else None,
        "polymarket": poly_time.isoformat() if poly_time else None,
    }

    # Backward compatibility for older clients expecting single field
    response["next_run_time"] = response["stock"]

    return response


def load_backtest_as_initial_data():
    """Load backtest data as initial trading data if no live data exists."""
    if not os.path.exists(MODELS_DATA_FILE) and os.path.exists(MODELS_DATA_INIT_FILE):
        try:
            # Import helper functions from models_data
            from .models_data import _create_compact_model_data

            # Read init file
            with open(MODELS_DATA_INIT_FILE, "r") as f:
                init_data = json.load(f)

            # Copy full data to hist file
            shutil.copy(MODELS_DATA_INIT_FILE, MODELS_DATA_HIST_FILE)
            os.chmod(MODELS_DATA_HIST_FILE, 0o644)
            logger.info("📚 Created complete historical data file")

            # Create compact version for frontend
            compact_data = [_create_compact_model_data(model) for model in init_data]
            with open(MODELS_DATA_FILE, "w") as f:
                json.dump(compact_data, f, indent=4)
            os.chmod(MODELS_DATA_FILE, 0o644)

            logger.info(
                "📊 Loaded backtest data as initial trading data (compact frontend + full hist)"
            )
        except Exception as e:
            logger.error(f"❌ Failed to load backtest data: {e}")


def safe_generate_models_data():
    if should_run_trading_cycle():
        logger.info("🕐 Running trading cycle at market close time...")
        generate_models_data(stock_system, polymarket_system, bitmex_system)
    else:
        logger.info("⏰ Skipping trading cycle - not in market time window")


def safe_generate_bitmex_cycle():
    """Run BitMEX trading cycle (24/7 crypto markets)."""
    logger.info("🔄 Running BitMEX trading cycle...")
    try:
        bitmex_system.run_cycle()
        logger.info("✅ BitMEX cycle completed")
    except Exception as e:
        logger.error(f"❌ BitMEX cycle failed: {e}")


def schedule_background_tasks(scheduler: BackgroundScheduler):
    from datetime import timedelta

    import pytz

    utc_now = datetime.now(pytz.UTC)
    est_now = utc_now.astimezone(pytz.timezone("US/Eastern"))
    is_dst = est_now.dst() != timedelta(0)

    if is_dst:
        schedule_hour = 19
        schedule_desc = "3:00 PM EDT"
    else:
        schedule_hour = 20
        schedule_desc = "3:00 PM EST"

    scheduler.add_job(
        safe_generate_models_data,
        "cron",
        day_of_week="mon-fri",
        hour=schedule_hour,
        minute=0,
        timezone="UTC",
        id="generate_models_data",
        replace_existing=True,
    )
    logger.info(f"📅 Scheduled trading job for UTC {schedule_hour}:00 ({schedule_desc})")

    # Schedule BitMEX cycles 4x daily (00:00, 06:00, 12:00, 18:00 UTC)
    for hour in [0, 6, 12, 18]:
        scheduler.add_job(
            safe_generate_bitmex_cycle,
            "cron",
            hour=hour,
            minute=0,
            timezone="UTC",
            id=f"bitmex_cycle_{hour:02d}00",
            replace_existing=True,
        )
    logger.info("📅 Scheduled BitMEX cycles 4x daily (00:00, 06:00, 12:00, 18:00 UTC)")

    price_interval = UPDATE_FREQUENCY["realtime_prices"]
    logger.info(
        f"📈 Scheduled stock price update job for every {price_interval} seconds ({price_interval//60} minutes)"
    )
    scheduler.add_job(
        update_stock_prices_and_values,
        "interval",
        seconds=price_interval,
        id="update_stock_prices",
        replace_existing=True,
    )

    polymarket_interval = UPDATE_FREQUENCY["polymarket_prices"]
    logger.info(
        f"📊 Scheduled polymarket price update job for every {polymarket_interval} seconds ({polymarket_interval//60} minutes)"
    )
    scheduler.add_job(
        update_polymarket_prices_and_values,
        "interval",
        seconds=polymarket_interval,
        id="update_polymarket_prices",
        replace_existing=True,
    )

    # BitMEX price updates (every 10 minutes, 24/7)
    bitmex_interval = 600  # 10 minutes
    logger.info(
        f"📈 Scheduled BitMEX price update job for every {bitmex_interval} seconds ({bitmex_interval//60} minutes)"
    )
    scheduler.add_job(
        update_bitmex_prices_and_values,
        "interval",
        seconds=bitmex_interval,
        id="update_bitmex_prices",
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

    # Ensure initial data exists before any scheduled jobs run
    load_backtest_as_initial_data()

    # Start background scheduler
    global scheduler
    # Allow background jobs to run concurrently so a slow price update doesn't block
    executors = {"default": ThreadPoolExecutor(max_workers=4)}
    scheduler = BackgroundScheduler(executors=executors)
    schedule_background_tasks(scheduler)
    scheduler.start()

    logger.info("✅ Background scheduler started.")

    # Run all initial data generation in background threads - don't block startup
    # threading.Thread(
    #     target=lambda: generate_models_data(stock_system, polymarket_system),
    #     daemon=True,
    # ).start()

    # threading.Thread(target=update_news_data, daemon=True).start()
    # threading.Thread(target=update_social_data, daemon=True).start()

    logger.info("🚀 FastAPI app startup completed - data loading in background")


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
