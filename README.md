![live-trade-bench](assets/live-trade-bench.png)

<h1 align="center">Live Evaluation of Trading Agents</h1>

<div align="center">

[![Python 3.10](https://img.shields.io/badge/python-%E2%89%A53.10-blue)](https://www.python.org/downloads/release/python-3109/)
[![GitHub pull request](https://img.shields.io/badge/PRs-welcome-red)](https://github.com/hiyouga/LLaMA-Factory/pulls)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://pre-commit.com/)
[![bear-ified](https://raw.githubusercontent.com/beartype/beartype-assets/main/badge/bear-ified.svg)](https://beartype.readthedocs.io)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</div>

## Overview

Trading agent evaluation in the live environment. We target at avoiding overfitting on back test and build an arena for LLM-based trading agents.

## Features

- **AI Agents**: GPT-4 powered trading decisions
- **Multi-Asset**: Stocks and prediction markets
- **Real-time Data**: Live market feeds
- **Portfolio Management**: Automated tracking and execution

## Quick Start

```bash
# Install
poetry install

# Stock trading
from live_trade_bench import LLMStockAgent, create_stock_account
agent = LLMStockAgent("Trader")
account = create_stock_account(10000.0)

# Prediction markets
from live_trade_bench import LLMPolyMarketAgent, fetch_trending_markets
agent = LLMPolyMarketAgent("Predictor")
markets = fetch_trending_markets(5)
```

## Structure

```
live_trade_bench/
├── agents/                     # AI trading agents
│   ├── base_agent.py          # Base LLM agent class
│   ├── stock_agent.py         # Stock trading agent
│   ├── polymarket_agent.py    # Prediction market agent
│   ├── stock_system.py        # Stock trading system
│   └── polymarket_system.py   # Polymarket trading system
├── accounts/                   # Portfolio management
│   ├── base_account.py        # Base account class
│   ├── stock_account.py       # Stock portfolio & execution
│   ├── polymarket_account.py  # Prediction market portfolio
│   ├── action.py              # Trading action definitions
│   └── utils.py               # Account utilities
├── fetchers/                   # Real-time data sources
│   ├── base_fetcher.py        # Base fetcher class
│   ├── stock_fetcher.py       # Yahoo Finance integration
│   ├── polymarket_fetcher.py  # Polymarket API
│   ├── news_fetcher.py        # Financial news
│   ├── option_fetcher.py      # Options data
│   └── reddit_fetcher.py      # Social sentiment
└── utils/                      # LLM & utilities
    ├── llm_client.py          # LLM integration
    └── logger.py              # Logging utilities
```

## Examples

See `examples/` directory for demo scripts.

## License

MIT
