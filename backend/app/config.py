import os
import sys
from enum import Enum
from typing import List, Tuple

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

BACKEND_ROOT = os.path.join(PROJECT_ROOT, "backend")
FRONTEND_ROOT = os.path.join(PROJECT_ROOT, "frontend")
FRONTEND_BUILD = os.path.join(FRONTEND_ROOT, "build")

MODELS_DATA_FILE = os.path.join(BACKEND_ROOT, "models_data.json")
BACKTEST_RESULTS_FILE = os.path.join(BACKEND_ROOT, "backtest_results.json")
NEWS_DATA_FILE = os.path.join(BACKEND_ROOT, "news_data.json")
SOCIAL_DATA_FILE = os.path.join(BACKEND_ROOT, "social_data.json")
SYSTEM_DATA_FILE = os.path.join(BACKEND_ROOT, "system_data.json")


def get_base_model_configs() -> List[Tuple[str, str]]:
    return [
        ("Claude 4 Sonnet", "claude-sonnet-4-20250514"),
        ("GPT-5", "gpt-5"),
        ("GPT-4 Turbo", "gpt-4-turbo"),
        ("GPT-4o Mini", "gpt-4o-mini"),
        ("Claude 3 Haiku", "claude-3-5-haiku-latest"),
        ("Gemini 2.5 Flash", "gemini-2-5-flash"),
        ("Llama 4 Maverick", "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"),
        ("Qwen3 235B", "Qwen/Qwen3-235B-A22B-Instruct-2507-tput"),
    ]


UPDATE_FREQUENCY = {
    "system_status": 60,
    "news_social": 600,
    "trading_cycle": 3600,
}

TRADING_CONFIG = {
    "initial_cash_stock": 1000,
    "initial_cash_polymarket": 500,
    "max_consecutive_failures": 3,
    "recovery_wait_time": 3600,
    "error_retry_time": 600,
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


class MockMode(str, Enum):
    NONE = "NONE"
    MOCK_AGENTS = "MOCK_AGENTS"
    MOCK_FETCHERS = "MOCK_FETCHERS"
    MOCK_AGENTS_AND_FETCHERS = "MOCK_AGENTS_AND_FETCHERS"


STOCK_MOCK_MODE = MockMode.NONE
POLYMARKET_MOCK_MODE = MockMode.NONE
