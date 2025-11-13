import os
import sys
from datetime import datetime, time
from enum import Enum
from typing import List, Tuple

import pytz

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

BACKEND_ROOT = os.path.join(PROJECT_ROOT, "backend")
FRONTEND_ROOT = os.path.join(PROJECT_ROOT, "frontend")
FRONTEND_BUILD = os.path.join(FRONTEND_ROOT, "build")

MODELS_DATA_FILE = os.path.join(BACKEND_ROOT, "models_data.json")
MODELS_DATA_HIST_FILE = os.path.join(BACKEND_ROOT, "models_data_hist.json")
MODELS_DATA_INIT_FILE = os.path.join(BACKEND_ROOT, "models_data_init.json")
BACKTEST_RESULTS_FILE = os.path.join(BACKEND_ROOT, "backtest_results.json")
NEWS_DATA_FILE = os.path.join(BACKEND_ROOT, "news_data.json")
SOCIAL_DATA_FILE = os.path.join(BACKEND_ROOT, "social_data.json")
SYSTEM_DATA_FILE = os.path.join(BACKEND_ROOT, "system_data.json")


def get_base_model_configs() -> List[Tuple[str, str]]:
    return [
        ("GPT-5", "openai/gpt-5"),
        ("GPT-4.1", "openai/gpt-4.1"),
        ("GPT-4o", "openai/gpt-4o"),
        ("GPT-o3", "openai/o3-2025-04-16"),
        ("Claude-Opus-4.1", "anthropic/claude-opus-4-1-20250805"),
        ("Claude-Opus-4", "anthropic/claude-opus-4-20250514"),
        ("Claude-Sonnet-4.5", "anthropic/claude-sonnet-4-5-20250929"),
        ("Claude-Sonnet-4", "anthropic/claude-sonnet-4-20250514"),
        ("Claude-Sonnet-3.7", "anthropic/claude-3-7-sonnet-latest"),
        ("Gemini-2.5-Flash", "gemini/gemini-2.5-flash"),
        ("Gemini-2.5-Pro", "gemini/gemini-2.5-pro"),
        ("Grok-4", "xai/grok-4"),
        ("Grok-3", "xai/grok-3"),
        ("Llama4-Maverick", "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"),
        ("Llama4-Scout", "meta-llama/Llama-4-Scout-17B-16E-Instruct"),
        ("Llama3.3-70B-Instruct-Turbo", "meta-llama/Llama-3.3-70B-Instruct-Turbo"),
        ("Qwen3-235B-A22B-Instruct", "Qwen/Qwen3-235B-A22B-Instruct-2507-tput"),
        ("Qwen3-235B-A22B-Thinking", "Qwen/Qwen3-235B-A22B-Thinking-2507"),
        ("Qwen2.5-72B-Instruct", "Qwen/Qwen2.5-72B-Instruct-Turbo"),
        ("DeepSeek-R1", "deepseek-ai/DeepSeek-R1"),
        ("DeepSeek-V3.1", "deepseek-ai/DeepSeek-V3.1"),
        ("Kimi-K2-Instruct", "moonshotai/Kimi-K2-Instruct-0905"),
    ]


UPDATE_FREQUENCY = {
    "system_status": 60,
    "news_social": 600,
    "trading_cycle": "daily_before_close",
    "realtime_prices": 600,  # Stock prices: 10 minutes
    "polymarket_prices": 1800,  # Polymarket prices: 30 minutes by default
}

TRADING_CONFIG = {
    "initial_cash_stock": 1000,
    "initial_cash_polymarket": 500,
    "initial_cash_bitmex": 1000,
    "max_consecutive_failures": 3,
    "recovery_wait_time": 3600,
    "error_retry_time": 600,
}

MARKET_HOURS = {
    "stock_open": "09:30",
    "stock_close": "16:00",
    "trading_days": [0, 1, 2, 3, 4],
    "run_before_close_minutes": 60,
}

SERVER_CONFIG = {
    "default_port": 5001,
    "workers": 1,
    "reload": False,
}

ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React dev server
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:5001",  # Backend server
    "http://127.0.0.1:5001",
    "https://live-trade-bench.herokuapp.com",
    "https://live-trade-bench-frontend.herokuapp.com",
]


def ensure_data_directory():
    os.makedirs(BACKEND_ROOT, exist_ok=True)


def get_data_file_path(file_type: str) -> str:
    mapping = {
        "models": MODELS_DATA_FILE,
        "news": NEWS_DATA_FILE,
        "social": SOCIAL_DATA_FILE,
        "system": SYSTEM_DATA_FILE,
    }

    if file_type not in mapping:
        raise ValueError(
            f"Unknown file type: {file_type}. Valid types: {list(mapping.keys())}"
        )

    return mapping[file_type]


def is_trading_day() -> bool:
    utc_now = datetime.now(pytz.UTC)
    est_now = utc_now.astimezone(pytz.timezone("US/Eastern"))
    return est_now.weekday() in MARKET_HOURS["trading_days"]


def should_run_trading_cycle() -> bool:
    if not is_trading_day():
        return False

    utc_now = datetime.now(pytz.UTC)
    current_utc_time = utc_now.time()

    est_now = utc_now.astimezone(pytz.timezone("US/Eastern"))

    from datetime import timedelta

    is_dst = est_now.dst() != timedelta(0)

    if is_dst:
        run_window_start = time(18, 55)  # UTC 18:55 (美东 2:55 PM EDT)
        run_window_end = time(20, 5)  # UTC 20:05 (美东 4:05 PM EDT)
    else:
        run_window_start = time(19, 55)  # UTC 19:55 (美东 2:55 PM EST)
        run_window_end = time(21, 5)  # UTC 21:05 (美东 4:05 PM EST)

    return run_window_start <= current_utc_time <= run_window_end


def is_market_hours() -> bool:
    if not is_trading_day():
        return False

    utc_now = datetime.now(pytz.UTC)
    est_now = utc_now.astimezone(pytz.timezone("US/Eastern"))

    stock_open = datetime.strptime(MARKET_HOURS["stock_open"], "%H:%M").time()
    stock_close = datetime.strptime(MARKET_HOURS["stock_close"], "%H:%M").time()

    current_time = est_now.time()

    return stock_open <= current_time <= stock_close


class MockMode(str, Enum):
    NONE = "NONE"
    MOCK_AGENTS = "MOCK_AGENTS"
    MOCK_FETCHERS = "MOCK_FETCHERS"
    MOCK_AGENTS_AND_FETCHERS = "MOCK_AGENTS_AND_FETCHERS"


STOCK_MOCK_MODE = MockMode.NONE
POLYMARKET_MOCK_MODE = MockMode.NONE
BITMEX_MOCK_MODE = MockMode.NONE
