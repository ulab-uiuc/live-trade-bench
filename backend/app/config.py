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
MODELS_DATA_INIT_FILE = os.path.join(BACKEND_ROOT, "models_data_init.json")
BACKTEST_RESULTS_FILE = os.path.join(BACKEND_ROOT, "backtest_results.json")
NEWS_DATA_FILE = os.path.join(BACKEND_ROOT, "news_data.json")
SOCIAL_DATA_FILE = os.path.join(BACKEND_ROOT, "social_data.json")
SYSTEM_DATA_FILE = os.path.join(BACKEND_ROOT, "system_data.json")


def get_base_model_configs() -> List[Tuple[str, str]]:
    return [
        ("GPT-5", "openai/gpt-5"),
        ("GPT-5 Nano", "openai/gpt-5-nano"),
        ("GPT-5 Mini", "openai/gpt-5-mini"),
        ("GPT-4.1", "openai/gpt-4.1"),
        ("GPT-4.1 Mini", "openai/gpt-4.1-mini"),
        ("GPT-4.1 Nano", "openai/gpt-4.1-nano"),
        ("GPT-4o Mini", "openai/gpt-4o-mini"),
        ("GPT-o3", "openai/o3-2025-04-16"),
        ("Claude Sonnet 4.1", "anthropic/claude-opus-4-1-20250805"),
        ("Claude Sonnet 4", "anthropic/claude-sonnet-4-20250514"),
        ("Claude Sonnet 3.7", "anthropic/claude-3-7-sonnet-latest"),
        ("Claude Haiku 3.5", "anthropic/claude-3-5-haiku-latest"),
        ("GPT OSS 120B", "openai/gpt-oss-120b"),
        ("Llama 4 Maverick", "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"),
        ("Llama 4 Scout", "meta-llama/Llama-4-Scout-17B-16E-Instruct"),
        ("Llama 3.3 70B", "meta-llama/Llama-3.3-70B-Instruct-Turbo"),
        ("Qwen3 235B", "Qwen/Qwen3-235B-A22B-Instruct-2507-tput"),
        ("DeepSeek V3", "deepseek-ai/DeepSeek-V3"),
        ("Deepseek V3.1", "deepseek-ai/DeepSeek-V3.1"),
        ("Kimi K2", "moonshotai/Kimi-K2-Instruct-0905"),
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
