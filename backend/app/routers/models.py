import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

import yfinance as yf
from fastapi import APIRouter

from ..config import MODELS_DATA_FILE
from .router_utils import read_json_or_404

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/models", response_model=List[Dict[str, Any]], include_in_schema=False)
@router.get("/models/", response_model=List[Dict[str, Any]])
def get_models():
    return read_json_or_404(MODELS_DATA_FILE)


@router.get("/indices", response_model=List[Dict[str, Any]])
def get_indices():
    """Get QQQ and VOO index data with return rates calculated from earliest allocation history."""
    try:
        # Read models data to get the earliest allocation history date
        models_data = read_json_or_404(MODELS_DATA_FILE)

        # Find the earliest date from allocation history across all stock models
        earliest_date = None
        for model in models_data:
            if model.get("category") == "stock" and "allocationHistory" in model:
                for allocation in model["allocationHistory"]:
                    if "timestamp" in allocation:
                        allocation_date = datetime.fromisoformat(
                            allocation["timestamp"].replace("Z", "+00:00")
                        )
                        if earliest_date is None or allocation_date < earliest_date:
                            earliest_date = allocation_date

        if earliest_date is None:
            # Fallback to 30 days ago if no allocation history found
            earliest_date = datetime.now() - timedelta(days=30)

        # Format date for yfinance
        start_date = earliest_date.strftime("%Y-%m-%d")

        indices = []
        for symbol in ["QQQ", "VOO"]:
            try:
                # Get current price
                ticker = yf.Ticker(symbol)
                current_price = ticker.history(period="1d")["Close"].iloc[-1]

                # Get historical price on the earliest date
                historical_data = ticker.history(
                    start=start_date,
                    end=(earliest_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                )
                if not historical_data.empty:
                    historical_price = historical_data["Close"].iloc[0]
                    return_rate = (
                        (current_price - historical_price) / historical_price
                    ) * 100
                else:
                    # If no historical data, try to get data from 30 days ago
                    fallback_date = (datetime.now() - timedelta(days=30)).strftime(
                        "%Y-%m-%d"
                    )
                    fallback_data = ticker.history(
                        start=fallback_date,
                        end=(datetime.now() - timedelta(days=29)).strftime("%Y-%m-%d"),
                    )
                    if not fallback_data.empty:
                        historical_price = fallback_data["Close"].iloc[0]
                        return_rate = (
                            (current_price - historical_price) / historical_price
                        ) * 100
                    else:
                        return_rate = 0.0
                        historical_price = current_price

                indices.append(
                    {
                        "id": f"{symbol.lower()}-index",
                        "name": symbol,
                        "category": "stock",
                        "status": "active",
                        "performance": return_rate,
                        "profit": return_rate,  # For display consistency
                        "trades": 0,  # Indices don't have trades
                        "asset_allocation": {},
                        "portfolio": {
                            "cash": 0,
                            "total_value": 1000,  # Base value for display
                            "positions": {},
                        },
                        "profitHistory": [],
                        "allocationHistory": [],
                        "is_index": True,  # Flag to identify as index
                        "current_price": float(current_price),
                        "historical_price": float(historical_price),
                        "return_rate": float(return_rate),
                    }
                )

            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
                # Add a fallback entry with zero return
                indices.append(
                    {
                        "id": f"{symbol.lower()}-index",
                        "name": symbol,
                        "category": "stock",
                        "status": "active",
                        "performance": 0.0,
                        "profit": 0.0,
                        "trades": 0,
                        "asset_allocation": {},
                        "portfolio": {"cash": 0, "total_value": 1000, "positions": {}},
                        "profitHistory": [],
                        "allocationHistory": [],
                        "is_index": True,
                        "current_price": 0.0,
                        "historical_price": 0.0,
                        "return_rate": 0.0,
                    }
                )

        return indices

    except Exception as e:
        logger.error(f"Error fetching indices data: {e}")
        return []
