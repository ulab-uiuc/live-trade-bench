#!/usr/bin/env python3
"""
Real Fetchers + Mock Agents Demo

This demo showcases using real fetchers with mock agents for data pipeline testing.
- Real fetchers get actual market data from external APIs
- Mock agents make instant deterministic decisions without LLM calls
- Perfect for testing data pipelines without LLM costs or unpredictable responses
"""

import time
from typing import Any, Dict

from live_trade_bench.accounts import PolymarketAccount, StockAccount
from live_trade_bench.fetchers.news_fetcher import fetch_news_data
from live_trade_bench.fetchers.reddit_fetcher import fetch_reddit_sentiment_data

# Use real fetchers - import directly from specific modules like real agents do
from live_trade_bench.fetchers.stock_fetcher import (
    fetch_current_stock_price,
    fetch_trending_stocks,
)

# Use mock agents
from live_trade_bench.mock import create_mock_polymarket_agent, create_mock_stock_agent


def demo_real_fetchers_mock_stock_agent() -> None:
    """Demo real stock fetchers with mock stock agent"""
    print("\n🏗️ DEMO 1: Real Stock Fetchers + Mock Stock Agent")
    print("=" * 60)

    # Create mock agent and account
    agent = create_mock_stock_agent("RealData_MockTrader")
    account = StockAccount(cash_balance=10000.0)
    agent.account = account

    print(f"✅ Created mock agent: {agent.name} (model: {agent.model_name})")
    print(f"✅ Starting cash: ${account.cash_balance:,.2f}")

    # Use real fetchers to get actual market data
    print("\n📊 Fetching REAL market data from external APIs...")
    start_time = time.time()

    try:
        # Get real trending stocks
        print("🌐 Fetching trending stocks...")
        tickers = fetch_trending_stocks(limit=5)
        print(f"📈 Real trending stocks: {tickers}")

        # Build market data with real prices
        market_data: Dict[str, Dict[str, Any]] = {}
        for ticker in tickers:
            print(f"🌐 Fetching price for {ticker}...")
            price = fetch_current_stock_price(ticker)
            if price:
                market_data[ticker] = {
                    "current_price": price,
                    "name": f"{ticker} Corp",
                    "sector": (
                        "Technology"
                        if ticker in ["AAPL", "MSFT", "NVDA", "META", "TSLA"]
                        else "Financial"
                    ),
                }
            else:
                print(f"⚠️ Could not fetch price for {ticker}")

        # Get real news data (limit to avoid long fetch times)
        print("🌐 Fetching recent news...")
        news_data = {}
        for ticker in list(tickers)[:2]:  # Just first 2 to keep demo fast
            print(f"🌐 Fetching news for {ticker}...")
            try:
                articles = fetch_news_data(
                    f"{ticker} stock", "2024-09-01", "2024-09-08", max_pages=1
                )
                news_data[ticker] = articles[:3]  # Limit to 3 articles
                print(f"📰 Found {len(articles)} articles for {ticker}")
            except Exception as e:
                print(f"⚠️ Could not fetch news for {ticker}: {e}")
                news_data[ticker] = []

        # Try to get Reddit sentiment (optional, may fail)
        print("🌐 Fetching Reddit sentiment (optional)...")
        try:
            reddit_data = fetch_reddit_sentiment_data(
                "company_news", "2024-09-08", max_limit=5
            )
            print(f"📱 Found {len(reddit_data)} Reddit posts")
        except Exception as e:
            print(f"⚠️ Reddit data unavailable: {e}")
            reddit_data = []

        fetch_time = time.time() - start_time
        print(f"🌐 Real data fetched in {fetch_time:.3f}s (real APIs take time)")

        if not market_data:
            print("❌ No market data available, skipping agent demo")
            return

        print(f"📈 Market data: {len(market_data)} stocks")
        for ticker, data in list(market_data.items())[:3]:
            print(f"   • {ticker}: ${data['current_price']:.2f} ({data['sector']})")

        print(
            f"📰 News data: {sum(len(articles) for articles in news_data.values())} articles"
        )

        # Let mock agent make instant decision
        print(f"\n🤖 Asking {agent.name} to generate portfolio allocation...")
        agent_start = time.time()

        allocation = agent.generate_portfolio_allocation(
            market_data=market_data,
            account=account,
            date="2024-09-08",
            news_data=news_data,
        )

        agent_time = time.time() - agent_start
        print(f"⚡ Mock agent decision took {agent_time:.3f}s (no LLM calls!)")

        if allocation:
            print(f"✅ Portfolio allocation generated: {allocation}")

            # Simulate applying the allocation
            total_to_invest = account.cash_balance
            print(f"\n💰 Simulating investment of ${total_to_invest:,.2f}")

            for asset, weight in allocation.items():
                amount = total_to_invest * weight
                if asset == "CASH":
                    print(f"   💵 CASH: ${amount:,.2f} ({weight:.1%})")
                elif asset in market_data:
                    price = market_data[asset]["current_price"]
                    shares = amount / price
                    print(
                        f"   📊 {asset}: ${amount:,.2f} ({weight:.1%}) = {shares:.2f} shares @ ${price:.2f}"
                    )
        else:
            print("❌ No allocation generated")

        total_time = time.time() - start_time
        print(f"\n⏱️ Total demo time: {total_time:.3f}s")
        print(f"   🌐 Data fetch: {fetch_time:.3f}s ({fetch_time/total_time:.1%})")
        print(f"   ⚡ Agent decision: {agent_time:.3f}s ({agent_time/total_time:.1%})")

    except Exception as e:
        print(f"❌ Real fetcher error: {e}")
        print("This is expected if you don't have API keys or network access")


def demo_real_news_mock_polymarket_agent() -> None:
    """Demo real news fetcher with mock polymarket agent"""
    print("\n🏗️ DEMO 2: Real News Fetcher + Mock Polymarket Agent")
    print("=" * 60)

    # Create mock agent and account
    agent = create_mock_polymarket_agent("RealNews_MockPredictor")
    account = PolymarketAccount(cash_balance=2000.0)
    agent.account = account

    print(f"✅ Created mock agent: {agent.name} (model: {agent.model_name})")
    print(f"✅ Starting cash: ${account.cash_balance:,.2f}")

    print("\n📊 Creating mock prediction markets with REAL news data...")
    start_time = time.time()

    # Create mock prediction markets
    market_data: Dict[str, Dict[str, Any]] = {
        "election_2024": {
            "price": 0.55,
            "question": "Will the Republican candidate win the 2024 US Presidential election?",
            "category": "Politics",
            "yes_price": 0.55,
            "no_price": 0.45,
        },
        "bitcoin_100k": {
            "price": 0.25,
            "question": "Will Bitcoin reach $100,000 by end of 2024?",
            "category": "Crypto",
            "yes_price": 0.25,
            "no_price": 0.75,
        },
        "ai_stocks": {
            "price": 0.70,
            "question": "Will AI stocks outperform S&P 500 in 2024?",
            "category": "Technology",
            "yes_price": 0.70,
            "no_price": 0.30,
        },
    }

    # Fetch REAL news for each market topic
    print("🌐 Fetching REAL news data for market analysis...")
    news_data = {}

    try:
        # Fetch election news
        print("🌐 Fetching 2024 election news...")
        election_news = fetch_news_data(
            "2024 presidential election", "2024-08-01", "2024-09-08", max_pages=1
        )
        news_data["election_2024"] = election_news[:3]
        print(f"📰 Found {len(election_news)} election articles")

        # Fetch Bitcoin news
        print("🌐 Fetching Bitcoin news...")
        bitcoin_news = fetch_news_data(
            "Bitcoin price 100000", "2024-08-01", "2024-09-08", max_pages=1
        )
        news_data["bitcoin_100k"] = bitcoin_news[:3]
        print(f"📰 Found {len(bitcoin_news)} Bitcoin articles")

        # Fetch AI stocks news
        print("🌐 Fetching AI stocks news...")
        ai_news = fetch_news_data(
            "AI stocks artificial intelligence", "2024-08-01", "2024-09-08", max_pages=1
        )
        news_data["ai_stocks"] = ai_news[:3]
        print(f"📰 Found {len(ai_news)} AI stocks articles")

    except Exception as e:
        print(f"⚠️ Real news fetch error: {e}")
        print("Using minimal mock news data...")
        news_data = {
            "election_2024": [
                {
                    "title": "Election update",
                    "snippet": "Latest polling data...",
                    "source": "NewsAPI",
                }
            ],
            "bitcoin_100k": [
                {
                    "title": "Bitcoin analysis",
                    "snippet": "Crypto market trends...",
                    "source": "NewsAPI",
                }
            ],
            "ai_stocks": [
                {
                    "title": "AI market update",
                    "snippet": "Technology sector performance...",
                    "source": "NewsAPI",
                }
            ],
        }

    fetch_time = time.time() - start_time
    print(f"🌐 Real news data fetched in {fetch_time:.3f}s")

    print(f"🔮 Prediction markets: {len(market_data)} markets")
    for market_id, data in market_data.items():
        print(
            f"   • {market_id}: YES {data['yes_price']:.3f} / NO {data['no_price']:.3f}"
        )
        print(f"     Question: {data['question'][:60]}...")

    total_articles = sum(len(articles) for articles in news_data.values())
    print(f"📰 Real news articles: {total_articles} total")

    # Show sample of real news
    if news_data.get("election_2024"):
        sample_article = news_data["election_2024"][0]
        print(
            f"📰 Sample election article: '{sample_article.get('title', 'No title')[:50]}...'"
        )

    # Let mock agent make instant decision
    print(f"\n🤖 Asking {agent.name} to generate portfolio allocation...")
    agent_start = time.time()

    allocation = agent.generate_portfolio_allocation(
        market_data=market_data, account=account, date="2024-09-08", news_data=news_data
    )

    agent_time = time.time() - agent_start
    print(f"⚡ Mock agent decision took {agent_time:.3f}s (no LLM calls!)")

    if allocation:
        print(f"✅ Portfolio allocation generated: {allocation}")

        # Simulate applying the allocation
        total_to_invest = account.cash_balance
        print(f"\n💰 Simulating investment of ${total_to_invest:,.2f}")

        for asset, weight in allocation.items():
            amount = total_to_invest * weight
            if asset == "CASH":
                print(f"   💵 CASH: ${amount:,.2f} ({weight:.1%})")
            elif asset in market_data:
                yes_price = market_data[asset]["yes_price"]
                shares = amount / yes_price if yes_price > 0 else 0
                print(
                    f"   🔮 {asset}: ${amount:,.2f} ({weight:.1%}) = {shares:.0f} shares @ {yes_price:.3f}"
                )
    else:
        print("❌ No allocation generated")

    total_time = time.time() - start_time
    print(f"\n⏱️ Total demo time: {total_time:.3f}s")
    print(f"   🌐 News fetch: {fetch_time:.3f}s ({fetch_time/total_time:.1%})")
    print(f"   ⚡ Agent decision: {agent_time:.3f}s ({agent_time/total_time:.1%})")


def main() -> None:
    """Run both demos"""
    print("🚀 REAL FETCHERS + MOCK AGENTS DEMO")
    print("This demo shows how mock agents enable fast testing")
    print("of real data pipelines without LLM costs or variability")
    print("=" * 80)

    try:
        # Demo 1: Real stock fetchers with mock agent
        demo_real_fetchers_mock_stock_agent()

        print("\n" + "=" * 80)

        # Demo 2: Real news fetcher with mock polymarket agent
        demo_real_news_mock_polymarket_agent()

        print("\n" + "=" * 80)
        print("🎉 SUMMARY:")
        print("✅ Real fetchers provided actual market data from external APIs")
        print("✅ Mock agents made instant deterministic decisions")
        print("✅ Perfect for testing data pipelines and integration!")
        print("✅ No LLM costs, variability, or unpredictable responses")

    except KeyboardInterrupt:
        print("\n⏹️ Demo stopped by user")
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
