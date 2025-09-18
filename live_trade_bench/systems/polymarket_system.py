from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from ..accounts import PolymarketAccount, create_polymarket_account
from ..agents.polymarket_agent import LLMPolyMarketAgent
from ..fetchers.news_fetcher import fetch_news_data
from ..fetchers.polymarket_fetcher import (
    fetch_market_price_with_history,
    fetch_verified_markets,
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

    def initialize_from_init_data(self):
        """Initialize markets from init data file with real token IDs"""
        import json
        import os

        # Path to init file
        backend_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        init_file = os.path.join(backend_root, "backend", "models_data_init.json")

        if not os.path.exists(init_file):
            print(f"Init file not found: {init_file}")
            return

        try:
            # Extract unique URLs from init data
            urls = set()
            with open(init_file, "r") as f:
                historical_data = json.load(f)

            for model_data in historical_data:
                if model_data.get("category") == "polymarket":
                    # Extract URLs from allocation history (more complete)
                    allocation_history = model_data.get("allocationHistory", [])
                    for snapshot in allocation_history:
                        allocations_array = snapshot.get("allocations_array", [])
                        for allocation in allocations_array:
                            url = allocation.get("url")
                            if url:
                                urls.add(url)

                    # Also check positions as backup
                    positions = model_data.get("portfolio", {}).get("positions", {})
                    for pos_data in positions.values():
                        url = pos_data.get("url")
                        if url:
                            urls.add(url)

            print(f"Found {len(urls)} unique URLs from init data")
            for url in list(urls)[:3]:  # Show first 3 URLs for debugging
                print(f"  - {url}")

            # Get real market data from URLs
            markets = []
            for url in list(urls)[: self.universe_size]:
                event_slug = url.split("/")[-1]
                print(f"Trying to get market data for event_slug: {event_slug}")
                market_data = self._get_market_by_event_slug(event_slug, url)
                if market_data:
                    markets.append(market_data)
                    print(f"  ✅ Found market: {market_data.get('question', 'Unknown')}")
                else:
                    print(f"  ❌ No market data found for {event_slug}")

            self.set_universe(markets)
            print(
                f"Initialized {len(markets)} markets from init data with real token IDs"
            )

        except Exception as e:
            print(f"Failed to load markets from init data: {e}")

    def _get_market_by_event_slug(self, event_slug, url):
        """Get market data by event slug from Polymarket API"""
        try:
            from ..fetchers.polymarket_fetcher import PolymarketFetcher

            fetcher = PolymarketFetcher()
            # Search for active markets with much larger limit
            params = {
                "limit": 500,  # Much larger limit to find our markets
                "active": "true",
                "closed": "false",
            }
            markets = fetcher._fetch_markets(params)

            print(f"    API returned {len(markets)} markets")
            if len(markets) > 0:
                print(
                    f"    First market example: {markets[0].keys() if markets[0] else 'Empty'}"
                )

            found_event_slugs = []
            for market in markets:
                if not isinstance(market, dict) or not market.get("id"):
                    continue

                # Check if this market matches our event slug
                if market.get("events") and len(market["events"]) > 0:
                    market_event_slug = market["events"][0].get("slug")
                    found_event_slugs.append(market_event_slug)

                    if market_event_slug == event_slug:
                        print(f"    🎯 Found matching event slug: {market_event_slug}")
                        # Parse token_ids and outcomes
                        raw_token_ids = market.get("clobTokenIds", [])
                        raw_outcomes = market.get("outcomes", [])

                        if isinstance(raw_token_ids, str):
                            import json

                            token_ids = json.loads(raw_token_ids)
                            outcomes = json.loads(raw_outcomes)
                        else:
                            token_ids = raw_token_ids
                            outcomes = raw_outcomes

                        if token_ids:  # Only return if we have real token IDs
                            return {
                                "id": market.get("id"),
                                "question": market.get("question"),
                                "category": market.get("category"),
                                "token_ids": token_ids,
                                "outcomes": outcomes,
                                "event_slug": event_slug,
                                "url": url,
                            }
                        else:
                            print("    ⚠️ Found market but no token_ids")

            print(
                f"    Available event slugs: {found_event_slugs[:5]}..."
            )  # Show first 5
            print(f"    Looking for: {event_slug}")

        except Exception as e:
            print(f"Failed to get market data for {event_slug}: {e}")

        return None

    def initialize_for_live(self):
        # markets = fetch_trending_markets(limit=self.universe_size)
        # self.set_universe(markets)
        # from datetime import datetime, timedelta
        self.initialize_from_init_data()
        # end_date = datetime.now()
        # trading_days = []
        # for i in range(5):
        #     day = end_date - timedelta(days=i)
        #     trading_days.append(day)
        # markets = fetch_verified_markets(trading_days, self.universe_size)
        # self.set_universe(markets)

    def initialize_for_backtest(self, trading_days: List[datetime]):
        verified_markets = fetch_verified_markets(trading_days, self.universe_size)
        self.set_universe(verified_markets)

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
                "outcomes": m.get("outcomes", []),
                "url": m.get("url"),
            }

    def add_agent(
        self, name: str, initial_cash: float = 500.0, model_name: str = "gpt-4o-mini"
    ) -> None:
        if name in self.agents:
            return
        agent = LLMPolyMarketAgent(name, model_name)
        account = create_polymarket_account(initial_cash)
        self.agents[name] = agent
        self.accounts[name] = account

    def run_cycle(self, for_date: str | None = None) -> None:
        print(f"\n--- 🔄 Cycle {self.cycle_count + 1} for Polymarket System ---")
        if for_date:
            print(f"--- 📅 Backtest Date: {for_date} ---")
            current_time_str = for_date
        else:
            print("--- 🚀 Live Trading Mode ---")
            current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.cycle_count += 1
        print("Fetching data for polymarket portfolio...")

        market_data = self._fetch_market_data(current_time_str if for_date else None)
        if not market_data:
            print("No market data for polymarkets, skipping cycle.")
            return

        news_data = self._fetch_news_data(
            market_data, current_time_str if for_date else None
        )
        allocations = self._generate_allocations(
            market_data, news_data, current_time_str if for_date else None
        )
        self._update_accounts(
            allocations, market_data, current_time_str if for_date else None
        )

    def _fetch_market_data(
        self, for_date: str | None = None
    ) -> Dict[str, Dict[str, Any]]:
        print("  - Fetching market data...")
        market_data_expanded = {}
        for market_id in self.universe:
            try:
                market_info = self.market_info[market_id]
                token_ids = market_info.get("token_ids")
                outcomes = market_info.get("outcomes")
                if not token_ids or len(token_ids) < 2:
                    continue
                question = market_info["question"]
                url = market_info.get("url")
                for outcome, token_id in zip(outcomes, token_ids):
                    if not token_id:
                        continue
                    price_data = fetch_market_price_with_history(token_id, for_date)
                    current_price = price_data.get("current_price")
                    if current_price is not None:
                        key = f"{question}_{outcome}"
                        market_data_expanded[key] = {
                            "price": current_price,
                            "outcome": outcome,
                            "id": f"{market_id}_{outcome}",
                            "question": question,
                            "url": url,
                            "price_history": price_data.get("price_history", []),
                        }
            except Exception as e:
                question = self.market_info[market_id].get("question", market_id)
                print(f"    - Failed to fetch data for '{question[:40]}...': {e}")
        print(f"  - ✅ Market data fetched for {len(market_data_expanded)} markets")
        self.market_data = market_data_expanded
        return self.market_data

    def _fetch_social_data(self) -> Dict[str, List[Dict[str, Any]]]:
        print("  - Fetching social media data...")
        from ..fetchers.reddit_fetcher import RedditFetcher

        social_data_map = {}
        fetcher = RedditFetcher()
        for market_id in self.universe:
            try:
                print(f"    - Fetching social data for polymarket: {market_id}...")
                question = self.market_info.get(market_id, {}).get(
                    "question", market_id
                )
                query = " ".join(question.split()[:5])
                posts = fetcher.fetch(category="market", query=query, max_limit=10)
                print(f"    - Fetched {len(posts)} social posts for {market_id}.")
                formatted_posts = []
                for post in posts:
                    formatted_posts.append(
                        {
                            "title": post.get("title", ""),
                            "content": post.get("content", ""),
                            "author": post.get("author", "Unknown"),
                            "platform": "Reddit",
                            "url": post.get("url", ""),
                            "created_at": post.get("created_utc", ""),
                            "subreddit": post.get("subreddit", ""),
                            "upvotes": post.get("upvotes", 0),
                            "num_comments": post.get("num_comments", 0),
                            "tag": query,
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
            if for_date:
                ref = datetime.strptime(for_date, "%Y-%m-%d") - timedelta(days=1)
            else:
                ref = datetime.now()

            start_date = (ref - timedelta(days=3)).strftime("%Y-%m-%d")
            end_date = ref.strftime("%Y-%m-%d")
            for market_id in list(market_data.keys()):
                question = market_data[market_id]["question"]
                news_data_map[market_id] = fetch_news_data(
                    question,
                    start_date,
                    end_date,
                    max_pages=1,
                    ticker=question,
                    target_date=for_date,
                )
        except Exception as e:
            print(f"    - News data fetch failed: {e}")
        print("  - ✅ News data fetched")
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
                cleaned_allocation = {}
                for symbol, value in raw_allocation.items():
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
        self,
        allocations: Dict[str, Dict[str, float]],
        market_data: Dict,
        for_date: str | None = None,
    ) -> None:
        print("  - Updating all accounts...")
        price_map = {key: asset["price"] for key, asset in market_data.items()}
        for agent_name, allocation in allocations.items():
            account = self.accounts[agent_name]
            account.target_allocations = allocation
            try:
                account.apply_allocation(
                    allocation, price_map=price_map, metadata_map=market_data
                )
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
            cls._instance = create_polymarket_portfolio_system()
        return cls._instance


def create_polymarket_portfolio_system() -> PolymarketPortfolioSystem:
    return PolymarketPortfolioSystem()
