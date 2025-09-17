from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from live_trade_bench.fetchers.base_fetcher import BaseFetcher


class PolymarketFetcher(BaseFetcher):
    def __init__(self, min_delay: float = 0.3, max_delay: float = 1.0):
        super().__init__(min_delay, max_delay)
        # Simple cache for backtest data
        self._cache: Dict[str, List[Dict[str, Any]]] = {}

    def fetch(
        self, mode: str, **kwargs: Any
    ) -> Union[List[Dict[str, Any]], Dict[str, Any], Optional[float]]:
        if mode == "trending_markets":
            return self.get_trending_markets(
                limit=int(kwargs.get("limit", 10)), for_date=kwargs.get("for_date")
            )
        elif mode == "token_price":
            token_id = kwargs.get("token_id")
            if token_id is None:
                raise ValueError("token_id is required for token_price")
            return self.get_price(
                token_id=str(token_id),
                date=kwargs.get("date"),
                side=kwargs.get("side", "buy"),
            )
        elif mode == "price_with_history":
            token_id = kwargs.get("token_id")
            if token_id is None:
                raise ValueError("token_id is required for price_with_history")
            return self.get_price_with_history(
                token_id=str(token_id),
                date=kwargs.get("date"),
                side=kwargs.get("side", "buy"),
            )
        elif mode == "verified_markets":
            trading_days = kwargs.get("trading_days")
            limit = int(kwargs.get("limit", 20))
            if not trading_days:
                return []
            return self.get_verified_markets(trading_days, limit=limit)
        else:
            raise ValueError(f"Unknown fetch mode: {mode}")

    def get_trending_markets(
        self, limit: int = 10, for_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"limit": limit}
        if for_date:
            params.update(
                {
                    "start_date_max": f"{for_date}T23:59:59Z",
                    "end_date_min": f"{for_date}T00:00:00Z",
                }
            )
        else:
            params.update({"active": "true", "closed": "false"})
        markets = self._fetch_markets(params)
        out: List[Dict[str, Any]] = []
        for m in markets[:limit]:
            if isinstance(m, dict) and m.get("id"):
                # Generate real URL from slug if available
                url = m.get("url")
                if not url and m.get("slug"):
                    url = f"https://polymarket.com/event/{m.get('slug')}"

                out.append(
                    {
                        "id": m.get("id"),
                        "question": m.get("question"),
                        "category": m.get("category"),
                        "token_ids": m.get("clobTokenIds", []),
                        "slug": m.get("slug"),
                        "url": url,
                    }
                )
        return out

    def get_verified_markets(
        self, trading_days: List[datetime], limit: int
    ) -> List[Dict[str, Any]]:
        if not trading_days:
            return []
        start_date = trading_days[0].strftime("%Y-%m-%d")
        end_date = trading_days[-1].strftime("%Y-%m-%d")
        params = {
            "start_date_max": f"{end_date}T23:59:59Z",
            "end_date_min": f"{start_date}T00:00:00Z",
            "limit": max(limit * 10, 100),
        }
        markets = self._fetch_markets(params)
        verified: List[Dict[str, Any]] = []
        for m in markets[::6]:
            if not isinstance(m, dict) or not m.get("id"):
                continue
            raw_token_ids = m.get("clobTokenIds", [])
            raw_outcomes = m.get("outcomes", [])
            if isinstance(raw_token_ids, str):
                try:
                    import json

                    token_ids = json.loads(raw_token_ids)
                    outcomes = json.loads(raw_outcomes)
                except Exception:
                    token_ids = []
                    outcomes = []
            else:
                token_ids = raw_token_ids
                outcomes = raw_outcomes
            if not token_ids:
                continue
            has_price_data = False
            for token_id in token_ids[:1]:
                if token_id:
                    history = self._fetch_daily_history(
                        token_id, start_date, end_date, fidelity=900
                    )
                    if history:
                        has_price_data = True
                        break
            if has_price_data:
                # Generate real URL from slug if available
                url = m.get("url")
                if not url and m.get("slug"):
                    url = f"https://polymarket.com/event/{m.get('slug')}"

                verified.append(
                    {
                        "id": m.get("id"),
                        "question": m.get("question"),
                        "category": m.get("category"),
                        "token_ids": token_ids,
                        "outcomes": outcomes,
                        "slug": m.get("slug"),
                        "url": url,
                    }
                )
            if len(verified) >= limit:
                break
        return verified

    def get_price(
        self, token_id: str, date: Optional[str] = None, side: str = "buy"
    ) -> Optional[float]:
        if date:
            return self._get_price_on_date(token_id, date)
        return self._get_current_price(token_id, side=side)

    def get_price_with_history(
        self,
        token_id: str,
        date: Optional[str] = None,
        side: str = "buy",
        backtest_start: Optional[str] = None,
        backtest_end: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Determine date range
        if date:
            end_date = date
            start_date = (
                datetime.strptime(date, "%Y-%m-%d") - timedelta(days=10)
            ).strftime("%Y-%m-%d")
        else:
            today = datetime.now(timezone.utc)
            end_date = today.strftime("%Y-%m-%d")
            start_date = (today - timedelta(days=10)).strftime("%Y-%m-%d")

        # Backtest mode with caching
        if backtest_start and backtest_end and date:
            cache_key = f"{token_id}_{backtest_start}_{backtest_end}"

            # Cache entire period on first call
            if cache_key not in self._cache:
                print(f"🚀 Caching {token_id} from {backtest_start} to {backtest_end}")
                cache_start = (
                    datetime.strptime(backtest_start, "%Y-%m-%d") - timedelta(days=15)
                ).strftime("%Y-%m-%d")
                self._cache[cache_key] = self._fetch_daily_history(
                    token_id, cache_start, backtest_end, fidelity=900
                )

            # Get price and history from cache (use previous day's price for backtest)
            cached_data = self._cache[cache_key]

            # For backtest: use previous day's price to avoid data leakage
            previous_day = (
                datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)
            ).strftime("%Y-%m-%d")
            current_price = next(
                (
                    float(item["price"])
                    for item in cached_data
                    if item["date"] == previous_day
                ),
                None,
            )

            # History should only include data up to previous day (not including current day)
            history = [item for item in cached_data if item["date"] < date][-10:]
        else:
            # Regular mode: fetch data on demand
            history = self._fetch_daily_history(
                token_id, start_date, end_date, fidelity=900
            )

            # Get current price
            if date:
                current_price = next(
                    (float(item["price"]) for item in history if item["date"] == date),
                    self._get_price_on_date(token_id, date),
                )
            else:
                current_price = self._get_current_price(token_id, side=side)

        return {
            "current_price": current_price,
            "price_history": [
                {"date": h["date"], "price": h["price"]} for h in history
            ],
            "token_id": token_id,
        }

    def _fetch_markets(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        url = "https://gamma-api.polymarket.com/markets"
        try:
            resp = self.make_request(url, params=params, timeout=15)
            if resp.status_code == 200:
                data = self.safe_json_parse(resp, "Markets API")
                return data.get("data", []) if isinstance(data, dict) else (data or [])
        except Exception:
            pass
        return []

    def _get_current_price(self, token_id: str, side: str = "buy") -> Optional[float]:
        url = "https://clob.polymarket.com/price"
        try:
            resp = self.make_request(
                url, params={"token_id": token_id, "side": side}, timeout=8
            )
            if resp.status_code == 200:
                data = self.safe_json_parse(resp, f"Token {token_id} price")
                price = data.get("price") if isinstance(data, dict) else None
                if price is not None:
                    price = float(price)
                    return price / 100.0 if price > 1.0 else price
        except Exception:
            pass
        return None

    def _fetch_daily_history(
        self, token_id: str, start_date: str, end_date: str, fidelity: int = 900
    ) -> List[Dict[str, Any]]:
        url = "https://clob.polymarket.com/prices-history"
        cur = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        day_closes: Dict[str, Tuple[int, float]] = {}
        while cur <= end:
            day_start = int(cur.replace(hour=0, minute=0, second=0).timestamp())
            day_end = int(cur.replace(hour=23, minute=59, second=59).timestamp())
            try:
                resp = self.make_request(
                    url,
                    params={
                        "market": token_id,
                        "startTs": day_start,
                        "endTs": day_end,
                        "fidelity": fidelity,
                    },
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = self.safe_json_parse(resp, f"History for {token_id}")
                    points = data.get("history", []) if isinstance(data, dict) else []
                    for p in points:
                        if not (isinstance(p, dict) and "t" in p and "p" in p):
                            continue
                        ts = int(p["t"])
                        dstr = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
                        price = float(p["p"])
                        if price > 1.0:
                            price /= 100.0
                        prev = day_closes.get(dstr)
                        if prev is None or ts > prev[0]:
                            day_closes[dstr] = (ts, price)
            except Exception:
                pass
            cur += timedelta(days=1)
        out = [
            {"date": d, "price": pr, "token_id": token_id}
            for d, (_ts, pr) in day_closes.items()
        ]
        out.sort(key=lambda x: x["date"])
        return out

    def _get_price_on_date(self, token_id: str, date: str) -> Optional[float]:
        try:
            hist = self._fetch_daily_history(token_id, date, date, fidelity=900)
            if hist:
                return float(hist[-1]["price"])
        except Exception:
            pass
        return None


def fetch_trending_markets(
    limit: int = 10, for_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    return PolymarketFetcher().get_trending_markets(limit=limit, for_date=for_date)


def fetch_verified_markets(
    trading_days: List[datetime], limit: int
) -> List[Dict[str, Any]]:
    return PolymarketFetcher().get_verified_markets(trading_days, limit=limit)


# Global fetcher instance for sharing cache across calls
_global_fetcher: Optional[PolymarketFetcher] = None


def fetch_market_price_with_history(
    token_id: str,
    date: Optional[str] = None,
    side: str = "buy",
    backtest_start: Optional[str] = None,
    backtest_end: Optional[str] = None,
) -> Dict[str, Any]:
    global _global_fetcher
    if _global_fetcher is None:
        _global_fetcher = PolymarketFetcher()

    return _global_fetcher.get_price_with_history(
        token_id,
        date=date,
        side=side,
        backtest_start=backtest_start,
        backtest_end=backtest_end,
    )


def clear_global_cache():
    """Clear the global fetcher cache. Useful for testing or memory management."""
    global _global_fetcher
    if _global_fetcher is not None:
        _global_fetcher._cache.clear()
        print("🧹 Global fetcher cache cleared")
