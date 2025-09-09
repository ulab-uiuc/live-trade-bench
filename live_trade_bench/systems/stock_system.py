from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from ..accounts import StockAccount, create_stock_account
from ..agents.stock_agent import LLMStockAgent
from ..fetchers.news_fetcher import fetch_news_data
from ..fetchers.stock_fetcher import (
    fetch_current_stock_price,
    fetch_stock_price_on_date,
    fetch_trending_stocks,
)


class StockPortfolioSystem:
    def __init__(self, universe_size: int = 10) -> None:
        self.agents: Dict[str, LLMStockAgent] = {}
        self.accounts: Dict[str, StockAccount] = {}
        self.universe: List[str] = []
        self.stock_info: Dict[str, Dict[str, Any]] = {}
        self.cycle_count = 0
        self.universe_size = universe_size

    def initialize_for_live(self):
        tickers = fetch_trending_stocks(limit=self.universe_size)
        self.universe = tickers
        self.stock_info = {
            ticker: {"name": ticker, "sector": "Unknown", "market_cap": 0}
            for ticker in tickers
        }

    def add_agent(
        self, name: str, initial_cash: float = 10000.0, model_name: str = "gpt-4o-mini"
    ) -> None:
        agent = LLMStockAgent(name, model_name)
        account = create_stock_account(initial_cash)
        self.agents[name] = agent
        self.accounts[name] = account

    def _format_social_content(self, content: str) -> str:
        """Helper to format social media content for display or analysis."""
        import re

        content = " ".join(content.split())
        content = re.sub(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            "[link]",
            content,
        )
        content = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\\1", content)
        content = re.sub(r"\\*\\*([^*]+)\\*\\*", r"\\1", content)
        return content[:300] + "..." if len(content) > 300 else content

    def run_cycle(self, for_date: str | None = None) -> None:
        print(
            f"\n--- 🔄 Cycle {self.cycle_count} | Processing {len(self.agents)} agents ---"
        )

        # 1. Fetch Market Data
        market_data = self._fetch_market_data(for_date)
        if not market_data:
            print("  - Market data fetch failed, skipping cycle")
            return

        # 2. Fetch News Data
        news_data = self._fetch_news_data(market_data, for_date)

        # 3. Generate Allocations for all agents
        allocations = self._generate_allocations(market_data, news_data, for_date)

        # 4. Update Accounts with new allocations
        self._update_accounts(allocations, market_data)

        self.cycle_count += 1
        print("--- ✅ Cycle Finished ---")

    def _fetch_market_data(self, for_date: str | None) -> Dict[str, Dict[str, Any]]:
        print("  - Fetching market data...")
        market_data = {}
        for ticker in self.universe:
            try:
                price = (
                    fetch_stock_price_on_date(ticker, for_date)
                    if for_date
                    else fetch_current_stock_price(ticker)
                )
                if price:
                    market_data[ticker] = {
                        "ticker": ticker,
                        "name": self.stock_info[ticker]["name"],
                        "sector": self.stock_info[ticker]["sector"],
                        "current_price": price,
                        "market_cap": self.stock_info[ticker]["market_cap"],
                    }
                    for account in self.accounts.values():
                        account.update_position_price(ticker, price)
            except Exception as e:
                print(f"    - Failed to fetch data for {ticker}: {e}")
        print(f"  - ✅ Market data fetched for {len(market_data)} stocks")
        for ticker, data in list(market_data.items())[:3]:
            print(f"    - {ticker}: ${data['current_price']:.2f}")
        return market_data

    def _fetch_social_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch social media data (Reddit) for the stock universe."""
        print("  - Fetching social media data...")
        from ..fetchers.reddit_fetcher import RedditFetcher

        social_data_map = {}
        fetcher = RedditFetcher()
        today = datetime.now().strftime("%Y-%m-%d")

        for ticker in self.universe[:3]:  # Limit to 3 tickers for performance
            try:
                posts = fetcher.fetch_posts_by_ticker(ticker, date=today, max_limit=3)
                formatted_posts = []
                for post in posts:
                    content = self._format_social_content(post.get("content", ""))
                    formatted_posts.append(
                        {
                            "content": content,
                            "author": post.get("author", "Unknown"),
                            "platform": "Reddit",
                            "url": post.get("url", ""),
                            "created_at": post.get("created_at", ""),
                        }
                    )
                social_data_map[ticker] = formatted_posts
            except Exception as e:
                print(f"    - Failed to fetch social data for {ticker}: {e}")

        print(f"  - ✅ Social media data fetched for {len(social_data_map)} stocks")
        return social_data_map

    def _fetch_news_data(
        self, market_data: Dict[str, Any], for_date: str | None
    ) -> Dict[str, Any]:
        print("  - Fetching news data...")
        news_data_map: Dict[str, Any] = {}
        try:
            ref = (
                datetime.strptime(for_date, "%Y-%m-%d") if for_date else datetime.now()
            )
            start_date = (ref - timedelta(days=3)).strftime("%Y-%m-%d")
            end_date = ref.strftime("%Y-%m-%d")
            for ticker in list(market_data.keys())[:3]:
                query = f"{ticker} stock earnings news"
                news_data_map[ticker] = fetch_news_data(
                    query, start_date, end_date, max_pages=1, ticker=ticker
                )
        except Exception as e:
            print(f"    - News data fetch failed: {e}")
        print("  - ✅ News data fetched")
        for ticker, news in list(news_data_map.items())[:2]:
            if news:
                print(f"    - News for {ticker}: {news[0].get('title', 'N/A')[:50]}...")
        return news_data_map

    def _generate_allocations(
        self,
        market_data: Dict[str, Any],
        news_data: Dict[str, Any],
        for_date: str | None,
    ) -> Dict[str, Dict[str, float]]:
        print("  - Generating allocations for all agents...")
        all_allocations = {}
        for agent_name, agent in self.agents.items():
            print(f"    - Processing agent: {agent_name}...")
            account = self.accounts[agent_name]
            account_data = account.get_account_data()

            allocation = agent.generate_allocation(
                market_data, account_data, for_date, news_data=news_data
            )
            if allocation:
                all_allocations[agent_name] = allocation
                print(
                    f"    - ✅ Allocation for {agent_name}: { {k: f'{v:.1%}' for k, v in allocation.items()} }"
                )
            else:
                print(
                    f"    - ⚠️ No allocation generated for {agent_name}, keeping previous target."
                )
                all_allocations[agent_name] = account.target_allocations
        print("  - ✅ All allocations generated")
        return all_allocations

    def _update_accounts(
        self, allocations: Dict[str, Dict[str, float]], market_data: Dict[str, Any]
    ) -> None:
        print("  - Updating all accounts...")
        price_map = {t: d.get("current_price") for t, d in market_data.items()}

        for agent_name, allocation in allocations.items():
            account = self.accounts[agent_name]
            account.target_allocations = allocation
            try:
                account.apply_allocation(allocation, price_map=price_map)
                account.record_allocation()
                print(
                    f"    - ✅ Account for {agent_name} updated. New Value: ${account.get_total_value():,.2f}, Cash: ${account.cash_balance:,.2f}"
                )
            except Exception as e:
                print(f"    - ❌ Failed to update account for {agent_name}: {e}")
        print("  - ✅ All accounts updated")

    @classmethod
    def get_instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = create_stock_portfolio_system()
        return cls._instance


StockTradingSystem = StockPortfolioSystem


def create_stock_portfolio_system() -> StockPortfolioSystem:
    return StockPortfolioSystem()
