"""
System status data provider
"""

import json
import os
from datetime import datetime
from typing import Any, Dict


def get_system_status() -> Dict[str, Any]:
    """Get system status from JSON file or generate default status."""
    try:
        if os.path.exists("system_data.json"):
            with open("system_data.json", "r") as f:
                return json.load(f)
        else:
            # Generate default system status
            return generate_system_status()
    except Exception:
        return generate_system_status()


def generate_system_status() -> Dict[str, Any]:
    """Generate system status data."""
    try:
        # Try to get actual model count from models_data.json
        model_count = 0
        stock_agents = 0
        polymarket_agents = 0

        if os.path.exists("models_data.json"):
            with open("models_data.json", "r") as f:
                models = json.load(f)
                model_count = len(models)
                stock_agents = len([m for m in models if m.get("category") == "stock"])
                polymarket_agents = len(
                    [m for m in models if m.get("category") == "polymarket"]
                )

        status = {
            "running": True,
            "total_agents": model_count,
            "stock_agents": stock_agents,
            "polymarket_agents": polymarket_agents,
            "last_updated": datetime.now().isoformat(),
            "uptime": "Active",
            "version": "1.0.0",
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
        with open("system_data.json", "w") as f:
            json.dump(status, f, indent=2)
    except Exception:
        pass
