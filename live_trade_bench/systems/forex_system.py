from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from ..accounts import ForexAccount, create_forex_account
from ..agents.forex_agent import LLMForexAgent
from ..fetchers.forex_fetcher import ForexFetcher
from ..fetchers.news_fetcher import fetch_news_data


class ForexPortfolioSystem:
    """Portfolio system that manages FX allocations across major pairs."""

    def __init__(self, universe_size: int = 12) -> None:
        self.agents: Dict[str, LLMForexAgent] = {}
        self.accounts: Dict[str, ForexAccount] = {}
        self.universe: List[str] = []
        self.pair_info: Dict[str, Dict[str, Any]] = {}
        self.cycle_count = 0
        self.universe_size = universe_size
        self.fetcher = ForexFetcher()

    # ---------------------------------------------------------------- lifecycle
    def initialize_for_live(self) -> None:
        pairs = self.fetcher.get_major_pairs(limit=self.universe_size)
        self.set_universe(pairs)

    def initialize_for_backtest(self, trading_days: List[datetime]) -> None:
        _ = trading_days  # For potential future use
        self.initialize_for_live()

    def set_universe(self, pairs: List[str]) -> None:
        self.universe = pairs
        self.pair_info = {}
        for pair in pairs:
            base, quote = pair[:3], pair[3:6]
            self.pair_info[pair] = {"base": base, "quote": quote}

    def add_agent(
        self, name: str, initial_cash: float = 1000.0, model_name: str = "gpt-4o-mini"
    ) -> None:
        if name in self.agents:
            return
        agent = LLMForexAgent(name, model_name)
        account = create_forex_account(initial_cash)
        self.agents[name] = agent
        self.accounts[name] = account

    def run_cycle(self, for_date: str | None = None) -> None:
        self.cycle_count += 1
        current_time_str = for_date or datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        market_data = self._fetch_market_data(current_time_str if for_date else None)
        if not market_data:
            print("No FX market data available, skipping cycle.")
            return

        news_data = self._fetch_news_data(market_data, current_time_str if for_date else None)
        allocations = self._generate_allocations(market_data, news_data, current_time_str)
        self._update_accounts(allocations, market_data, current_time_str)

    # ----------------------------------------------------------------- fetchers
    def _fetch_market_data(
        self, for_date: str | None = None
    ) -> Dict[str, Dict[str, Any]]:
        market_data: Dict[str, Dict[str, Any]] = {}

        for pair in self.universe:
            try:
                price_payload = self.fetcher.get_price_with_history(
                    pair, lookback_days=10, date=for_date
                )
                current_price = price_payload.get("current_price")
                if current_price is None:
                    continue

                yahoo_symbol = self.fetcher._to_yahoo_symbol(pair)
                url = f"https://finance.yahoo.com/quote/{yahoo_symbol}"
                market_data[pair] = {
                    "pair": pair,
                    "base": price_payload.get("base", pair[:3]),
                    "quote": price_payload.get("quote", pair[3:6]),
                    "current_price": current_price,
                    "price_history": price_payload.get("price_history", []),
                    "url": url,
                }

                for account in self.accounts.values():
                    account.update_position_price(pair, current_price)
            except Exception as exc:
                print(f"Failed to fetch FX data for {pair}: {exc}")

        return market_data

    def _fetch_news_data(
        self, market_data: Dict[str, Any], for_date: str | None
    ) -> Dict[str, Any]:
        news_map: Dict[str, Any] = {}
        try:
            if for_date:
                ref = datetime.strptime(for_date[:10], "%Y-%m-%d") - timedelta(days=1)
            else:
                ref = datetime.utcnow()

            start_date = (ref - timedelta(days=3)).strftime("%Y-%m-%d")
            end_date = ref.strftime("%Y-%m-%d")

            for pair, data in market_data.items():
                base = data.get("base", pair[:3])
                quote = data.get("quote", pair[3:6])
                query = f"{base} {quote} forex news"
                news_map[pair] = fetch_news_data(
                    query,
                    start_date,
                    end_date,
                    max_pages=1,
                    ticker=pair,
                    target_date=for_date,
                )
        except Exception as exc:
            print(f"FX news fetch failed: {exc}")
        return news_map

    def _fetch_social_data(self) -> Dict[str, List[Dict[str, Any]]]:
        from ..fetchers.reddit_fetcher import RedditFetcher

        social_map: Dict[str, List[Dict[str, Any]]] = {}
        fetcher = RedditFetcher()

        for pair in self.universe:
            try:
                base, quote = pair[:3], pair[3:6]
                query = f"{base} {quote} forex"
                posts = fetcher.fetch(category="forex", query=query, max_limit=8)
                formatted = []
                for post in posts:
                    formatted.append(
                        {
                            "id": post.get("id", ""),
                            "title": post.get("title", ""),
                            "content": post.get("content", ""),
                            "author": post.get("author", "Unknown"),
                            "platform": "Reddit",
                            "url": post.get("url", ""),
                            "created_at": post.get("created_utc", ""),
                            "subreddit": post.get("subreddit", ""),
                            "upvotes": post.get("score", 0),
                            "num_comments": post.get("num_comments", 0),
                            "tag": pair,
                        }
                    )
                social_map[pair] = formatted
            except Exception as exc:
                print(f"FX social data fetch failed for {pair}: {exc}")
                social_map[pair] = []

        return social_map

    # --------------------------------------------------------------- allocations
    def _generate_allocations(
        self,
        market_data: Dict[str, Any],
        news_data: Dict[str, Any],
        for_date: str | None,
    ) -> Dict[str, Dict[str, float]]:
        all_allocations: Dict[str, Dict[str, float]] = {}
        for agent_name, agent in self.agents.items():
            account = self.accounts[agent_name]
            account_data = account.get_account_data()
            allocation = agent.generate_allocation(
                market_data, account_data, for_date, news_data=news_data
            )
            if allocation:
                all_allocations[agent_name] = allocation
            else:
                all_allocations[agent_name] = account.target_allocations
        return all_allocations

    def _update_accounts(
        self,
        allocations: Dict[str, Dict[str, float]],
        market_data: Dict[str, Any],
        for_date: str | None = None,
    ) -> None:
        price_map = {pair: data.get("current_price") for pair, data in market_data.items()}

        for agent_name, allocation in allocations.items():
            account = self.accounts[agent_name]
            account.target_allocations = allocation
            try:
                account.apply_allocation(
                    allocation, price_map=price_map, metadata_map=market_data
                )
                agent = self.agents.get(agent_name)
                llm_input = getattr(agent, "last_llm_input", None) if agent else None
                llm_output = getattr(agent, "last_llm_output", None) if agent else None
                account.record_allocation(
                    metadata_map=market_data,
                    backtest_date=for_date,
                    llm_input=llm_input,
                    llm_output=llm_output,
                )
            except Exception as exc:
                print(f"Failed to update FX account for {agent_name}: {exc}")

    # --------------------------------------------------------------- singletons
    @classmethod
    def get_instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = create_forex_portfolio_system()
        return cls._instance


def create_forex_portfolio_system() -> ForexPortfolioSystem:
    return ForexPortfolioSystem()

