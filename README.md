# Live Trade Bench

A comprehensive trading evaluation and data fetching platform for financial markets analysis.

## Overview

Live Trade Bench provides tools for fetching financial data from multiple sources and evaluating trading strategies across different markets including stocks, options, prediction markets, and social sentiment.

## Features

### Data Fetchers

- **Stock Data**: Historical price data via Yahoo Finance
- **Options Data**: Option chains, Greeks, and implied volatility
- **News Data**: Financial news articles and sentiment
- **Polymarket Data**: Prediction market data and outcomes
- **Reddit Data**: Social sentiment from trading-related subreddits

### Evaluators

- **Polymarket Evaluator**: Prediction market trading strategy evaluation
- **Kelly Criterion**: Optimal bet sizing calculations
- **Market Efficiency Analysis**: Arbitrage opportunity detection

### Web Interface

- **Backend API**: FastAPI-based REST API for data and evaluations
- **Frontend**: React-based dashboard for trading analysis
- **Real-time Data**: Live market data and trading history

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or using poetry
poetry install
```

### Basic Usage

```python
# Fetch stock data
from trading_bench.data_fetchers.stock_fetcher import fetch_stock_data
data = fetch_stock_data("AAPL", period="1mo")

# Evaluate Polymarket trades
from trading_bench.evaluators.polymarket_evaluator import eval_polymarket
actions = [{"market_id": "test", "outcome": "yes", "action": "buy", "price": 0.6, "quantity": 100}]
result = eval_polymarket(actions)
```

### Run Web Interface

```bash
# Start backend
cd backend && python run.py

# Start frontend (in another terminal)
cd frontend && npm start
```

### Examples

Check the `examples/` directory for demonstration scripts:

- `stock_demo.py` - Stock data fetching
- `option_demo.py` - Option chain analysis
- `polymarket_demo.py` - Prediction market evaluation
- `reddit_demo.py` - Social sentiment analysis

## Project Structure

```
live-trade-bench/
├── trading_bench/          # Core library
│   ├── data_fetchers/      # Data source connectors
│   └── evaluators/         # Trading strategy evaluators
├── backend/                # API server
├── frontend/               # Web dashboard
├── examples/               # Demo scripts
└── tests/                  # Test suite
```

## License

MIT License - see LICENSE file for details.
