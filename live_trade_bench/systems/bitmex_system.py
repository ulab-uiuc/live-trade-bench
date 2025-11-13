"""
BitMEX Portfolio System for managing multiple LLM agents trading perpetual contracts.
"""

from __future__ import annotations

import logging
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List

from ..accounts import BitMEXAccount, create_bitmex_account
from ..agents.bitmex_agent import LLMBitMEXAgent
from ..fetchers.bitmex_fetcher import BitMEXFetcher
from ..fetchers.news_fetcher import fetch_news_data

logger = logging.getLogger(__name__)


class BitMEXPortfolioSystem:
    """
    Portfolio system for BitMEX perpetual contract trading.

    Manages multiple LLM agents, each with independent accounts trading
    crypto perpetual contracts with 4x daily rebalancing.
    """

    def __init__(self, universe_size: int = 15) -> None:
        """
        Initialize BitMEX portfolio system.

        Args:
            universe_size: Number of contracts to track (default 15)
        """
        self.agents: Dict[str, LLMBitMEXAgent] = {}
        self.accounts: Dict[str, BitMEXAccount] = {}
        self.universe: List[str] = []
        self.contract_info: Dict[str, Dict[str, Any]] = {}
        self.cycle_count = 0
        self.universe_size = universe_size
        self.fetcher = BitMEXFetcher()

    def initialize_for_live(self) -> None:
        """Initialize for live trading by fetching trending contracts."""
        trending = self.fetcher.get_trending_contracts(limit=self.universe_size)
        symbols = [contract["symbol"] for contract in trending]
        self.set_universe(symbols)
        logger.info(f"Initialized BitMEX system with {len(symbols)} contracts")

    def initialize_for_backtest(self, trading_days: List[datetime]) -> None:
        """
        Initialize for backtesting.

        Args:
            trading_days: List of trading dates
        """
        trending = self.fetcher.get_trending_contracts(limit=self.universe_size)
        symbols = [contract["symbol"] for contract in trending]
        self.set_universe(symbols)

    def set_universe(self, symbols: List[str]) -> None:
        """
        Set the universe of tradable contracts.

        Args:
            symbols: List of BitMEX contract symbols (e.g., ["XBTUSD", "ETHUSD"])
        """
        self.universe = symbols
        self.contract_info = {symbol: {"name": symbol} for symbol in symbols}

    def add_agent(
        self, name: str, initial_cash: float = 10000.0, model_name: str = "gpt-4o-mini"
    ) -> None:
        """
        Add a new LLM agent with dedicated account.

        Args:
            name: Agent display name
            initial_cash: Starting capital (default $10,000)
            model_name: LLM model identifier
        """
        if name in self.agents:
            return
        agent = LLMBitMEXAgent(name, model_name)
        account = create_bitmex_account(initial_cash)
        self.agents[name] = agent
        self.accounts[name] = account

    def run_cycle(self, for_date: str | None = None) -> None:
        """
        Execute one trading cycle for all agents.

        Fetches market data, generates allocations, and updates accounts.

        Args:
            for_date: Optional date for backtesting (YYYY-MM-DD format)
        """
        logger.info(f"Cycle {self.cycle_count + 1} started for BitMEX System")
        if for_date:
            logger.info(f"Backtest mode - Date: {for_date}")
            current_time_str = for_date
        else:
            logger.info("Live Trading Mode (UTC)")
            current_time_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        self.cycle_count += 1
        logger.info("Fetching data for BitMEX perpetual contracts...")

        market_data = self._fetch_market_data(current_time_str if for_date else None)
        if not market_data:
            logger.warning("No market data for BitMEX, skipping cycle")
            return

        news_data = self._fetch_news_data(
            market_data, current_time_str if for_date else None
        )
        allocations = self._generate_allocations(
            market_data, news_data, current_time_str
        )
        self._update_accounts(allocations, market_data, current_time_str)

    def _fetch_market_data(
        self, for_date: str | None = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch comprehensive market data for all contracts.

        Includes:
        - Current prices and history
        - Funding rates
        - Order book depth
        - Open interest (from trending data)

        Args:
            for_date: Optional date for backtesting

        Returns:
            Dictionary mapping symbol to market data
        """
        logger.info("Fetching BitMEX market data...")
        market_data = {}

        for symbol in self.universe:
            try:
                # Get price with history (pass for_date for backtesting)
                price_data = self.fetcher.get_price_with_history(
                    symbol, lookback_days=10, price_type="mark", date=for_date
                )

                # Get funding rate
                try:
                    funding_data = self.fetcher.get_funding_rate(symbol)
                    funding_rate = funding_data.get("funding_rate") or 0.0
                except Exception:
                    funding_rate = 0.0

                # Get order book depth
                try:
                    orderbook = self.fetcher.get_orderbook(symbol, depth=10)
                    bids = orderbook.get("bids", [])
                    asks = orderbook.get("asks", [])
                    bid_depth = sum(b["size"] * b["price"] for b in bids[:10]) if bids else 0
                    ask_depth = sum(a["size"] * a["price"] for a in asks[:10]) if asks else 0
                except Exception:
                    bid_depth = 0
                    ask_depth = 0

                current_price = price_data.get("current_price")
                price_history = price_data.get("price_history", [])

                if current_price:
                    url = f"https://www.bitmex.com/app/trade/{symbol}"
                    market_data[symbol] = {
                        "symbol": symbol,
                        "name": symbol,
                        "current_price": current_price,
                        "price_history": price_history,
                        "funding_rate": funding_rate,
                        "bid_depth": bid_depth,
                        "ask_depth": ask_depth,
                        "open_interest": None,  # Could be added from trending data
                        "url": url,
                    }

                    # Update position prices in all accounts
                    for account in self.accounts.values():
                        account.update_position_price(symbol, current_price)

            except Exception as e:
                logger.error(f"Failed to fetch data for {symbol}: {e}")
                logger.debug(f"Full traceback for {symbol}:\n{traceback.format_exc()}")

        logger.info(f"Market data fetched for {len(market_data)} contracts")
        for symbol, data in list(market_data.items())[:3]:
            funding = (data.get("funding_rate") or 0) * 100
            logger.info(f"{symbol}: ${data['current_price']:,.2f} (funding: {funding:.4f}%)")

        return market_data

    def _fetch_news_data(
        self, market_data: Dict[str, Any], for_date: str | None
    ) -> Dict[str, Any]:
        """
        Fetch crypto news for all contracts.

        Args:
            market_data: Market data dictionary
            for_date: Optional date for backtesting

        Returns:
            Dictionary mapping symbol to news articles
        """
        print("  - Fetching crypto news data...")
        news_data_map: Dict[str, Any] = {}

        # Map symbols to crypto names for better news queries
        symbol_to_crypto = {
            "XBTUSD": "Bitcoin",
            "XBTUSDT": "Bitcoin",
            "ETHUSD": "Ethereum",
            "ETHUSDT": "Ethereum",
            "SOLUSDT": "Solana",
            "BNBUSDT": "BNB Binance",
            "XRPUSDT": "XRP Ripple",
            "ADAUSDT": "Cardano",
            "DOGEUSDT": "Dogecoin",
            "AVAXUSDT": "Avalanche",
            "LINKUSDT": "Chainlink",
            "LTCUSDT": "Litecoin",
        }

        try:
            if for_date:
                ref = datetime.strptime(for_date, "%Y-%m-%d") - timedelta(days=1)
            else:
                ref = datetime.utcnow()

            start_date = (ref - timedelta(days=3)).strftime("%Y-%m-%d")
            end_date = ref.strftime("%Y-%m-%d")

            for symbol in list(market_data.keys()):
                crypto_name = symbol_to_crypto.get(symbol, symbol)
                query = f"{crypto_name} crypto news"
                news_data_map[symbol] = fetch_news_data(
                    query,
                    start_date,
                    end_date,
                    max_pages=1,
                    ticker=symbol,
                    target_date=for_date,
                )
        except Exception as e:
            print(f"    - Crypto news data fetch failed: {e}")

        return news_data_map

    def _fetch_social_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch social media posts for crypto contracts.

        Returns:
            Dictionary mapping symbol to list of social posts
        """
        logger.info("Fetching crypto social media data...")
        from ..fetchers.reddit_fetcher import RedditFetcher

        social_data_map: Dict[str, List[Dict[str, Any]]] = {}
        fetcher = RedditFetcher()

        # Map symbols to searchable crypto terms
        symbol_to_search = {
            "XBTUSD": "Bitcoin",
            "XBTUSDT": "Bitcoin",
            "ETHUSD": "Ethereum",
            "ETHUSDT": "Ethereum",
            "ETH_XBT": "Ethereum",
            "SOLUSDT": "Solana",
            "SOL_USDT": "Solana",
            "BNBUSDT": "BNB",
            "XRPUSDT": "XRP",
            "ADAUSDT": "Cardano",
            "DOGEUSDT": "Dogecoin",
            "AVAXUSDT": "Avalanche",
            "LINKUSDT": "Chainlink",
            "LINK_USDT": "Chainlink",
            "LTCUSDT": "Litecoin",
            "BCHUSDT": "Bitcoin Cash",
            "PEPEUSDT": "Pepe",
            "FLOKIUSDT": "Floki",
            "BONK_USDT": "Bonk",
            "SHIBUSDT": "Shiba Inu",
            "SUIUSDT": "Sui",
            "ARBUSDT": "Arbitrum",
            "PUMPUSDT": "Pump",
            "STLS_USDT": "Starknet",
            "BMEX_USDT": "BitMEX",
        }

        for symbol in self.universe:
            try:
                crypto_name = symbol_to_search.get(symbol, symbol)
                logger.info(f"Fetching social data for crypto: {crypto_name} ({symbol})")

                # Fetch Reddit posts by crypto name query
                posts = fetcher.fetch(
                    category="crypto", query=crypto_name, max_limit=10
                )
                logger.info(f"Fetched {len(posts)} social posts for {symbol}")

                formatted_posts = []
                for post in posts:
                    formatted_posts.append({
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
                        "tag": symbol,
                    })
                social_data_map[symbol] = formatted_posts
            except Exception as e:
                logger.error(f"Failed to fetch social data for {symbol}: {e}")
                social_data_map[symbol] = []

        return social_data_map

    def _generate_allocations(
        self,
        market_data: Dict[str, Any],
        news_data: Dict[str, Any],
        for_date: str | None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Generate allocations for all agents.

        Args:
            market_data: Market data dictionary
            news_data: News data dictionary
            for_date: Optional date string

        Returns:
            Dictionary mapping agent name to allocation
        """
        logger.info("Generating allocations for all agents...")
        all_allocations = {}

        for agent_name, agent in self.agents.items():
            logger.info(f"Processing agent: {agent_name}")
            account = self.accounts[agent_name]
            account_data = account.get_account_data()

            allocation = agent.generate_allocation(
                market_data, account_data, for_date, news_data=news_data
            )

            if allocation:
                all_allocations[agent_name] = allocation
                logger.info(
                    f"Allocation for {agent_name}: "
                    f"{ {k: f'{v:.1%}' for k, v in list(allocation.items())[:5]} }"
                )
            else:
                logger.warning(
                    f"No allocation generated for {agent_name}, keeping previous target"
                )
                all_allocations[agent_name] = account.target_allocations

        logger.info("All allocations generated")
        return all_allocations

    def _update_accounts(
        self,
        allocations: Dict[str, Dict[str, float]],
        market_data: Dict[str, Any],
        for_date: str | None = None,
    ) -> None:
        """
        Update all accounts with new allocations.

        Args:
            allocations: Dictionary mapping agent name to allocation
            market_data: Market data dictionary
            for_date: Optional date string
        """
        logger.info("Updating all accounts...")
        price_map = {s: d.get("current_price") for s, d in market_data.items()}

        for agent_name, allocation in allocations.items():
            account = self.accounts[agent_name]
            account.target_allocations = allocation

            try:
                account.apply_allocation(
                    allocation, price_map=price_map, metadata_map=market_data
                )

                # Capture LLM input/output for audit trail
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

                logger.info(
                    f"Account for {agent_name} updated. "
                    f"New Value: ${account.get_total_value():,.2f}, "
                    f"Cash: ${account.cash_balance:,.2f}"
                )
            except Exception as e:
                logger.error(f"Failed to update account for {agent_name}: {e}")

        logger.info("All accounts updated")

    @classmethod
    def get_instance(cls):
        """Get singleton instance (for compatibility with mock systems)."""
        if not hasattr(cls, "_instance"):
            cls._instance = create_bitmex_portfolio_system()
        return cls._instance


def create_bitmex_portfolio_system() -> BitMEXPortfolioSystem:
    """
    Create a new BitMEX portfolio system instance.

    Returns:
        Initialized BitMEXPortfolioSystem
    """
    return BitMEXPortfolioSystem()
