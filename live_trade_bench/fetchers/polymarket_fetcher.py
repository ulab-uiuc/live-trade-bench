"""
Polymarket data fetcher for trading bench (simplified).

Exports:
1) PolymarketFetcher         - Core fetcher class
2) fetch_trending_markets()  - Convenience wrapper
3) fetch_current_market_price() - Convenience wrapper
4) fetch_token_price()       - Convenience wrapper
"""

from typing import Any, Dict, List, Optional

from live_trade_bench.fetchers.base_fetcher import BaseFetcher


class PolymarketFetcher(BaseFetcher):
    # Global token_id to market info mapping
    _token_market_map: Dict[str, Dict[str, Any]] = {}

    def __init__(self, min_delay: float = 0.5, max_delay: float = 1.5):
        super().__init__(min_delay, max_delay)

    def fetch(self, mode: str, **kwargs):
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

    def get_trending_markets(self, limit: int = 10) -> List[Dict[str, Any]]:
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

            market_info = {
                "id": m.get("id"),
                "question": m.get("question"),
                "category": m.get("category"),
                "token_ids": token_ids if isinstance(token_ids, list) else None,
            }
            out.append(market_info)

            # Update global token mapping
            if token_ids and isinstance(token_ids, list):
                for token_id in token_ids:
                    if token_id:
                        PolymarketFetcher._token_market_map[token_id] = {
                            "market_id": m.get("id"),
                            "question": m.get("question"),
                            "category": m.get("category"),
                        }
            if len(out) >= limit:
                break
        return out

    def get_token_price(self, token_id: str, side: str = "buy") -> Optional[float]:
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

    @classmethod
    def get_market_info_by_token(cls, token_id: str) -> Optional[Dict[str, Any]]:
        """Get market info (question, category) from token_id."""
        return cls._token_market_map.get(token_id)

    def get_market_prices(self, token_ids: List[str]) -> Dict[str, Any]:
        prices: Dict[str, Any] = {}

        # Get prices
        for idx, tid in enumerate(token_ids):
            if not tid:
                continue
            # Try buy first, then sell
            price = self.get_token_price(tid, "buy")
            if price is None:
                price = self.get_token_price(tid, "sell")
            prices[tid] = price
            prices[f"token_{idx}"] = price

        # Add yes/no mapping for binary markets
        if len(token_ids) == 2:
            prices["yes"] = prices.get("token_0")
            prices["no"] = prices.get("token_1")

        # Add market info from token mapping
        if token_ids:
            first_token = token_ids[0]
            market_info = self.get_market_info_by_token(first_token)
            if market_info:
                prices["question"] = market_info.get("question")
                prices["category"] = market_info.get("category")
                prices["market_id"] = market_info.get("market_id")

        return prices


# ----------------------------
# Convenience wrappers
# ----------------------------
def fetch_trending_markets(limit: int = 10) -> List[Dict[str, Any]]:
    markets = PolymarketFetcher().get_trending_markets(limit=limit)
    valid_markets = [m for m in markets if m.get("token_ids")]
    print(f"📊 Fetched {len(valid_markets)} markets")
    return valid_markets


def fetch_current_market_price(token_ids: List[str]) -> Dict[str, Any]:
    prices = PolymarketFetcher().get_market_prices(token_ids)
    if prices and "yes" in prices:
        question = prices.get("question")
        if question:
            question_short = question[:40] + "..." if len(question) > 40 else question
            print(f"💰 {question_short}")
            print(
                f"   YES: {prices['yes']:.3f} | NO: {prices.get('no', 1-prices['yes']):.3f}"
            )
        else:
            print(
                f"💰 YES: {prices['yes']:.3f} | NO: {prices.get('no', 1-prices['yes']):.3f}"
            )
    return prices


def fetch_token_price(token_id: str, side: str = "buy") -> Optional[float]:
    price = PolymarketFetcher().get_token_price(token_id, side)
    market_info = PolymarketFetcher.get_market_info_by_token(token_id)

    if price:
        if market_info and market_info.get("question"):
            question_short = (
                market_info["question"][:30] + "..."
                if len(market_info["question"]) > 30
                else market_info["question"]
            )
            print(f"🪙 {question_short}: {price:.4f}")
        else:
            print(f"🪙 Token price: {price:.4f}")
    return price


def get_question_by_token_id(token_id: str) -> Optional[str]:
    """Get market question by token_id from global mapping."""
    market_info = PolymarketFetcher.get_market_info_by_token(token_id)
    return market_info.get("question") if market_info else None
