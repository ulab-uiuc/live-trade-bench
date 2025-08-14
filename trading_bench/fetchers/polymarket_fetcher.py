"""
Polymarket data fetcher for trading bench.

This module provides:
1. PolymarketFetcher class - Core fetcher class with methods
2. fetch_trending_markets() - Standalone function using the class
3. fetch_current_market_price() - Standalone function using the class
"""

from typing import Dict, List

from trading_bench.fetchers.base_fetcher import BaseFetcher


class PolymarketFetcher(BaseFetcher):
    """Fetcher for Polymarket prediction market data."""

    def __init__(self, min_delay: float = 0.5, max_delay: float = 1.5):
        """Initialize the Polymarket fetcher."""
        super().__init__(min_delay, max_delay)

    def fetch(self, mode: str, **kwargs):
        """
        Unified fetch interface for PolymarketFetcher.

        Args:
            mode: The type of data to fetch ('trending_markets' or 'market_price')
            **kwargs: Arguments for the specific fetch method
        """
        if mode == "trending_markets":
            return self.get_trending_markets(limit=kwargs.get("limit", 10))
        elif mode == "market_price":
            if "market_id" not in kwargs:
                raise ValueError("market_id is required for market_price")
            return self.get_current_market_price(kwargs["market_id"])
        else:
            raise ValueError(f"Unknown fetch mode: {mode}")

    def get_trending_markets(self, limit: int = 10) -> List[Dict]:
        """
        Fetch trending markets from Polymarket API.

        Args:
            limit: Maximum number of markets to return

        Returns:
            List of dictionaries containing market basic info
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

                # Extract basic market info for trending markets
                trending_markets = []
                for market in markets_data:
                    if isinstance(market, dict) and market.get("active", False):
                        market_id = (
                            market.get("question_id")
                            or market.get("condition_id")
                            or market.get("market_slug")
                        )
                        if market_id:
                            trending_markets.append(
                                {
                                    "id": market_id,
                                    "title": market.get("question")
                                    or market.get("description", ""),
                                    "category": "prediction",  # Default category
                                }
                            )

                            if len(trending_markets) >= limit:
                                break

                return trending_markets

        except Exception as e:
            raise ValueError(f"Failed to fetch trending markets: {e}")

    def get_current_market_price(self, market_id: str) -> Dict[str, float]:
        """
        Fetch current price for a specific market.

        Args:
            market_id: The market ID to fetch price for

        Returns:
            Dictionary with yes/no prices
        """
        try:
            # Try to get detailed market info
            url = f"https://clob.polymarket.com/markets/{market_id}"
            response = self.make_request(url, timeout=10)

            if response.status_code == 200:
                market_data = self.safe_json_parse(
                    response, f"Market {market_id} details"
                )

                # Extract yes/no prices from outcomes
                prices = {"yes": 0.5, "no": 0.5}  # Default prices

                for outcome in market_data.get("outcomes", []):
                    if isinstance(outcome, dict):
                        outcome_name = outcome.get("name", "").lower()
                        price = float(outcome.get("current_price", 0.5) or 0.5)

                        if any(word in outcome_name for word in ["yes", "true", "win"]):
                            prices["yes"] = price
                        elif any(
                            word in outcome_name for word in ["no", "false", "lose"]
                        ):
                            prices["no"] = price

                return prices

        except Exception as e:
            raise ValueError(f"Failed to fetch price for market {market_id}: {e}")

    def _get_mock_markets(self) -> List[Dict]:
        """Generate mock market data for testing/fallback purposes."""
        return [
            {
                "id": "election_2024",
                "title": "Will Democrats win the 2024 US Presidential Election?",
                "category": "politics",
            },
            {
                "id": "agi_2025",
                "title": "Will AGI be achieved by 2025?",
                "category": "tech",
            },
            {
                "id": "climate_2024",
                "title": "Will CO2 emissions decrease by 5% in 2024?",
                "category": "economics",
            },
            {
                "id": "crypto_btc_100k",
                "title": "Will Bitcoin reach $100K by end of 2024?",
                "category": "crypto",
            },
            {
                "id": "superbowl_2024",
                "title": "Will the Super Bowl have over 60 points scored?",
                "category": "sports",
            },
        ]

    def _get_mock_price(self, market_id: str) -> Dict[str, float]:
        """Generate mock price data based on market_id."""
        if "election" in market_id:
            return {"yes": 0.52, "no": 0.48}
        elif "agi" in market_id:
            return {"yes": 0.25, "no": 0.75}
        elif "climate" in market_id:
            return {"yes": 0.30, "no": 0.70}
        elif "crypto" in market_id or "btc" in market_id:
            return {"yes": 0.35, "no": 0.65}
        elif "superbowl" in market_id or "sports" in market_id:
            return {"yes": 0.60, "no": 0.40}
        else:
            # Use hash-based consistent price for unknown markets
            # This ensures the same market_id always gets the same price
            import hashlib

            hash_value = int(hashlib.md5(market_id.encode()).hexdigest()[:8], 16)
            # Convert to a price between 0.2 and 0.8
            yes_price = round(0.2 + (hash_value % 1000) / 1000 * 0.6, 2)
            return {"yes": yes_price, "no": round(1.0 - yes_price, 2)}


# Standalone functions that use the class
def fetch_trending_markets(limit: int = 10) -> List[Dict]:
    """
    Fetch trending markets from Polymarket API.

    Args:
        limit: Maximum number of markets to return (default: 10)

    Returns:
        List of dictionaries containing market basic info
    """
    fetcher = PolymarketFetcher()
    markets = fetcher.get_trending_markets(limit=limit)
    print(f"📊 Fetched {len(markets)} trending markets")
    return markets


def fetch_current_market_price(market_id: str) -> Dict[str, float]:
    """
    Fetch current price for a specific market.

    Args:
        market_id: The market ID to fetch price for

    Returns:
        Dictionary with yes/no prices:
        {
            "yes": 0.52,
            "no": 0.48
        }
    """
    fetcher = PolymarketFetcher()
    return fetcher.get_current_market_price(market_id)
