"""
配置管理 - 单一配置源
统一管理所有路径、常量和系统配置
"""

import os
import sys
from typing import List, Tuple

# ============================================================================
# 路径管理 - 计算一次，到处使用
# ============================================================================

# 项目根目录 (live-trade-bench/)
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

# 确保 live_trade_bench 在 Python 路径中
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 后端目录结构
BACKEND_ROOT = os.path.join(PROJECT_ROOT, "backend")
FRONTEND_ROOT = os.path.join(PROJECT_ROOT, "frontend")
FRONTEND_BUILD = os.path.join(FRONTEND_ROOT, "build")

# 数据文件路径 - 标准化命名
MODELS_DATA_FILE = os.path.join(BACKEND_ROOT, "models_data.json")
NEWS_DATA_FILE = os.path.join(BACKEND_ROOT, "news_data.json")
SOCIAL_DATA_FILE = os.path.join(BACKEND_ROOT, "social_data.json")
SYSTEM_DATA_FILE = os.path.join(BACKEND_ROOT, "system_data.json")

# ============================================================================
# 模型配置 - 单一配置源
# ============================================================================


def get_base_model_configs() -> List[Tuple[str, str]]:
    """单一配置源：所有模型配置的权威来源

    Returns:
        List[Tuple[str, str]]: [(display_name, model_id), ...]
    """
    return [
        ("Claude 3.5 Sonnet", "claude-3-5-sonnet-20241022"),
        ("GPT-4 Turbo", "gpt-4-turbo"),
        ("GPT-4o Mini", "gpt-4o-mini"),
        ("Claude 3 Haiku", "claude-3-haiku-20240307"),
        ("Gemini Pro", "gemini-pro"),
        ("Llama 3.1", "llama-3.1-70b-versatile"),
        ("Qwen/Qwen2.5-Instruct-Turbo", "qwen/qwen2.5-7b-instruct-turbo"),
    ]


# ============================================================================
# 系统常量
# ============================================================================

# 更新频率 (秒)
UPDATE_FREQUENCY = {
    "system_status": 60,  # 1分钟
    "news_social": 600,  # 10分钟
    "trading": 3600,  # 60分钟
    "trading_cycle": 3600,  # 60分钟 - 别名
}

# 交易配置
TRADING_CONFIG = {
    "initial_cash_stock": 1000,
    "initial_cash_polymarket": 500,
    "max_consecutive_failures": 3,
    "recovery_wait_time": 3600,  # 1小时
    "error_retry_time": 600,  # 10分钟
}

# 服务器配置
SERVER_CONFIG = {
    "default_port": 5001,
    "workers": 1,
    "reload": False,
}

# CORS 允许的源
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

# ============================================================================
# 工具函数
# ============================================================================


def ensure_data_directory():
    """确保数据目录存在"""
    os.makedirs(BACKEND_ROOT, exist_ok=True)


def get_data_file_path(file_type: str) -> str:
    """获取数据文件路径

    Args:
        file_type: 'models', 'news', 'social', 'system'
    """
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


# Mock 配置
USE_MOCK_AGENTS = False  # 改为True使用mock agents
USE_MOCK_FETCHERS = False  # 改为True使用mock fetchers
