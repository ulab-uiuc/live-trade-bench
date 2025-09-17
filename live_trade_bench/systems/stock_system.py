from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from live_trade_bench.fetchers.constants import TICKER_TO_COMPANY

from ..accounts import StockAccount, create_stock_account
from ..agents.stock_agent import LLMStockAgent
from ..fetchers.news_fetcher import fetch_news_data
from ..fetchers.stock_fetcher import (
    fetch_stock_price_with_history,
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
        self.set_universe(tickers)

    def initialize_for_backtest(self, trading_days: List[datetime]):
        tickers = fetch_trending_stocks(limit=self.universe_size)
        self.set_universe(tickers)

    def set_universe(self, tickers: List[str]):
        self.universe = tickers
        self.stock_info = {ticker: {"name": ticker} for ticker in tickers}

    def add_agent(
        self, name: str, initial_cash: float = 10000.0, model_name: str = "gpt-4o-mini"
    ) -> None:
        if name in self.agents:  # avoid overwriting existing account/agent
            return
        agent = LLMStockAgent(name, model_name)
        account = create_stock_account(initial_cash)
        self.agents[name] = agent
        self.accounts[name] = account

    def run_cycle(self, for_date: str | None = None) -> None:
        print(f"\n--- 🔄 Cycle {self.cycle_count + 1} for Stock System ---")
        if for_date:
            print(f"--- 📅 Backtest Date: {for_date} ---")
            current_time_str = for_date
        else:
            print("--- 🚀 Live Trading Mode ---")
            current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.cycle_count += 1
        print("Fetching data for stock portfolio...")

        # 1. Fetch market data
        market_data = self._fetch_market_data(current_time_str if for_date else None)
        if not market_data:
            print("No market data for stocks, skipping cycle.")
            return

        # 2. Fetch news and social media data
        news_data = self._fetch_news_data(
            market_data, current_time_str if for_date else None
        )

        # 3. Generate allocations from agents
        allocations = self._generate_allocations(
            market_data, news_data, current_time_str if for_date else None
        )

        # 4. Update accounts based on allocations
        self._update_accounts(
            allocations, market_data, current_time_str if for_date else None
        )

    def _fetch_market_data(
        self, for_date: str | None = None
    ) -> Dict[str, Dict[str, Any]]:
        print("  - Fetching market data...")
        market_data = {}
        for ticker in self.universe:
            try:
                # Use the new function that gets both current price and history
                price_data = fetch_stock_price_with_history(ticker, for_date)
                current_price = price_data.get("current_price")
                price_history = price_data.get("price_history", [])

                if current_price:
                    url = f"https://finance.yahoo.com/quote/{ticker}"
                    market_data[ticker] = {
                        "ticker": ticker,
                        "name": self.stock_info[ticker]["name"],
                        "current_price": current_price,
                        "price_history": price_history,
                        "url": url,
                    }
                    for account in self.accounts.values():
                        account.update_position_price(ticker, current_price)
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

        # Update universe with latest trending stocks for social media fetching
        latest_trending_stocks = fetch_trending_stocks(limit=self.universe_size)
        if latest_trending_stocks:
            self.universe = latest_trending_stocks
            print(
                f"  - Updated social media universe to {len(self.universe)} trending stocks."
            )

        for ticker in self.universe:  # Fetch social data for all available tickers
            try:
                print(f"    - Fetching social data for stock: {ticker}...")
                posts = fetcher.fetch_posts_by_ticker(
                    ticker, date=today, max_limit=10
                )  # Increased max_limit
                print(f"    - Fetched {len(posts)} social posts for {ticker}.")
                formatted_posts = []
                for post in posts:
                    content = post.get("content", "")  # No longer format content here
                    formatted_posts.append(
                        {
                            "title": post.get("title", ""),
                            "content": content,
                            "author": post.get("author", "Unknown"),
                            "platform": "Reddit",
                            "url": post.get("url", ""),
                            "created_at": post.get(
                                "created_utc", ""
                            ),  # Use created_utc
                            "subreddit": post.get("subreddit", ""),  # Add subreddit
                            "upvotes": post.get("upvotes", 0),  # Add upvotes
                            "num_comments": post.get(
                                "num_comments", 0
                            ),  # Add num_comments
                            "tag": ticker,  # Add ticker as tag
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
            for ticker in list(
                market_data.keys()
            ):  # Fetch news for all available tickers
                query = f"{ticker} stock news OR {TICKER_TO_COMPANY[ticker]}"
                news_data_map[ticker] = fetch_news_data(
                    query,
                    start_date,
                    end_date,
                    max_pages=1,
                    ticker=ticker,
                    target_date=for_date,
                )
        except Exception as e:
            print(f"    - News data fetch failed: {e}")
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
        self,
        allocations: Dict[str, Dict[str, float]],
        market_data: Dict[str, Any],
        for_date: str | None = None,
    ) -> None:
        print("  - Updating all accounts...")
        price_map = {t: d.get("current_price") for t, d in market_data.items()}

        for agent_name, allocation in allocations.items():
            account = self.accounts[agent_name]
            account.target_allocations = allocation
            try:
                account.apply_allocation(
                    allocation, price_map=price_map, metadata_map=market_data
                )
                # Capture and persist agent LLM info if available
                llm_input = None
                llm_output = None
                agent = self.agents.get(agent_name)
                if agent is not None:
                    llm_input = getattr(agent, "last_llm_input", None)
                    llm_output = getattr(agent, "last_llm_output", None)
                account.record_allocation(
                    metadata_map=market_data,
                    backtest_date=for_date,
                    llm_input=llm_input,
                    llm_output=llm_output,
                )
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
