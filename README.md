![live-trade-bench](assets/live-trade-bench.png)

<h1 align="center">Live Evaluation of Trading Agents</h1>

<div align="center">

[![arXiv](https://img.shields.io/badge/arXiv-PDF-b31b1b.svg)](assets/live_trade_bench_arxiv.pdf)
[![Python 3.10](https://img.shields.io/badge/python-%E2%89%A53.10-blue)](https://www.python.org/downloads/release/python-3109/)
[![GitHub pull request](https://img.shields.io/badge/PRs-welcome-red)](https://github.com/hiyouga/LLaMA-Factory/pulls)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://pre-commit.com/)
[![bear-ified](https://raw.githubusercontent.com/beartype/beartype-assets/main/badge/bear-ified.svg)](https://beartype.readthedocs.io)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</div>

## Overview

Live Trade Bench is a comprehensive platform for evaluating LLM-based trading agents in real-time market environments. Built with FastAPI, it provides a full-stack solution for running, monitoring, and benchmarking AI trading agents across multiple markets while avoiding backtest overfitting.

## 📰 News

**[October 2025]** 🎉 We've released our technical report! Read the full paper: [LiveTradeBench: Seeking Real-world Alpha with Large Language Models](assets/live_trade_bench_arxiv.pdf)

## Features

- **🤖 Multiple LLMs Support**: Run multiple LLM-powered trading agents simultaneously (GPT, Claude, Gemini, etc.)
- **📈 Dual Market Systems**: Stock market (US equities) and Polymarket (prediction markets)
- **🔄 Real-time Updates**: Automated price updates, news feeds, and social sentiment analysis
- **💾 Backtest Data**: Load and analyze past trading performance
- **🔌 RESTful API**: Full API access for external integrations

## Installation

```bash
# Install with pip
pip install live-trade-bench

# Or from source
git clone https://github.com/ulab-uiuc/live-trade-bench.git
cd live-trade-bench
poetry install
```

## Setup

### Set API Keys

```bash
# Required: Set your OpenAI API key
export OPENAI_API_KEY="your-openai-key"

# Optional: Set other LLM provider keys
export ANTHROPIC_API_KEY="your-anthropic-key"
export GOOGLE_API_KEY="your-google-key"
```

## Quick Start

### Minimal Example

```python
from live_trade_bench.systems import StockPortfolioSystem

# Create a trading system
system = StockPortfolioSystem.get_instance()

# Add an LLM agent with $10,000 initial capital
system.add_agent(
    name="GPT-4o-mini Trader",
    initial_cash=10000.0,
    model_name="gpt-4o-mini"
)

# Initialize and run trading cycle
system.initialize_for_live()
system.run_cycle()

# Get agent performance
performance = system.get_all_agent_performance()
print(performance)
```

## Package Structure

```
live_trade_bench/
├── fetchers/                   # Data crawlers and fetchers
│   ├── base_fetcher.py        # Base fetcher interface
│   ├── stock_fetcher.py       # Stock price & info (Yahoo Finance)
│   ├── polymarket_fetcher.py  # Polymarket data (CLOB API)
│   ├── news_fetcher.py        # Financial news (NewsAPI, Finnhub)
│   ├── reddit_fetcher.py      # Reddit sentiment (PRAW)
│   └── constants.py           # Stock symbols and constants
│
├── agents/                     # LLM trading agents
│   ├── base_agent.py          # Base LLM agent class
│   ├── stock_agent.py         # Stock trading agent
│   └── polymarket_agent.py    # Prediction market agent
│
├── accounts/                   # Portfolio & execution
│   ├── base_account.py        # Base account with portfolio tracking
│   ├── stock_account.py       # Stock portfolio management
│   └── polymarket_account.py  # Polymarket portfolio management
│
├── systems/                    # Complete trading systems
│   ├── stock_system.py        # Stock trading system
│   └── polymarket_system.py   # Polymarket trading system
│
├── backtest/                   # Backtesting framework
│   └── backtest_runner.py     # Historical strategy evaluation
│
├── mock/                       # Mock implementations for testing
│   ├── mock_agent.py          # Fake agent with random decisions
│   ├── mock_fetcher.py        # Fake fetcher with synthetic data
│   └── mock_system.py         # Combined mock systems
│
└── utils/                      # Utilities
    ├── llm_client.py          # LLM API wrapper (OpenAI, Anthropic, etc.)
    ├── logger.py              # Logging utilities
    └── agent_utils.py         # Agent helper functions
```


## Core Usage

### Example 1: Stock Trading System

```python
from live_trade_bench.systems import StockPortfolioSystem

# Create stock trading system
system = StockPortfolioSystem()

# Add AI agent
system.add_agent("Portfolio_Manager", initial_cash=10000.0, model_name="gpt-4o-mini")

# Initialize system (fetches trending stocks)
system.initialize_for_live()
print(f"Trading {len(system.universe)} stocks: {system.universe}...")

# Run trading cycles
for i in range(5):
    system.run_cycle()

print("Demo finished.")
```

### Example 2: Polymarket Trading System

```python
from live_trade_bench.systems import PolymarketPortfolioSystem

# Create polymarket system (auto-initializes)
system = PolymarketPortfolioSystem()

# Add AI agent for predictions
system.add_agent("Predictor", initial_cash=2000.0, model_name="gpt-4o-mini")

print(f"Trading {len(system.universe)} prediction markets")

# Run prediction cycles
for i in range(5):
    system.run_cycle()

print("Demo finished.")
```

### Example 3: Using Data Fetchers

```python
from datetime import datetime, timedelta
from live_trade_bench.fetchers.stock_fetcher import (
    fetch_trending_stocks,
    fetch_stock_price_with_history,
)
from live_trade_bench.fetchers.news_fetcher import fetch_news_data

# Fetch trending stocks
trending = fetch_trending_stocks(limit=10)
print(f"Trending stocks: {trending}")

# Fetch stock price data
stock_data = fetch_stock_price_with_history("AAPL")
print(stock_data)

# Fetch financial news
today = datetime.now().strftime("%Y-%m-%d")
start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
news = fetch_news_data(query="stock market", start_date=start_date, end_date=today)
for article in news[:5]:
    print(f"- {article['title']}")
```

For more examples, see the `examples/` directory.

### Mock Modes for Testing

```python
from live_trade_bench.mock import (
    MockAgentStockSystem,
    MockFetcherStockSystem,
    MockAgentFetcherStockSystem
)

# Option 1: Mock agents only (no LLM API calls)
system = MockAgentStockSystem.get_instance()

# Option 2: Mock fetchers only (no real market data)
system = MockFetcherStockSystem.get_instance()

# Option 3: Mock both (fastest for testing)
system = MockAgentFetcherStockSystem.get_instance()
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.


## License

This project is licensed under the PolyForm Noncommercial License 1.0.0 - see the [LICENSE](LICENSE) file for details.

For commercial licensing, please see [LICENSE.COMMERCIAL](LICENSE.COMMERCIAL).
