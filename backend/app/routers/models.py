import logging
from typing import Any, Dict, List

from app.models_data import (
    get_system_status, trigger_cycle
)
from fastapi import APIRouter, HTTPException
import os
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/models", tags=["models"])

STOCK_STATE_FILE = "stock_system_state.pkl"
POLY_STATE_FILE = "polymarket_system_state.pkl"

def _extract_model_data(agent, category):
    """Helper to extract frontend-compatible data from an agent object."""
    account = agent.account
    portfolio_breakdown = account.get_portfolio_value_breakdown()
    initial_cash = account.initial_cash

    total_value = portfolio_breakdown.get("total_value", initial_cash)
    return_pct = ((total_value - initial_cash) / initial_cash) * 100 if initial_cash > 0 else 0.0
    profit_amount = total_value - initial_cash

    return {
        "id": f"{agent.name.lower().replace(' ', '-')}_{category}",
        "name": agent.name,
        "category": category,
        "performance": round(return_pct, 2),
        "profit": round(profit_amount, 2),
        "trades": len(account.transactions),
        "status": "active",
        "asset_allocation": portfolio_breakdown.get("current_allocations", {}),
        "portfolio": account.get_portfolio_value_breakdown(),
        "chartData": { 'profit_history': account.allocation_history },
        "allocationHistory": account.allocation_history
    }

@router.get("/")
async def get_models() -> List[Dict[str, Any]]:
    """Get models data from the JSON file written by background task."""
    try:
        if not os.path.exists("models_data.json"):
            raise HTTPException(status_code=404, detail="Model data not ready yet. Please wait for background task.")
        
        with open("models_data.json", "r") as f:
            models = json.load(f)
        
        print(f"[DEBUG] Loaded {len(models)} models from JSON file")
        
        return models
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error reading model data file.")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Model data file not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching models: {str(e)}")


@router.post("/trigger-cycle")
async def trigger_trading_cycle() -> Dict[str, Any]:
    """Manually trigger a trading cycle for all models."""
    try:
        result = trigger_cycle()
        if result["status"] == "success":
            return {
                "success": True,
                "message": result["message"],
                "timestamp": None,
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error running trading cycle: {str(e)}"
        )


@router.get("/system-status")
async def system_status() -> Dict[str, Any]:
    """Get multi-asset trading system status and configuration."""
    try:
        status = get_system_status()
        return {
            "running": status["running"],
            "total_agents": status["total_agents"],
            "stock_agents": status["stock_agents"],
            "polymarket_agents": status["polymarket_agents"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting system status: {str(e)}"
        )
