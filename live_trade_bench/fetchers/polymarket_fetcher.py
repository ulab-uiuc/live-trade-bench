from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from live_trade_bench.fetchers.base_fetcher import BaseFetcher


class PolymarketFetcher(BaseFetcher):
    _token_market_map: Dict[str, Dict[str, Any]] = {}

    def __init__(self, min_delay: float = 0.5, max_delay: float = 1.5):
        super().__init__(min_delay, max_delay)

    def fetch(
        self, mode: str, **kwargs: Any
    ) -> Union[List[Dict[str, Any]], Dict[str, Any], Optional[float]]:
        if mode == "trending_markets":
            return self.get_trending_markets(
                limit=kwargs.get("limit", 10), for_date=kwargs.get("for_date")
            )
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

    def get_trending_markets(
        self, limit: int = 10, for_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if for_date:
            return self._get_historical_markets(limit, for_date)
        return self._get_live_trending_markets(limit)

    def _get_live_trending_markets(self, limit: int) -> List[Dict[str, Any]]:
        url = "https://gamma-api.polymarket.com/markets?active=true&closed=false"
        resp = self.make_request(url, timeout=10)
        if resp.status_code != 200:
            raise ValueError(f"Polymarket markets API error: {resp.status_code}")
        data = self.safe_json_parse(resp, "Polymarket markets API")
        markets = data.get("data", data) if isinstance(data, dict) else data
        return self._process_markets(markets, limit)

    def _get_historical_markets(
        self, limit: int, date_str: str
    ) -> List[Dict[str, Any]]:
        url = "https://gamma-api.polymarket.com/markets"

        # Format date for the API query
        start_of_day_utc = f"{date_str}T00:00:00Z"
        end_of_day_utc = f"{date_str}T23:59:59Z"

        params = {
            "start_date_max": end_of_day_utc,
            "end_date_min": start_of_day_utc,
            "limit": 100,  # Fetch more to find active ones
        }

        resp = self.make_request(url, params=params, timeout=15)
        if resp.status_code != 200:
            raise ValueError(f"Polymarket markets API error: {resp.status_code}")

        data = self.safe_json_parse(resp, "Polymarket markets API")
        all_markets = data.get("data", data) if isinstance(data, dict) else data
        return self._process_markets(all_markets, limit)

    def get_historical_markets_for_period(
        self, start_date_str: str, end_date_str: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        url = "https://gamma-api.polymarket.com/markets"

        start_utc = f"{start_date_str}T00:00:00Z"
        end_utc = f"{end_date_str}T23:59:59Z"

        params = {
            "start_date_max": end_utc,
            "end_date_min": start_utc,
            "limit": limit,
        }

        resp = self.make_request(url, params=params, timeout=15)
        if resp.status_code != 200:
            raise ValueError(f"Polymarket markets API error: {resp.status_code}")

        data = self.safe_json_parse(resp, "Polymarket markets API")
        all_markets = data.get("data", data) if isinstance(data, dict) else data
        return self._process_markets(all_markets, limit)

    def get_verified_historical_markets(
        self, trading_days: List[datetime], limit: int
    ) -> List[Dict[str, Any]]:
        if not trading_days:
            return []

        start_date_str = trading_days[0].strftime("%Y-%m-%d")
        end_date_str = trading_days[-1].strftime("%Y-%m-%d")

        candidate_markets = self.get_historical_markets_for_period(
            start_date_str, end_date_str, limit=limit * 10
        )
        print(
            f"--- Found {len(candidate_markets)} candidate markets. Verifying price history for each day... ---"
        )

        verified_markets = []
        for market in candidate_markets:
            token_ids = market.get("token_ids")
            if not token_ids:
                continue

            has_all_days = True
            for day in trading_days:
                date_str = day.strftime("%Y-%m-%d")
                price = self.get_market_price_on_date(token_ids[0], date_str)
                if price is None:
                    has_all_days = False
                    question = market.get("question", market["id"])
                    print(
                        f"    - ❌ Market '{question[:30]}...' is missing data on {date_str}. Discarding."
                    )
                    break

            if has_all_days:
                question = market.get("question", market["id"])
                print(
                    f"    - ✅ Market '{question[:30]}...' has complete history. Adding to universe."
                )
                verified_markets.append(market)
                if len(verified_markets) >= limit:
                    break

        return verified_markets

    def _process_markets(
        self, markets: List[Dict[str, Any]], limit: int
    ) -> List[Dict[str, Any]]:
        if not isinstance(markets, list):
            return []

        out: List[Dict[str, Any]] = []
        for m in markets:
            if not isinstance(m, dict):
                continue

            token_ids = self._parse_token_ids(m)
            if not token_ids:
                continue

            market_info = self._format_market_info(m, token_ids)
            out.append(market_info)
            self._map_tokens_to_market(m, token_ids)

            if len(out) >= limit:
                break
        return out

    def _parse_token_ids(self, market_data: Dict[str, Any]) -> Optional[List[str]]:
        token_ids = market_data.get("clobTokenIds")
        if isinstance(token_ids, str):
            try:
                import json

                return json.loads(token_ids)
            except (json.JSONDecodeError, TypeError):
                return None
        return token_ids if isinstance(token_ids, list) else None

    def _format_market_info(
        self, market_data: Dict[str, Any], token_ids: Optional[List[str]]
    ) -> Dict[str, Any]:
        return {
            "id": market_data.get("id"),
            "question": market_data.get("question"),
            "category": market_data.get("category"),
            "token_ids": token_ids,
        }

    def _map_tokens_to_market(self, market_data: Dict[str, Any], token_ids: List[str]):
        for token_id in token_ids:
            if token_id:
                PolymarketFetcher._token_market_map[token_id] = {
                    "market_id": market_data.get("id"),
                    "question": market_data.get("question"),
                    "category": market_data.get("category"),
                }

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
        return cls._token_market_map.get(token_id)

    def get_market_prices(self, token_ids: List[str]) -> Dict[str, Any]:
        prices: Dict[str, Any] = {}
        for idx, tid in enumerate(token_ids):
            if not tid:
                continue
            price = self.get_token_price(tid, "buy")
            if price is None:
                price = self.get_token_price(tid, "sell")
            prices[tid] = price
            prices[f"token_{idx}"] = price
        if len(token_ids) == 2:
            prices["yes"] = prices.get("token_0")
            prices["no"] = prices.get("token_1")
        if token_ids:
            first_token = token_ids[0]
            market_info = self.get_market_info_by_token(first_token)
            if market_info:
                prices["question"] = market_info.get("question")
                prices["category"] = market_info.get("category")
                prices["market_id"] = market_info.get("market_id")
        return prices

    def get_market_price_on_date(self, token_id: str, date: str) -> Optional[float]:
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
            start_ts = int(dt.timestamp())
            end_ts = int((dt.replace(hour=23, minute=59, second=59)).timestamp())

            url = "https://clob.polymarket.com/prices-history"
            params = {
                "market": token_id,
                "startTs": start_ts,
                "endTs": end_ts,
                "fidelity": 60,
            }

            resp = self.make_request(url, params=params, timeout=10)
            if resp.status_code != 200:
                return None

            data = self.safe_json_parse(resp, f"Market {token_id} history")
            history = data.get("history")

            if not history:
                return None

            closest_point = min(history, key=lambda p: abs(end_ts - p["t"]))

            price = float(closest_point["p"])
            if price > 1.0:
                price /= 100.0

            return price

        except Exception:
            # Silencing the error for verification purposes, as many will fail
            # print(f"Error fetching historical data for token {token_id} on {date}: {e}")
            return None


def fetch_trending_markets(
    limit: int = 10, for_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    fetcher = PolymarketFetcher()
    markets = fetcher.get_trending_markets(limit=limit, for_date=for_date)
    valid_markets = [m for m in markets if m.get("token_ids")]
    print(
        f"📊 Fetched {len(valid_markets)} valid markets for date {for_date or 'today'}"
    )
    return valid_markets


def fetch_verified_historical_markets(
    trading_days: List[datetime], limit: int
) -> List[Dict[str, Any]]:
    fetcher = PolymarketFetcher()
    return fetcher.get_verified_historical_markets(trading_days, limit)


def fetch_current_market_price(token_ids: List[str]) -> Dict[str, Any]:
    prices = PolymarketFetcher().get_market_prices(token_ids)
    if prices and prices.get("yes") is not None:
        question = prices.get("question")
        yes_price = prices["yes"]
        no_price = prices.get("no")

        if no_price is None:
            no_price = 1.0 - yes_price

        if question:
            question_short = question[:40] + "..." if len(question) > 40 else question
            print(f"💰 {question_short}")
            print(f"   YES: {yes_price:.3f} | NO: {no_price:.3f}")
        else:
            print(f"💰 YES: {yes_price:.3f} | NO: {no_price:.3f}")

        return {
            "price": yes_price,
            "yes_price": yes_price,
            "no_price": no_price,
            "timestamp": datetime.now().isoformat(),
        }
    return {}


def fetch_market_price_on_date(
    token_ids: List[str], date: str
) -> Optional[Dict[str, Any]]:
    if not token_ids:
        return None

    fetcher = PolymarketFetcher()
    yes_token_id = token_ids[0]

    price = fetcher.get_market_price_on_date(yes_token_id, date)

    if price is not None:
        return {
            "price": price,
            "yes_price": price,
            "no_price": 1.0 - price,
            "timestamp": datetime.strptime(date, "%Y-%m-%d").isoformat(),
        }
    return None


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
    market_info = PolymarketFetcher.get_market_info_by_token(token_id)
    return market_info.get("question") if market_info else None
