from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from ..accounts import PolymarketAccount, create_polymarket_account
from ..agents.polymarket_agent import LLMPolyMarketAgent
from ..fetchers.news_fetcher import fetch_news_data
from ..fetchers.polymarket_fetcher import (
    fetch_current_market_price,
    fetch_market_price_on_date,
    fetch_trending_markets,
    fetch_verified_historical_markets,
)


class PolymarketPortfolioSystem:
    def __init__(self, universe_size: int = 5) -> None:
        self.agents: Dict[str, LLMPolyMarketAgent] = {}
        self.accounts: Dict[str, PolymarketAccount] = {}
        self.universe: List[str] = []
        self.market_info: Dict[str, Dict[str, Any]] = {}
        self.cycle_count = 0
        self.universe_size = universe_size
        self.market_data: Dict[str, Dict[str, Any]] = {}
        self.initialize_for_live()

    def initialize_for_backtest(self, trading_days: List[datetime]):
        print("--- Initializing Polymarket universe for backtest period... ---")
        verified_markets = fetch_verified_historical_markets(
            trading_days, self.universe_size
        )
        self.set_universe(verified_markets)
        print(
            f"--- Polymarket universe finalized with {len(self.universe)} markets. ---"
        )

    def initialize_for_live(self):
        markets = fetch_trending_markets(limit=self.universe_size)
        self.set_universe(markets)

    def set_universe(self, markets: List[Dict[str, Any]]):
        self.universe = []
        self.market_info = {}
        for m in markets:
            market_id = m["id"]
            self.universe.append(market_id)
            self.market_info[market_id] = {
                "question": m.get("question", str(market_id)),
                "category": m.get("category", "Unknown"),
                "token_ids": m.get("token_ids", []),
                "url": m.get("url"),
            }

    def add_agent(
        self, name: str, initial_cash: float = 500.0, model_name: str = "gpt-4o-mini"
    ) -> None:
        agent = LLMPolyMarketAgent(name, model_name)
        account = create_polymarket_account(initial_cash)
        self.agents[name] = agent
        self.accounts[name] = account

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

        # 3. Generate Allocations
        allocations = self._generate_allocations(market_data, news_data, for_date)

        # 4. Update Accounts
        self._update_accounts(allocations, market_data)

        self.cycle_count += 1
        print("--- ✅ Cycle Finished ---")

    def _fetch_market_data(
        self, for_date: str | None = None
    ) -> Dict[str, Dict[str, Any]]:
        print("  - Fetching market data...")
        market_data_expanded = {}
        for market_id in self.universe:
            try:
                price_data = None
                token_ids = self.market_info[market_id].get("token_ids")
                if not token_ids:
                    continue

                if for_date:
                    price_data = fetch_market_price_on_date(token_ids, for_date)
                else:
                    price_data = fetch_current_market_price(token_ids)

                if price_data:
                    question = self.market_info[market_id]["question"]
                    url = self.market_info[market_id].get("url")

                    yes_key = f"{question}_YES"
                    no_key = f"{question}_NO"

                    if yes_key in price_data:
                        price_data[yes_key].update(
                            {"id": f"{market_id}_YES", "question": question, "url": url}
                        )

                    if no_key in price_data:
                        price_data[no_key].update(
                            {"id": f"{market_id}_NO", "question": question, "url": url}
                        )

                    market_data_expanded.update(price_data)
                else:
                    question = self.market_info[market_id].get("question", market_id)
                    print(
                        f"    - ⚠️ No price data found for '{question[:40]}...'. Skipping."
                    )
            except Exception as e:
                print(f"    - Failed to fetch data for {market_id}: {e}")

        print(
            f"  - ✅ Market data fetched and expanded for {len(market_data_expanded) // 2} markets"
        )
        self.market_data = market_data_expanded  # Store the expanded data
        return self.market_data

    def _fetch_social_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch social media data (Reddit) for the market universe."""
        print("  - Fetching social media data...")
        from ..fetchers.reddit_fetcher import RedditFetcher

        social_data_map = {}
        fetcher = RedditFetcher()

        for market_id in self.universe:  # Fetch social data for all available markets
            try:
                print(f"    - Fetching social data for polymarket: {market_id}...")
                question = self.market_info.get(market_id, {}).get(
                    "question", market_id
                )
                query = " ".join(question.split()[:5])  # Use first few words as query
                posts = fetcher.fetch(
                    category="market", query=query, max_limit=10
                )  # Increased max_limit
                print(f"    - Fetched {len(posts)} social posts for {market_id}.")

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
                            "tag": query,  # Add query as tag
                        }
                    )
                social_data_map[market_id] = formatted_posts
            except Exception as e:
                print(f"    - Failed to fetch social data for {market_id}: {e}")

        print(f"  - ✅ Social media data fetched for {len(social_data_map)} markets")
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
            for market_id in list(market_data.keys())[:3]:
                question = self.market_info.get(market_id, {}).get(
                    "question", str(market_id)
                )
                query = " ".join(question.split()[:5]) if question else str(market_id)
                news_data_map[market_id] = fetch_news_data(
                    query, start_date, end_date, max_pages=1, ticker=query
                )
        except Exception as e:
            print(f"    - News data fetch failed: {e}")
        print("  - ✅ News data fetched")
        for market_id, news in list(news_data_map.items())[:2]:
            if news:
                print(
                    f"    - News for {market_id}: {news[0].get('title', 'N/A')[:50]}..."
                )
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

            raw_allocation = agent.generate_allocation(
                market_data, account_data, for_date, news_data=news_data
            )

            if raw_allocation:
                # --- DATA CLEANING & NORMALIZATION ---
                cleaned_allocation = {}
                for symbol, value in raw_allocation.items():
                    # Default to YES outcome if not specified
                    if "_" not in symbol and symbol != "CASH":
                        symbol = f"{symbol}_YES"

                    if isinstance(value, str) and "%" in value:
                        try:
                            cleaned_allocation[symbol] = (
                                float(value.strip(" %")) / 100.0
                            )
                        except ValueError:
                            cleaned_allocation[symbol] = 0.0
                    elif isinstance(value, (int, float)):
                        cleaned_allocation[symbol] = value

                all_allocations[agent_name] = cleaned_allocation
                print(
                    f"    - ✅ Allocation for {agent_name}: { {k: f'{v:.1%}' for k, v in cleaned_allocation.items()} }"
                )
            else:
                print(f"    - ⚠️ No allocation generated for {agent_name}")
                all_allocations[agent_name] = account.target_allocations
        print("  - ✅ All allocations generated")
        return all_allocations

    def _update_accounts(
        self, allocations: Dict[str, Dict[str, float]], market_data: Dict
    ) -> None:
        print("  - Updating all accounts...")

        # The price_map keys should be the same as allocation keys (question_outcome)
        price_map = {key: asset["price"] for key, asset in market_data.items()}

        for agent_name, allocation in allocations.items():
            account = self.accounts[agent_name]

            # No more translation. Use question-based allocation directly.
            account.target_allocations = allocation

            # Rebalance account to target allocation
            try:
                account.apply_allocation(
                    allocation, price_map=price_map, metadata_map=market_data
                )
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
            cls._instance = create_polymarket_portfolio_system()
        return cls._instance


PolymarketTradingSystem = PolymarketPortfolioSystem


def create_polymarket_portfolio_system() -> PolymarketPortfolioSystem:
    return PolymarketPortfolioSystem()
