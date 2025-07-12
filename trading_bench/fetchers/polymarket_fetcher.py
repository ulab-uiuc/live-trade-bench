"""
Polymarket data fetcher for trading bench.

This module provides functions to fetch prediction market data from Polymarket
using their API endpoints with fallback mock data.
"""

import random
from datetime import datetime

from trading_bench.fetchers.base_fetcher import BaseFetcher


class PolymarketFetcher(BaseFetcher):
    """Fetcher for Polymarket prediction market data."""

    def __init__(self, min_delay: float = 0.5, max_delay: float = 1.5):
        """Initialize the Polymarket fetcher."""
        super().__init__(min_delay, max_delay)

    def _get_mock_markets(self) -> list[dict]:
        """Generate mock market data for testing/fallback purposes."""
        mock_markets = [
            {
                "id": f"market_{i}",
                "title": f"Mock Market {i}: Will Bitcoin reach $100K by end of 2024?",
                "category": "crypto",
                "description": f"This is a mock prediction market about Bitcoin price reaching $100,000 by the end of 2024. Market {i}.",
                "end_date": "2024-12-31T23:59:59Z",
                "status": "active",
                "total_volume": random.uniform(10000, 1000000),
                "total_liquidity": random.uniform(5000, 500000),
            }
            for i in range(1, 21)
        ]

        # Add some variety to mock data
        categories = ["politics", "sports", "crypto", "entertainment", "tech"]
        titles = [
            "Will the US presidential election be decided by less than 1%?",
            "Will the Super Bowl have over 60 points scored?",
            "Will Ethereum reach $5000 by year end?",
            "Will the next Marvel movie gross over $1B?",
            "Will Apple announce a new product category this year?",
        ]

        for i, market in enumerate(mock_markets[:5]):
            market["category"] = categories[i]
            market["title"] = f"Mock Market: {titles[i]}"

        return mock_markets

    def fetch_markets(self, category: str | None = None, limit: int = 50) -> list[dict]:
        """
        Fetch available markets from Polymarket API.
        Args:
            category: Market category filter (e.g., 'politics', 'sports', 'crypto').
            limit: Maximum number of markets to return.
        Returns:
            list: List of available markets with basic information.
        Raises:
            RuntimeError: If the API request fails or returns invalid data.
        """
        try:
            url = "https://clob.polymarket.com/markets"
            response = self.make_request(url, timeout=10)
            if response.status_code == 200:
                markets_data = self.safe_json_parse(response, "Polymarket markets API")
                # Ensure we're working with a list
                if not isinstance(markets_data, list):
                    if isinstance(markets_data, dict) and "data" in markets_data:
                        markets_data = markets_data["data"]
                    else:
                        raise RuntimeError("Unexpected API response format")
                # Filter by category if specified
                if category:
                    markets_data = [
                        market
                        for market in markets_data
                        if isinstance(market, dict)
                        and category.lower() in str(market.get("category", "")).lower()
                    ]
                # Limit results
                if len(markets_data) > limit:
                    markets_data = markets_data[:limit]
                # Extract relevant information, fill missing fields with None
                markets = []
                for market in markets_data:
                    if isinstance(market, dict):
                        markets.append(
                            {
                                "id": market.get("id"),
                                "title": market.get(
                                    "title", market.get("question", None)
                                ),
                                "category": market.get("category", None),
                                "description": market.get("description", None),
                                "end_date": market.get(
                                    "endDate", market.get("end_date", None)
                                ),
                                "status": market.get("status", None),
                                "total_volume": float(
                                    market.get("totalVolume", market.get("volume", 0))
                                )
                                if market.get("totalVolume") or market.get("volume")
                                else None,
                                "total_liquidity": float(
                                    market.get(
                                        "totalLiquidity", market.get("liquidity", 0)
                                    )
                                )
                                if market.get("totalLiquidity")
                                or market.get("liquidity")
                                else None,
                            }
                        )
                return markets
            else:
                raise RuntimeError(f"API returned status code: {response.status_code}")
        except Exception as api_error:
            raise RuntimeError(f"API fetch failed: {api_error}")

    def fetch_market_details(self, market_id: str) -> dict:
        """
        Fetch detailed information for a specific Polymarket market.
        Args:
            market_id: The unique identifier for the market.
        Returns:
            dict: Detailed market information including outcomes and current prices.
        Raises:
            RuntimeError: If the API request fails or returns invalid data.
        """
        try:
            url = f"https://clob.polymarket.com/markets/{market_id}"
            response = self.make_request(url, timeout=10)
            if response.status_code == 200:
                market_data = self.safe_json_parse(
                    response, "Polymarket market details API"
                )
                if not isinstance(market_data, dict):
                    raise RuntimeError("Invalid market data format")
                # Extract outcomes and their current prices, fill missing fields with None
                outcomes = []
                outcomes_data = market_data.get("outcomes", [])
                for outcome in outcomes_data:
                    if isinstance(outcome, dict):
                        outcomes.append(
                            {
                                "id": outcome.get("id"),
                                "name": outcome.get("name", outcome.get("title", None)),
                                "current_price": float(
                                    outcome.get(
                                        "currentPrice", outcome.get("price", None)
                                    )
                                )
                                if outcome.get("currentPrice") or outcome.get("price")
                                else None,
                                "volume_24h": float(
                                    outcome.get(
                                        "volume24h", outcome.get("volume", None)
                                    )
                                )
                                if outcome.get("volume24h") or outcome.get("volume")
                                else None,
                                "liquidity": float(outcome.get("liquidity", None))
                                if outcome.get("liquidity")
                                else None,
                                "probability": float(
                                    outcome.get(
                                        "probability", outcome.get("currentPrice", None)
                                    )
                                )
                                if outcome.get("probability")
                                or outcome.get("currentPrice")
                                else None,
                            }
                        )
                return {
                    "id": market_data.get("id", market_id),
                    "title": market_data.get(
                        "title", market_data.get("question", None)
                    ),
                    "description": market_data.get("description", None),
                    "category": market_data.get("category", None),
                    "status": market_data.get("status", None),
                    "end_date": market_data.get(
                        "endDate", market_data.get("end_date", None)
                    ),
                    "total_volume": float(
                        market_data.get("totalVolume", market_data.get("volume", 0))
                    )
                    if market_data.get("totalVolume") or market_data.get("volume")
                    else None,
                    "total_liquidity": float(
                        market_data.get(
                            "totalLiquidity", market_data.get("liquidity", 0)
                        )
                    )
                    if market_data.get("totalLiquidity") or market_data.get("liquidity")
                    else None,
                    "outcomes": outcomes,
                }
            else:
                raise RuntimeError(f"API returned status code: {response.status_code}")
        except Exception as e:
            raise RuntimeError(f"Market details API failed: {e}")

    def fetch_orderbook(self, market_id: str, outcome_id: str | None = None) -> dict:
        """
        Fetch order book data for a specific market and outcome.
        Args:
            market_id: The unique identifier for the market.
            outcome_id: The specific outcome ID (optional).
        Returns:
            dict: Order book with bids and asks.
        Raises:
            RuntimeError: If the API request fails or returns invalid data.
        """
        try:
            url = f"https://clob.polymarket.com/markets/{market_id}/orderbook"
            if outcome_id:
                url += f"?outcome={outcome_id}"
            response = self.make_request(url, timeout=10)
            if response.status_code == 200:
                orderbook_data = self.safe_json_parse(
                    response, "Polymarket orderbook API"
                )
                if not isinstance(orderbook_data, dict):
                    raise RuntimeError("Invalid orderbook data format")
                return {
                    "market_id": market_id,
                    "outcome_id": outcome_id,
                    "bids": orderbook_data.get("bids", None),
                    "asks": orderbook_data.get("asks", None),
                    "timestamp": orderbook_data.get(
                        "timestamp", datetime.now().isoformat()
                    ),
                }
            else:
                raise RuntimeError(f"API returned status code: {response.status_code}")
        except Exception as e:
            raise RuntimeError(f"Orderbook API failed: {e}")

    def fetch_trades(self, market_id: str, limit: int = 100) -> list[dict]:
        """
        Fetch recent trades for a specific market.
        Args:
            market_id: The unique identifier for the market.
            limit: Maximum number of trades to return.
        Returns:
            List of recent trades with price and volume information.
        Raises:
            RuntimeError: If the API request fails or returns invalid data.
        """
        try:
            url = (
                f"https://clob.polymarket.com/markets/{market_id}/trades?limit={limit}"
            )
            response = self.make_request(url, timeout=10)
            if response.status_code == 200:
                trades_data = self.safe_json_parse(response, "Polymarket trades API")
                if not isinstance(trades_data, list):
                    raise RuntimeError("Invalid trades data format")
                trades = []
                for trade in trades_data:
                    if isinstance(trade, dict):
                        trades.append(
                            {
                                "id": trade.get("id"),
                                "outcome_id": trade.get(
                                    "outcomeId", trade.get("outcome_id", None)
                                ),
                                "price": float(trade.get("price", None))
                                if trade.get("price") is not None
                                else None,
                                "size": float(trade.get("size", None))
                                if trade.get("size") is not None
                                else None,
                                "side": trade.get("side", None),
                                "timestamp": trade.get("timestamp", None),
                                "maker": trade.get("maker", None),
                                "taker": trade.get("taker", None),
                            }
                        )
                return trades
            else:
                raise RuntimeError(f"API returned status code: {response.status_code}")
        except Exception as e:
            raise RuntimeError(f"Trades API failed: {e}")

    def fetch_market_stats(self, market_id: str) -> dict:
        """
        Fetch market statistics and analytics.
        Args:
            market_id: The unique identifier for the market.
        Returns:
            Dictionary with market statistics including volume, liquidity, and price movements.
        Raises:
            RuntimeError: If the API request fails or returns invalid data.
        """
        try:
            market_details = self.fetch_market_details(market_id)
            recent_trades = self.fetch_trades(market_id, limit=100)
            total_volume_24h = sum(
                float(trade["size"])
                for trade in recent_trades
                if trade.get("size") is not None
            )
            if recent_trades:
                weighted_sum = sum(
                    float(trade["price"]) * float(trade["size"])
                    for trade in recent_trades
                    if trade.get("price") is not None and trade.get("size") is not None
                )
                total_size = sum(
                    float(trade["size"])
                    for trade in recent_trades
                    if trade.get("size") is not None
                )
                avg_price = weighted_sum / total_size if total_size > 0 else None
            else:
                avg_price = None
            if len(recent_trades) >= 2:
                latest_price = (
                    float(recent_trades[0]["price"])
                    if recent_trades[0].get("price") is not None
                    else None
                )
                oldest_price = (
                    float(recent_trades[-1]["price"])
                    if recent_trades[-1].get("price") is not None
                    else None
                )
                if latest_price is not None and oldest_price is not None:
                    price_change = latest_price - oldest_price
                    price_change_pct = (
                        (price_change / oldest_price * 100)
                        if oldest_price > 0
                        else None
                    )
                else:
                    price_change = None
                    price_change_pct = None
            else:
                price_change = None
                price_change_pct = None
            return {
                "market_id": market_id,
                "title": market_details.get("title", None),
                "total_volume_24h": total_volume_24h,
                "average_price": avg_price,
                "price_change": price_change,
                "price_change_percent": price_change_pct,
                "total_trades_24h": len(recent_trades),
                "outcomes_count": len(market_details.get("outcomes", [])),
                "market_status": market_details.get("status", None),
                "total_liquidity": market_details.get("total_liquidity", None),
            }
        except Exception as e:
            raise RuntimeError(f"Market stats calculation failed: {e}")

    def search_markets(
        self, query: str, category: str | None = None, limit: int = 50
    ) -> list[dict]:
        """
        Searches for markets based on a query string.
        Args:
            query: Search query string.
            category: Optional category filter.
            limit: Maximum number of results to return.
        Returns:
            list: List of markets matching the search criteria.
        """
        try:
            # Get all markets first
            all_markets = self.fetch_markets(category=category, limit=1000)
            # Filter by query
            query_lower = query.lower()
            matching_markets = []
            for market in all_markets:
                if isinstance(market, dict):
                    title = str(market.get("title", "")).lower()
                    description = str(market.get("description", "")).lower()
                    category_name = str(market.get("category", "")).lower()
                    if (
                        query_lower in title
                        or query_lower in description
                        or query_lower in category_name
                    ):
                        matching_markets.append(market)
            return matching_markets[:limit]
        except Exception as e:
            print(f"Search failed: {e}")
            # Return filtered mock data
            mock_markets = self._get_mock_markets()
            query_lower = query.lower()
            matching_markets = [
                market
                for market in mock_markets
                if query_lower in market["title"].lower()
                or query_lower in market["description"].lower()
                or query_lower in market["category"].lower()
            ]
            if category:
                matching_markets = [
                    market
                    for market in matching_markets
                    if category.lower() in market["category"].lower()
                ]
            return matching_markets[:limit]

    def fetch_trending_markets(self, limit: int = 10) -> list[dict]:
        """
        Fetches trending markets based on volume and activity.
        Args:
            limit: Maximum number of trending markets to return.
        Returns:
            list: List of trending markets sorted by activity.
        """
        try:
            # Get all markets
            all_markets = self.fetch_markets(limit=1000)
            # Sort by total volume (proxy for trending)
            trending_markets = sorted(
                all_markets,
                key=lambda x: float(x.get("total_volume", 0))
                if isinstance(x, dict)
                else 0,
                reverse=True,
            )
            return trending_markets[:limit]
        except Exception as e:
            print(f"Trending markets fetch failed: {e}")
            # Return mock trending markets
            mock_markets = self._get_mock_markets()
            # Sort by volume for mock trending
            trending_markets = sorted(
                mock_markets, key=lambda x: x["total_volume"], reverse=True
            )
            return trending_markets[:limit]

    def fetch(self, mode: str, **kwargs):
        """
        Unified fetch interface for PolymarketFetcher.

        Args:
            mode (str): The type of data to fetch. One of: 'markets', 'market_details', 'orderbook', 'trades', 'market_stats'.
            **kwargs: Arguments for the specific fetch method.
                - For 'markets': category (str, optional), limit (int, optional)
                - For 'market_details': market_id (str, required)
                - For 'orderbook': market_id (str, required), outcome_id (str, optional)
                - For 'trades': market_id (str, required), limit (int, optional)
                - For 'market_stats': market_id (str, required)

        Returns:
            Any: The result of the corresponding fetch method.

        Raises:
            ValueError: If mode is not recognized or required arguments are missing.
        """
        if mode == "markets":
            return self.fetch_markets(
                category=kwargs.get("category"), limit=kwargs.get("limit", 50)
            )
        elif mode == "market_details":
            if "market_id" not in kwargs:
                raise ValueError("market_id is required for market_details")
            return self.fetch_market_details(kwargs["market_id"])
        elif mode == "orderbook":
            if "market_id" not in kwargs:
                raise ValueError("market_id is required for orderbook")
            return self.fetch_orderbook(
                market_id=kwargs["market_id"], outcome_id=kwargs.get("outcome_id")
            )
        elif mode == "trades":
            if "market_id" not in kwargs:
                raise ValueError("market_id is required for trades")
            return self.fetch_trades(
                market_id=kwargs["market_id"], limit=kwargs.get("limit", 100)
            )
        elif mode == "market_stats":
            if "market_id" not in kwargs:
                raise ValueError("market_id is required for market_stats")
            return self.fetch_market_stats(kwargs["market_id"])
        else:
            raise ValueError(f"Unknown fetch mode: {mode}")


def fetch_polymarket_markets(
    category: str | None = None, limit: int = 50
) -> list[dict]:
    """Backward compatibility function."""
    fetcher = PolymarketFetcher()
    return fetcher.fetch_markets(category, limit)


def fetch_polymarket_market_details(market_id: str) -> dict:
    """Backward compatibility function."""
    fetcher = PolymarketFetcher()
    return fetcher.fetch_market_details(market_id)


def fetch_polymarket_orderbook(market_id: str, outcome_id: str | None = None) -> dict:
    """Backward compatibility function."""
    fetcher = PolymarketFetcher()
    return fetcher.fetch_orderbook(market_id, outcome_id)


def fetch_polymarket_trades(market_id: str, limit: int = 100) -> list[dict]:
    """Backward compatibility function."""
    fetcher = PolymarketFetcher()
    return fetcher.fetch_trades(market_id, limit)


def fetch_polymarket_market_stats(market_id: str) -> dict:
    """Backward compatibility function."""
    fetcher = PolymarketFetcher()
    return fetcher.fetch_market_stats(market_id)


def search_polymarket_markets(
    query: str, category: str | None = None, limit: int = 50
) -> list[dict]:
    """Backward compatibility function."""
    fetcher = PolymarketFetcher()
    return fetcher.search_markets(query, category, limit)


def fetch_polymarket_trending_markets(limit: int = 10) -> list[dict]:
    """Backward compatibility function."""
    fetcher = PolymarketFetcher()
    return fetcher.fetch_trending_markets(limit)
