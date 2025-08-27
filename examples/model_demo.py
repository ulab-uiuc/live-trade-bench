#!/usr/bin/env python3
"""
Demo script for testing the models visualization frontend.
This creates a mock FastAPI server with sample model data including chart data.

Usage:
    python examples/demo.py

Then start the frontend:
    cd frontend && npm start

The frontend will show mock models with realistic chart data for testing visualizations.
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Live Trade Bench Demo", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mock data generators
def generate_profit_history(
    days: int = 30, volatility: float = 0.1
) -> List[Dict[str, Any]]:
    """Generate realistic profit history data."""
    history = []
    base_date = datetime.now() - timedelta(days=days)
    cumulative_profit = 0
    total_value = 1000  # Starting value

    for i in range(days):
        # Simulate daily profit/loss with some randomness
        daily_change = random.gauss(0, volatility * total_value)
        cumulative_profit += daily_change
        total_value = 1000 + cumulative_profit

        timestamp = (base_date + timedelta(days=i)).isoformat()
        history.append(
            {
                "timestamp": timestamp,
                "profit": cumulative_profit,
                "totalValue": total_value,
            }
        )

    return history


def generate_holdings() -> Dict[str, int]:
    """Generate random stock holdings."""
    stocks = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "META", "AMZN"]
    holdings = {}

    # Randomly select 2-4 stocks to hold
    num_holdings = random.randint(2, 4)
    selected_stocks = random.sample(stocks, num_holdings)

    for stock in selected_stocks:
        holdings[stock] = random.randint(1, 50)

    return holdings


def generate_portfolio_history(holdings: Dict[str, int]) -> List[Dict[str, Any]]:
    """Generate portfolio composition history for area chart."""
    history = []
    base_date = datetime.now() - timedelta(days=20)

    # Start with some initial holdings
    current_holdings = {
        stock: max(1, shares // 2) for stock, shares in holdings.items()
    }
    current_cash = 500

    for i in range(20):
        # Simulate price changes
        prices = {stock: random.uniform(80, 200) for stock in current_holdings.keys()}

        # Sometimes add or remove holdings
        if random.random() < 0.3 and len(current_holdings) < 5:
            new_stock = random.choice(["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"])
            if new_stock not in current_holdings:
                current_holdings[new_stock] = random.randint(1, 10)
                prices[new_stock] = random.uniform(80, 200)

        # Calculate total value
        total_value = current_cash + sum(
            current_holdings.get(stock, 0) * prices.get(stock, 100)
            for stock in current_holdings.keys()
        )

        timestamp = (base_date + timedelta(days=i)).isoformat()
        history.append(
            {
                "timestamp": timestamp,
                "holdings": current_holdings.copy(),
                "prices": prices.copy(),
                "cash": current_cash,
                "totalValue": total_value,
            }
        )

        # Gradually evolve holdings toward final state
        if i > 10:
            for stock in holdings:
                if stock not in current_holdings:
                    current_holdings[stock] = 1
                else:
                    target = holdings[stock]
                    current_holdings[stock] = min(
                        target, current_holdings[stock] + random.randint(0, 2)
                    )

    return history


# Sample model data
MOCK_MODELS = [
    {
        "id": "Test_Model_0",
        "name": "Test Model 0",
        "category": "stock",
        "performance": 15.7,
        "accuracy": 68.5,
        "trades": 45,
        "profit": 157.23,
        "status": "active",
        "total_value": 1157.23,
        "cash_balance": 234.56,
        "active_positions": 3,
        "is_activated": True,
        "recent_performance": {
            "daily_actions": 2,
            "weekly_actions": 8,
            "recent_win_rate": 72.0,
            "last_action_time": "2024-01-15T14:30:00Z",
        },
        "llm_available": True,
        "strategy": "momentum_growth",
    },
    {
        "id": "Test_Model_1",
        "name": "Test Model 1",
        "category": "stock",
        "performance": 8.3,
        "accuracy": 75.2,
        "trades": 28,
        "profit": 83.45,
        "status": "active",
        "total_value": 1083.45,
        "cash_balance": 456.78,
        "active_positions": 2,
        "is_activated": True,
        "recent_performance": {
            "daily_actions": 1,
            "weekly_actions": 4,
            "recent_win_rate": 78.0,
            "last_action_time": "2024-01-15T10:15:00Z",
        },
        "llm_available": True,
        "strategy": "value_investing",
    },
    {
        "id": "Test_Model_2",
        "name": "Test Model 2",
        "category": "stock",
        "performance": -2.1,
        "accuracy": 58.9,
        "trades": 52,
        "profit": -21.33,
        "status": "active",
        "total_value": 978.67,
        "cash_balance": 123.45,
        "active_positions": 4,
        "is_activated": True,
        "recent_performance": {
            "daily_actions": 3,
            "weekly_actions": 12,
            "recent_win_rate": 55.0,
            "last_action_time": "2024-01-15T16:45:00Z",
        },
        "llm_available": True,
        "strategy": "balanced_growth",
    },
    {
        "id": "Test_Model_3",
        "name": "Test Model 3",
        "category": "polymarket",
        "performance": 12.8,
        "accuracy": 71.4,
        "trades": 34,
        "profit": 64.20,
        "status": "active",
        "total_value": 564.20,
        "cash_balance": 187.65,
        "active_positions": 5,
        "is_activated": True,
        "recent_performance": {
            "daily_actions": 2,
            "weekly_actions": 7,
            "recent_win_rate": 74.0,
            "last_action_time": "2024-01-15T12:20:00Z",
        },
        "llm_available": True,
        "market_type": "prediction_markets",
        "strategy": "sentiment_momentum",
    },
]

# Generate chart data for each model
for model in MOCK_MODELS:
    model["holdings"] = generate_holdings() if model["active_positions"] > 0 else {}
    model["profit_history"] = generate_profit_history(
        30, 0.05 if "conservative" in model["name"].lower() else 0.1
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Live Trade Bench Demo API", "status": "running"}


@app.get("/api/models/")
async def get_models():
    """Get all mock trading models."""
    return MOCK_MODELS


@app.get("/api/models/{model_id}")
async def get_model(model_id: str):
    """Get a specific model by ID."""
    model = next((m for m in MOCK_MODELS if m["id"] == model_id), None)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@app.get("/api/models/{model_id}/chart-data")
async def get_model_chart_data(model_id: str):
    """Get chart data for a specific model."""
    model = next((m for m in MOCK_MODELS if m["id"] == model_id), None)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return {
        "holdings": model["holdings"],
        "profit_history": model["profit_history"],
        "total_value": model["total_value"],
    }


@app.get("/api/models/{model_id}/portfolio")
async def get_model_portfolio(model_id: str):
    """Get portfolio data for a specific model."""
    model = next((m for m in MOCK_MODELS if m["id"] == model_id), None)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # Generate detailed portfolio data
    holdings = model["holdings"]
    positions = {}

    for ticker, quantity in holdings.items():
        current_price = random.uniform(80, 200)
        avg_price = current_price * random.uniform(0.8, 1.2)
        current_value = quantity * current_price
        cost_basis = quantity * avg_price
        unrealized_pnl = current_value - cost_basis

        positions[ticker] = {
            "current_price": current_price,
            "current_value": current_value,
            "avg_price": avg_price,
            "cost_basis": cost_basis,
            "unrealized_pnl": unrealized_pnl,
            "quantity": quantity,
        }

    return {
        "model_id": model_id,
        "model_name": model["name"],
        "cash": model["cash_balance"],
        "holdings": holdings,
        "total_value": model["total_value"],
        "return_pct": model["performance"],
        "unrealized_pnl": sum(pos["unrealized_pnl"] for pos in positions.values()),
        "positions": positions,
        "market_data_available": True,
        "last_updated": datetime.now().isoformat(),
        "portfolio_history": generate_portfolio_history(holdings),
    }


@app.get("/api/models/system-status")
async def get_system_status():
    """Get system status."""
    return {
        "system_running": True,
        "cycle_interval_minutes": 30,
        "total_agents": len(MOCK_MODELS),
        "active_agents": len([m for m in MOCK_MODELS if m["status"] == "active"]),
        "tickers": ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "META", "AMZN"],
        "initial_cash": 1000,
        "last_cycle_time": (datetime.now() - timedelta(minutes=15)).isoformat(),
        "next_cycle_time": (datetime.now() + timedelta(minutes=15)).isoformat(),
        "market_status": "open",
    }


@app.get("/api/system-status")
async def get_system_status_alt():
    """Get system status."""
    return {
        "system_running": True,
        "cycle_interval_minutes": 30,
        "total_agents": len(MOCK_MODELS),
        "active_agents": len([m for m in MOCK_MODELS if m["status"] == "active"]),
        "tickers": ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "META", "AMZN"],
        "initial_cash": 1000,
        "last_cycle_time": (datetime.now() - timedelta(minutes=15)).isoformat(),
        "next_cycle_time": (datetime.now() + timedelta(minutes=15)).isoformat(),
        "market_status": "open",
    }


# Health check endpoints for other pages (return empty data to avoid errors)
@app.get("/api/news/")
async def get_news():
    """Return empty news data."""
    return []


@app.get("/api/social/")
async def get_social():
    """Return empty social data."""
    return []


@app.get("/api/system-logs/")
async def get_system_logs():
    """Return empty system logs."""
    return []


@app.get("/api/trades/")
async def get_trades():
    """Return empty trades data."""
    return []


if __name__ == "__main__":
    print("🚀 Starting Live Trade Bench Demo Server...")
    print("📊 Mock models with chart data will be available at:")
    print("   - Models API: http://localhost:5000/api/models/")
    print("   - Chart Data: http://localhost:5000/api/models/{model_id}/chart-data")
    print("   - Portfolio: http://localhost:5000/api/models/{model_id}/portfolio")
    print()
    print("🎯 To test the frontend:")
    print("   1. Keep this demo running")
    print("   2. In another terminal: cd frontend && npm start")
    print("   3. Open http://localhost:3000 and check the Models section")
    print()
    print("✨ Demo includes:")
    print("   - 5 mock trading models (4 active, 1 inactive)")
    print("   - Realistic profit/loss history")
    print("   - Stock holdings for pie charts")
    print("   - Portfolio composition history for area charts")
    print("   - Both stock and polymarket model types")
    print()

    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
