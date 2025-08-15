"""
Polymarket data fetcher for trading bench (simplified).

Exports:
1) PolymarketFetcher         - Core fetcher class
2) fetch_trending_markets()  - Convenience wrapper
3) fetch_current_market_price() - Convenience wrapper
4) fetch_token_price()       - Convenience wrapper
"""

from typing import Dict, List, Optional, Any

from trading_bench.fetchers.base_fetcher import BaseFetcher


class PolymarketFetcher(BaseFetcher):
    """Fetcher for Polymarket prediction market data."""

    def __init__(self, min_delay: float = 0.5, max_delay: float = 1.5):
        super().__init__(min_delay, max_delay)

    def fetch(self, mode: str, **kwargs):
        """
        Minimal unified fetch interface.

        Args:
            mode: 'trending_markets' | 'market_price' | 'token_price'
        """
        if mode == "trending_markets":
            return self.get_trending_markets(limit=kwargs.get("limit", 10))
        if mode == "market_price":
            token_ids = kwargs.get("token_ids")
            if not token_ids:
                raise ValueError("token_ids is required for market_price")
            return self.get_market_prices(token_ids)
        if mode == "token_price":
            token_id = kwargs.get("token_id")
            if not token_id:
                raise ValueError("token_id is required for token_price")
            return {
                "token_id": token_id,
                "side": kwargs.get("side", "buy"),
                "price": self.get_token_price(token_id, kwargs.get("side", "buy")),
            }
        raise ValueError(f"Unknown fetch mode: {mode}")

    # ----------------------------
    # Core methods (no mocks)
    # ----------------------------
    def get_trending_markets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Return basic info for active, open markets.

        Note: API may return a list or an object with a 'data' field.
        """
        url = "https://gamma-api.polymarket.com/markets?active=true&closed=false"
        resp = self.make_request(url, timeout=10)
        if resp.status_code != 200:
            raise ValueError(f"Polymarket markets API error: {resp.status_code}")

        data = self.safe_json_parse(resp, "Polymarket markets API")
        markets = data.get("data", data) if isinstance(data, dict) else data
        if not isinstance(markets, list):
            return []

        out: List[Dict[str, Any]] = []
        for m in markets:
            if not isinstance(m, dict):
                continue
            if m.get("active") is False or m.get("closed") is True:
                continue
            # Parse token_ids - handle both list and string formats
            token_ids = m.get("clobTokenIds")
            if isinstance(token_ids, str):
                try:
                    import json
                    token_ids = json.loads(token_ids)
                except (json.JSONDecodeError, TypeError):
                    token_ids = None
            
            out.append(
                {
                    "id": m.get("id"),
                    "question": m.get("question"),
                    "category": m.get("category"),
                    "token_ids": token_ids if isinstance(token_ids, list) else None,
                }
            )
            if len(out) >= limit:
                break
        return out

    def get_token_price(self, token_id: str, side: str = "buy") -> Optional[float]:
        """
        Return current price for a token on the given side, or None if unavailable.
        """
        url = f"https://clob.polymarket.com/price?token_id={token_id}&side={side}"
        resp = self.make_request(url, timeout=8)
        if resp.status_code != 200:
            return None
        payload = self.safe_json_parse(resp, f"Token {token_id} {side} price")
        price = payload.get("price") if isinstance(payload, dict) else None
        try:
            return float(price) if price is not None else None
        except (TypeError, ValueError):
            return None

    def get_market_prices(self, token_ids: List[str]) -> Dict[str, Optional[float]]:
        """
        Return a dict of prices for given token_ids.

        Keys:
          - Each token_id as-is maps to its price (or None).
          - Positional aliases: "token_0", "token_1", ...
          - If exactly two tokens, also add "yes" := token_0, "no" := token_1
            (kept for backward compatibility; **does not** infer actual YES/NO semantics).
        """
        prices: Dict[str, Optional[float]] = {}
        for idx, tid in enumerate(token_ids):
            if not tid:
                continue
            # Try buy first, then sell
            price = self.get_token_price(tid, "buy")
            if price is None:
                price = self.get_token_price(tid, "sell")
            prices[tid] = price
            prices[f"token_{idx}"] = price

        if len(token_ids) == 2:
            prices["yes"] = prices.get("token_0")
            prices["no"] = prices.get("token_1")
        return prices


# ----------------------------
# Convenience wrappers
# ----------------------------
def fetch_trending_markets(limit: int = 10) -> List[Dict[str, Any]]:
    return PolymarketFetcher().get_trending_markets(limit=limit)


def fetch_current_market_price(token_ids: List[str]) -> Dict[str, Optional[float]]:
    return PolymarketFetcher().get_market_prices(token_ids)


def fetch_token_price(token_id: str, side: str = "buy") -> Optional[float]:
    return PolymarketFetcher().get_token_price(token_id, side)
