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
}

TRADING_CONFIG = {
    "initial_cash_stock": 1000,
    "initial_cash_polymarket": 500,
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


def get_current_est_time() -> datetime:
    return datetime.now(pytz.timezone("US/Eastern"))


def is_trading_day() -> bool:
    est_now = get_current_est_time()
    return est_now.weekday() in MARKET_HOURS["trading_days"]


def should_run_trading_cycle() -> bool:
    if not is_trading_day():
        return False

    est_now = get_current_est_time()
    current_time = est_now.time()

    close_time = time.fromisoformat(MARKET_HOURS["stock_close"])

    # Correctly handle minute subtraction that might go negative
    run_minute = close_time.minute - MARKET_HOURS["run_before_close_minutes"]
    run_hour = close_time.hour
    if run_minute < 0:
        run_hour -= 1
        run_minute += 60

    run_time = time(run_hour, run_minute)

    # Create a 5-minute tolerance window
    start_minute = run_time.minute - 5
    start_hour = run_time.hour
    if start_minute < 0:
        start_hour -= 1
        start_minute += 60

    run_window_start = time(start_hour, start_minute)

    # Calculate end of window (5 minutes past close)
    end_minute = close_time.minute + 5
    end_hour = close_time.hour
    if end_minute >= 60:
        end_hour += 1
        end_minute -= 60
    run_window_end = time(end_hour, end_minute)

    return run_window_start <= current_time <= run_window_end


class MockMode(str, Enum):
    NONE = "NONE"
    MOCK_AGENTS = "MOCK_AGENTS"
    MOCK_FETCHERS = "MOCK_FETCHERS"
    MOCK_AGENTS_AND_FETCHERS = "MOCK_AGENTS_AND_FETCHERS"


STOCK_MOCK_MODE = MockMode.NONE
POLYMARKET_MOCK_MODE = MockMode.NONE
