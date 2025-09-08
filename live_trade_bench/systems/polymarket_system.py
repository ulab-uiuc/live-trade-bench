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
            }

    def add_agent(
        self, name: str, initial_cash: float = 500.0, model_name: str = "gpt-4o-mini"
    ) -> None:
        agent = LLMPolyMarketAgent(name, model_name)
        account = create_polymarket_account(initial_cash)
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
        market_data = {}
        for market_id in self.universe:
            try:
                price_data = None
                if for_date:
                    token_ids = self.market_info[market_id].get("token_ids")
                    if token_ids:
                        price_data = fetch_market_price_on_date(token_ids, for_date)
                else:
                    price_data = fetch_current_market_price(
                        self.market_info[market_id]["token_ids"]
                    )

                if price_data and "yes_price" in price_data:
                    market_data[market_id] = {
                        "id": market_id,
                        "question": self.market_info[market_id]["question"],
                        "category": self.market_info[market_id]["category"],
                        "price": float(price_data["yes_price"]),
                        "yes_price": float(price_data["yes_price"]),
                        "no_price": float(
                            price_data.get(
                                "no_price", 1.0 - float(price_data["yes_price"])
                            )
                        ),
                        "token_ids": self.market_info[market_id]["token_ids"],
                        "timestamp": price_data.get(
                            "timestamp", datetime.now().isoformat()
                        ),
                    }
                else:
                    question = self.market_info[market_id].get("question", market_id)
                    print(
                        f"    - ⚠️ No price data found for '{question[:40]}...' on {for_date}. Skipping."
                    )
            except Exception as e:
                print(f"    - Failed to fetch data for {market_id}: {e}")
        print(f"  - ✅ Market data fetched for {len(market_data)} markets")
        for market_id, data in list(market_data.items())[:3]:
            print(f"    - {data['question'][:40]}...: YES @ {data['yes_price']:.2%}")
        return market_data

    def _fetch_social_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch social media data (Reddit) for the market universe."""
        print("  - Fetching social media data...")
        from ..fetchers.reddit_fetcher import RedditFetcher

        social_data_map = {}
        fetcher = RedditFetcher()

        for market_id in self.universe[:3]:  # Limit for performance
            try:
                question = self.market_info.get(market_id, {}).get(
                    "question", market_id
                )
                query = " ".join(question.split()[:5])  # Use first few words as query
                posts = fetcher.fetch(category="market", query=query, max_limit=3)

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
                    query, start_date, end_date, max_pages=1
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
        self, allocations: Dict[str, Dict[str, float]], price_map: Dict
    ) -> None:
        print("  - Updating all accounts...")
        for agent_name, allocation in allocations.items():
            account = self.accounts[agent_name]
            account.target_allocations = allocation  # Set target allocation first

            # Rebalance account to target allocation
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
            cls._instance = create_polymarket_portfolio_system()
        return cls._instance


PolymarketTradingSystem = PolymarketPortfolioSystem


def create_polymarket_portfolio_system() -> PolymarketPortfolioSystem:
    return PolymarketPortfolioSystem()
