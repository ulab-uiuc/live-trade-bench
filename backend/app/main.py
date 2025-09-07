import asyncio
import logging
import os
import threading
import traceback
from datetime import datetime, timedelta

# 使用统一配置管理
from app.config import (
    ALLOWED_ORIGINS,
    FRONTEND_BUILD,
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


async def run_startup_backtest():
    """Run backtest for past week on startup using existing system."""
    try:
        print("🔄 Running startup backtest...")

        # Import here to avoid circular imports
        from live_trade_bench.backtesting import run_backtest

        # Use SINGLE source of truth for model configurations
        # Calculate past week dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=TRADING_CONFIG["backtest_days"])

        # 使用统一配置源
        base_models = get_base_model_configs()

        # Run backtests
        stock_results = await run_backtest(
            models=base_models,
            initial_cash=TRADING_CONFIG["initial_cash_stock"],
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            market_type="stock",
        )

        poly_results = await run_backtest(
            models=base_models,
            initial_cash=TRADING_CONFIG["initial_cash_polymarket"],
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            market_type="polymarket",
        )

        # Save results directly to models_data.json instead of separate file
        backtest_results = {
            "stock": stock_results,
            "polymarket": poly_results,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
        }

        # Import here to avoid circular dependency
        from .models_data import _save_backtest_data_to_models

        _save_backtest_data_to_models(backtest_results)

        print("✅ Startup backtest completed and saved to models_data.json")

    except Exception as e:
        print(f"❌ Startup backtest failed: {e}")
        traceback.print_exc()


# ============================================================================
# END STARTUP BACKTEST
# ============================================================================


# Background update function
def run_background_updates():
    """启动异步后台更新系统 - 消除线程复杂性"""

    async def system_status_updates():
        """系统状态更新 (高频)"""
        while True:
            try:
                update_system_status()
                await asyncio.sleep(UPDATE_FREQUENCY["system_status"])
            except Exception as e:
                print(f"❌ System status update error: {e}")
                await asyncio.sleep(60)

    async def news_social_updates():
        """新闻社交更新 (中频)"""
        while True:
            try:
                update_news_data()
                update_social_data()
                await asyncio.sleep(UPDATE_FREQUENCY["news_social"])
            except Exception as e:
                print(f"❌ News/Social update error: {e}")
                await asyncio.sleep(60)

    async def trading_cycle_updates():
        """交易周期更新 (低频) - 纯异步实现"""
        consecutive_failures = 0
        max_failures = TRADING_CONFIG["max_consecutive_failures"]

        while True:
            try:
                print("🤖 Running hourly trading cycle...")

                # Import here to avoid circular imports
                from .models_data import get_models_data, trigger_cycle

                # 直接调用异步函数，无需创建新循环
                cycle_result = await trigger_cycle()

                if cycle_result.get("status") == "success":
                    consecutive_failures = 0  # 重置失败计数
                    print("✅ Hourly trading cycle completed successfully")

                    # 更新模型数据 - 添加防御性检查
                    try:
                        models = get_models_data()
                        if models is not None:
                            print(f"📊 Updated {len(models)} models data")
                        else:
                            print("⚠️ Warning: get_models_data() returned None")
                    except Exception as e:
                        print(f"⚠️ Error updating models data: {e}")

                    # 正常等待下次交易
                    print("⏰ Next trading cycle in 60 minutes...")
                    await asyncio.sleep(UPDATE_FREQUENCY["trading"])

                else:
                    consecutive_failures += 1
                    print(
                        f"⚠️ Trading cycle had issues ({consecutive_failures}/{max_failures}): {cycle_result.get('message', 'Unknown')}"
                    )

                    if consecutive_failures >= max_failures:
                        print(
                            "❌ Too many trading failures, entering recovery mode (1 hour wait)"
                        )
                        await asyncio.sleep(TRADING_CONFIG["recovery_wait_time"])
                        consecutive_failures = 0
                    else:
                        await asyncio.sleep(TRADING_CONFIG["error_retry_time"])

            except Exception as e:
                consecutive_failures += 1
                print(
                    f"❌ Trading update error ({consecutive_failures}/{max_failures}): {e}"
                )
                import traceback

                traceback.print_exc()

                if consecutive_failures >= max_failures:
                    print("❌ Critical trading errors, entering recovery mode")
                    await asyncio.sleep(TRADING_CONFIG["recovery_wait_time"])
                    consecutive_failures = 0
                else:
                    await asyncio.sleep(TRADING_CONFIG["error_retry_time"])

    # 在后台任务中启动异步任务 - 消除线程复杂性
    def start_background_tasks():
        """在线程中运行异步任务组"""

        async def run_all_tasks():
            # 并发运行所有后台任务
            await asyncio.gather(
                system_status_updates(),
                news_social_updates(),
                trading_cycle_updates(),
                return_exceptions=True,  # 一个任务失败不影响其他任务
            )

        # 为后台线程创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_all_tasks())
        finally:
            loop.close()

    # 启动单个后台线程运行所有异步任务
    background_thread = threading.Thread(target=start_background_tasks, daemon=True)
    background_thread.start()

    print("🚀 Optimized background updates started:")
    print(f"   📊 System status: every {UPDATE_FREQUENCY['system_status']}s")
    print(f"   📰 News/Social: every {UPDATE_FREQUENCY['news_social']}s")
    print(f"   🤖 Trading: every {UPDATE_FREQUENCY['trading']}s")

    logger.info("Optimized multi-frequency background updates active")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "API is running"}


@app.on_event("startup")
async def startup_event():
    """Initialize API with complete trading workflow."""
    logger.info("Starting Live Trade Bench API")

    # Step 1: Run 7-day backtest for historical baseline
    try:
        print("📈 Step 1: Running 7-day backtest for historical data...")
        await run_startup_backtest()
        logger.info("✅ 7-day backtest completed successfully")
    except Exception as e:
        logger.warning(f"⚠️ Startup backtest failed: {e}")
        import traceback

        traceback.print_exc()

    # Step 2: Run initial trading cycle for current state
    try:
        print("🤖 Step 2: Running initial trading cycle...")
        from .models_data import get_models_data, trigger_cycle

        cycle_result = await trigger_cycle()

        if cycle_result.get("status") == "success":
            print("✅ Initial trading cycle completed")
        else:
            print(
                f"⚠️ Initial trading had issues: {cycle_result.get('message', 'Unknown')}"
            )

        # Generate complete models data (backtest + current trading)
        models = get_models_data()
        logger.info(f"✅ Generated {len(models)} models with complete data")

    except Exception as e:
        logger.warning(f"⚠️ Initial trading setup failed: {e}")
        import traceback

        traceback.print_exc()

    # Step 3: Start multi-frequency background updates (including hourly trading)
    try:
        print("🔄 Step 3: Starting background update systems...")
        run_background_updates()
        logger.info("✅ Multi-frequency background updates started")

        print("🎯 Live Trade Bench initialization complete!")
        print("   📊 Historical data: 7-day backtest")
        print("   🤖 Current state: Initial trading cycle")
        print("   ⏰ Future updates: Hourly automatic trading")

    except Exception as e:
        logger.error(f"❌ Failed to start background updates: {e}")
        import traceback

        traceback.print_exc()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down API")


# Serve React frontend using centralized config
if os.path.exists(FRONTEND_BUILD):
    app.mount(
        "/static",
        StaticFiles(directory=os.path.join(FRONTEND_BUILD, "static")),
        name="static",
    )


@app.get("/{path:path}")
async def serve_frontend(path: str):
    """Serve React frontend files."""
    # Serve index.html for all routes (SPA)
    index_file = os.path.join(FRONTEND_BUILD, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    else:
        raise HTTPException(status_code=404, detail="Frontend not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5001)
