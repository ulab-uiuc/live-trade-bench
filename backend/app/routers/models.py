import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

import yfinance as yf
from fastapi import APIRouter

from ..config import MODELS_DATA_FILE
from .router_utils import read_json_or_404

logger = logging.getLogger(__name__)

router = APIRouter()

# Stock symbols from the fetcher
STOCK_SYMBOLS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "JPM",
    "V",
    "JNJ",
    "UNH",
    "PG",
    "KO",
    "XOM",
    "CAT",
    "WMT",
    "META",
    "TSLA",
    "AMZN",
]


def update_models_with_latest_prices(
    models_data: List[Dict[str, Any]], price_data: Any
) -> None:
    """Update models data with latest stock prices and recalculate profit/performance."""
    try:
        # Extract current prices from yfinance data
        current_prices = {}
        for symbol in STOCK_SYMBOLS:
            if symbol in price_data.columns.get_level_values(1):
                try:
                    current_prices[symbol] = float(price_data["Close"][symbol].iloc[-1])
                except (IndexError, KeyError, ValueError):
                    logger.warning(f"Could not get current price for {symbol}")
                    continue

        # Update each stock model
        for model in models_data:
            if model.get("category") == "stock":
                portfolio = model.get("portfolio", {})
                positions = portfolio.get("positions", {})
                cash = portfolio.get("cash", 0)

                # Calculate total value with latest prices
                total_value = cash
                for symbol, position in positions.items():
                    if symbol in current_prices:
                        quantity = position.get("quantity", 0)
                        current_price = current_prices[symbol]
                        total_value += quantity * current_price

                        # Update current_price in position
                        position["current_price"] = current_price

                # Recalculate profit and performance
                initial_cash = 1000.0  # All accounts start with $1000
                profit = total_value - initial_cash
                performance = (profit / initial_cash) * 100

                # Update model data
                model["profit"] = profit
                model["performance"] = performance
                model["portfolio"]["total_value"] = total_value

        # Save updated data back to file
        with open(MODELS_DATA_FILE, "w") as f:
            json.dump(models_data, f, indent=4)

        logger.info("Successfully updated models data with latest prices")

    except Exception as e:
        logger.error(f"Error updating models with latest prices: {e}")


@router.get("/models", response_model=List[Dict[str, Any]], include_in_schema=False)
@router.get("/models/", response_model=List[Dict[str, Any]])
def get_models():
    return read_json_or_404(MODELS_DATA_FILE)


@router.get("/indices", response_model=List[Dict[str, Any]])
def get_indices():
    """Get QQQ and VOO index data with return rates calculated from earliest allocation history.
    Also updates all stock models with latest prices and recalculates profit/performance.
    """
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

        # Get all required symbols (indices + stocks)
        all_symbols = ["QQQ", "VOO"] + STOCK_SYMBOLS

        # Batch download all prices
        logger.info(f"Fetching prices for {len(all_symbols)} symbols...")
        price_data = yf.download(" ".join(all_symbols), period="1d", progress=False)

        # Update models with latest stock prices
        update_models_with_latest_prices(models_data, price_data)

        indices = []
        for symbol in ["QQQ", "VOO"]:
            try:
                # Get current price from already downloaded data
                if symbol in price_data.columns.get_level_values(1):
                    current_price = float(price_data["Close"][symbol].iloc[-1])
                else:
                    # Fallback to individual ticker if not in batch data
                    ticker = yf.Ticker(symbol)
                    current_price = ticker.history(period="1d")["Close"].iloc[-1]

                # Get historical price on the earliest date
                ticker = yf.Ticker(symbol)
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
