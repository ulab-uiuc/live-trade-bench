#!/usr/bin/env python3
"""
Real Agents + Mock Fetchers Demo

This demo showcases using real AI agents with mock fetchers for fast testing.
- Real LLM agents make actual investment decisions
- Mock fetchers provide instant fake data without external API calls
- Perfect for testing agent logic without network delays or API costs
"""

import time
from typing import Any, Dict

from live_trade_bench.accounts import PolymarketAccount, StockAccount
from live_trade_bench.agents.polymarket_agent import create_polymarket_agent
from live_trade_bench.agents.stock_agent import create_stock_agent

# Use mock fetchers instead of real ones
from live_trade_bench.mock import (
    fetch_current_stock_price,
    fetch_news_data,
    fetch_trending_stocks,
)


def demo_stock_agent_mock_fetchers() -> None:
    """Demo real stock agent with mock fetchers"""
    print("\n🏗️ DEMO 1: Real Stock Agent + Mock Fetchers")
    print("=" * 60)

    # Create real agent and account
    agent = create_stock_agent("MockData_Trader", "gpt-4o-mini")
    account = StockAccount(cash_balance=10000.0)
    agent.account = account

    print(f"✅ Created real agent: {agent.name} (model: {agent.model_name})")
    print(f"✅ Starting cash: ${account.cash_balance:,.2f}")

    # Use mock fetchers to get instant data
    print("\n📊 Fetching market data using mock fetchers...")
    start_time = time.time()

    # Get trending stocks (instant with mocks)
    tickers = fetch_trending_stocks(limit=5)
    print(f"🏃‍♂️ Mock trending stocks: {tickers}")

    # Build market data with mock prices
    market_data: Dict[str, Dict[str, Any]] = {}
    for ticker in tickers:
        price = fetch_current_stock_price(ticker)
        market_data[ticker] = {
            "current_price": price,
            "name": f"Mock {ticker} Corp",
            "sector": (
                "Technology" if ticker in ["AAPL", "MSFT", "NVDA"] else "Financial"
            ),
        }

    # Get mock news data
    news_data = {}
    for ticker in tickers[:3]:  # Just first 3 for demo
        articles = fetch_news_data(
            f"{ticker} stock", "2024-01-01", "2024-12-31", max_pages=1
        )
        news_data[ticker] = articles

    fetch_time = time.time() - start_time
    print(f"⚡ Data fetched in {fetch_time:.3f}s (mock fetchers are instant!)")

    print(f"📈 Market data: {len(market_data)} stocks")
    for ticker, data in list(market_data.items())[:3]:
        print(f"   • {ticker}: ${data['current_price']:.2f} ({data['sector']})")

    print(
        f"📰 News data: {sum(len(articles) for articles in news_data.values())} articles"
    )

    # Let real agent make decision
    print(f"\n🤖 Asking {agent.name} to generate portfolio allocation...")
    llm_start = time.time()

    allocation = agent.generate_portfolio_allocation(
        market_data=market_data, account=account, date="2025-09-05", news_data=news_data
    )

    llm_time = time.time() - llm_start
    print(f"🧠 LLM decision took {llm_time:.3f}s")

    if allocation:
        print(f"✅ Portfolio allocation generated: {allocation}")

        # Simulate applying the allocation
        total_to_invest = account.cash_balance
        print(f"\n💰 Simulating investment of ${total_to_invest:,.2f}")

        for asset, weight in allocation.items():
            amount = total_to_invest * weight
            if asset == "CASH":
                print(f"   💵 CASH: ${amount:,.2f} ({weight:.1%})")
            else:
                shares = amount / market_data[asset]["current_price"]
                print(
                    f"   📊 {asset}: ${amount:,.2f} ({weight:.1%}) = {shares:.2f} shares @ ${market_data[asset]['current_price']:.2f}"
                )
    else:
        print("❌ No allocation generated")

    total_time = time.time() - start_time
    print(f"\n⏱️ Total demo time: {total_time:.3f}s")
    print(f"   📊 Data fetch: {fetch_time:.3f}s ({fetch_time/total_time:.1%})")
    print(f"   🧠 LLM decision: {llm_time:.3f}s ({llm_time/total_time:.1%})")


def demo_polymarket_agent_mock_fetchers() -> None:
    """Demo real polymarket agent with mock fetchers"""
    print("\n🏗️ DEMO 2: Real Polymarket Agent + Mock Fetchers")
    print("=" * 60)

    # Create real agent and account
    agent = create_polymarket_agent("MockData_Predictor", "gpt-4o-mini")
    account = PolymarketAccount(cash_balance=2000.0)
    agent.account = account

    print(f"✅ Created real agent: {agent.name} (model: {agent.model_name})")
    print(f"✅ Starting cash: ${account.cash_balance:,.2f}")

    # Mock polymarket data (since we don't have a polymarket mock fetcher, simulate it)
    print("\n📊 Generating mock prediction market data...")
    start_time = time.time()

    # Simulate prediction market data
    market_data: Dict[str, Dict[str, Any]] = {
        "election_2024": {
            "price": 0.65,
            "question": "Will the Republican candidate win the 2024 US Presidential election?",
            "category": "Politics",
            "yes_price": 0.65,
            "no_price": 0.35,
        },
        "bitcoin_100k": {
            "price": 0.30,
            "question": "Will Bitcoin reach $100,000 by end of 2024?",
            "category": "Crypto",
            "yes_price": 0.30,
            "no_price": 0.70,
        },
        "ai_breakthrough": {
            "price": 0.45,
            "question": "Will there be a major AI breakthrough announcement in 2024?",
            "category": "Technology",
            "yes_price": 0.45,
            "no_price": 0.55,
        },
    }

    # Mock news for prediction markets
    news_data = {
        "election_2024": [
            {
                "title": "Latest polling data shows tight race",
                "snippet": "Recent polls indicate...",
                "source": "PoliticsNews",
            }
        ],
        "bitcoin_100k": [
            {
                "title": "Bitcoin volatility continues",
                "snippet": "Market analysts predict...",
                "source": "CryptoDaily",
            }
        ],
    }

    fetch_time = time.time() - start_time
    print(f"⚡ Data generated in {fetch_time:.3f}s (mock data is instant!)")

    print(f"🔮 Prediction markets: {len(market_data)} markets")
    for market_id, data in market_data.items():
        print(
            f"   • {market_id}: YES {data['yes_price']:.3f} / NO {data['no_price']:.3f}"
        )
        print(f"     Question: {data['question'][:50]}...")

    # Let real agent make decision
    print(f"\n🤖 Asking {agent.name} to generate portfolio allocation...")
    llm_start = time.time()

    allocation = agent.generate_portfolio_allocation(
        market_data=market_data, account=account, date="2025-09-05", news_data=news_data
    )

    llm_time = time.time() - llm_start
    print(f"🧠 LLM decision took {llm_time:.3f}s")

    if allocation:
        print(f"✅ Portfolio allocation generated: {allocation}")

        # Simulate applying the allocation
        total_to_invest = account.cash_balance
        print(f"\n💰 Simulating investment of ${total_to_invest:,.2f}")

        for asset, weight in allocation.items():
            amount = total_to_invest * weight
            if asset == "CASH":
                print(f"   💵 CASH: ${amount:,.2f} ({weight:.1%})")
            else:
                market = market_data.get(asset, {})
                yes_price = market.get("yes_price", 0.5)
                shares = amount / yes_price if yes_price > 0 else 0
                print(
                    f"   🔮 {asset}: ${amount:,.2f} ({weight:.1%}) = {shares:.0f} shares @ {yes_price:.3f}"
                )
    else:
        print("❌ No allocation generated")

    total_time = time.time() - start_time
    print(f"\n⏱️ Total demo time: {total_time:.3f}s")
    print(f"   📊 Data generation: {fetch_time:.3f}s ({fetch_time/total_time:.1%})")
    print(f"   🧠 LLM decision: {llm_time:.3f}s ({llm_time/total_time:.1%})")


def main() -> None:
    """Run both demos"""
    print("🚀 REAL AGENTS + MOCK FETCHERS DEMO")
    print("This demo shows how mock fetchers enable instant testing")
    print("of real AI agents without external API dependencies")
    print("=" * 80)

    try:
        # Demo 1: Stock agent with mock fetchers
        demo_stock_agent_mock_fetchers()

        print("\n" + "=" * 80)

        # Demo 2: Polymarket agent with mock fetchers
        demo_polymarket_agent_mock_fetchers()

        print("\n" + "=" * 80)
        print("🎉 SUMMARY:")
        print("✅ Real agents made actual LLM-powered investment decisions")
        print("✅ Mock fetchers provided instant data without external APIs")
        print("✅ Perfect for rapid testing and development!")
        print("✅ No network delays, API costs, or rate limiting")

    except KeyboardInterrupt:
        print("\n⏹️ Demo stopped by user")
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
