"""
System status data provider
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict

# 使用统一配置管理
from app.config import MODELS_DATA_FILE, SYSTEM_DATA_FILE


def generate_system_status() -> Dict[str, Any]:
    """Generate system status data."""
    try:
        # Try to get actual model count from models_data.json
        model_count = 0
        stock_agents = 0
        polymarket_agents = 0

        if os.path.exists(MODELS_DATA_FILE):
            with open(MODELS_DATA_FILE, "r") as f:
                models = json.load(f)
                model_count = len(models)
                stock_agents = len([m for m in models if m.get("category") == "stock"])
                polymarket_agents = len(
                    [m for m in models if m.get("category") == "polymarket"]
                )

        # Check for trading status files and last update times
        trading_status = {}

        # Check when models_data.json was last updated (indicates last trading cycle)
        if os.path.exists(MODELS_DATA_FILE):
            last_trading_time = datetime.fromtimestamp(
                os.path.getmtime(MODELS_DATA_FILE)
            )
            next_trading_time = last_trading_time + timedelta(hours=1)

            trading_status = {
                "last_trading_cycle": last_trading_time.isoformat(),
                "next_trading_cycle": next_trading_time.isoformat(),
                "trading_enabled": True,
                "trading_interval_hours": 1,
                "minutes_until_next_trade": max(
                    0, int((next_trading_time - datetime.now()).total_seconds() / 60)
                ),
            }
        else:
            trading_status = {
                "last_trading_cycle": None,
                "next_trading_cycle": None,
                "trading_enabled": False,
                "trading_interval_hours": 1,
                "minutes_until_next_trade": None,
            }

        status = {
            "running": True,
            "total_agents": model_count,
            "stock_agents": stock_agents,
            "polymarket_agents": polymarket_agents,
            "last_updated": datetime.now().isoformat(),
            "uptime": "Active",
            "version": "1.0.0",
            **trading_status,  # Merge trading status
        }

        # Save to JSON file
        with open("system_data.json", "w") as f:
            json.dump(status, f, indent=2)

        return status

    except Exception:
        # Fallback status
        return {
            "running": True,
            "total_agents": 0,
            "stock_agents": 0,
            "polymarket_agents": 0,
            "last_updated": datetime.now().isoformat(),
            "uptime": "Active",
            "version": "1.0.0",
        }


def update_system_status():
    """Update system status and save to JSON file."""
    try:
        status = generate_system_status()
        with open(SYSTEM_DATA_FILE, "w") as f:
            json.dump(status, f, indent=2)
    except Exception:
        pass


