"""
BitMEX API Fetcher for cryptocurrency derivatives data.

This module provides methods to fetch data from BitMEX exchange including
perpetual contracts, futures, spot prices, funding rates, and order book data.
"""

import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from .base_fetcher import BaseFetcher


class BitMEXFetcher(BaseFetcher):
    """Fetcher for BitMEX cryptocurrency derivatives exchange data."""

    BASE_URL = "https://www.bitmex.com/api/v1"
    TESTNET_URL = "https://testnet.bitmex.com/api/v1"

    # Popular trading pairs on BitMEX
    POPULAR_SYMBOLS = [
        "XBTUSD",    # Bitcoin Perpetual
        "ETHUSD",    # Ethereum Perpetual
        "XBTUSDT",   # Bitcoin/USDT Perpetual
        "ETHUSDT",   # Ethereum/USDT Perpetual
        "SOLUSDT",   # Solana/USDT Perpetual
        "BNBUSDT",   # BNB/USDT Perpetual
        "XRPUSDT",   # XRP/USDT Perpetual
        "ADAUSDT",   # Cardano/USDT Perpetual
        "DOGEUSDT",  # Dogecoin/USDT Perpetual
        "AVAXUSDT",  # Avalanche/USDT Perpetual
        "LINKUSDT",  # Chainlink/USDT Perpetual
        "LTCUSDT",   # Litecoin/USDT Perpetual
    ]

    def __init__(
        self,
        min_delay: float = 0.5,
        max_delay: float = 1.5,
        use_testnet: bool = False,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None
    ):
        """
        Initialize BitMEX fetcher.

        Args:
            min_delay: Minimum delay between API calls (seconds)
            max_delay: Maximum delay between API calls (seconds)
            use_testnet: Whether to use testnet API
            api_key: BitMEX API key (optional, from env if not provided)
            api_secret: BitMEX API secret (optional, from env if not provided)
        """
        super().__init__(min_delay, max_delay)

        self.base_url = self.TESTNET_URL if use_testnet else self.BASE_URL
        self.api_key = api_key or os.getenv("BITMEX_API_KEY")
        self.api_secret = api_secret or os.getenv("BITMEX_API_SECRET")

        # Update headers for BitMEX
        self.default_headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })

    def _generate_signature(self, verb: str, path: str, expires: int, data: str = "") -> str:
        """
        Generate HMAC-SHA256 signature for authenticated endpoints.

        Args:
            verb: HTTP method (GET, POST, etc.)
            path: API endpoint path
            expires: Expiration timestamp
            data: Request body data

        Returns:
            Hex-encoded signature
        """
        if not self.api_secret:
            raise ValueError("API secret required for authenticated endpoints")

        message = f"{verb}{path}{expires}{data}"
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _get_auth_headers(self, verb: str, path: str, data: str = "") -> Dict[str, str]:
        """
        Get authentication headers for protected endpoints.

        Args:
            verb: HTTP method
            path: API endpoint path
            data: Request body data

        Returns:
            Headers dict with authentication
        """
        if not self.api_key:
            return {}

        expires = int(time.time() + 60)  # 60 seconds from now
        signature = self._generate_signature(verb, path, expires, data)

        return {
            "api-key": self.api_key,
            "api-expires": str(expires),
            "api-signature": signature
        }

    def get_trending_contracts(self, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Get list of most actively traded contracts.

        Args:
            limit: Maximum number of contracts to return

        Returns:
            List of contract information dictionaries
        """
        # Get active instruments sorted by volume
        url = f"{self.base_url}/instrument/active"

        response = self.make_request(url)
        self.validate_response(response, "Get trending contracts")

        data = self.safe_json_parse(response, "Trending contracts")

        # Filter for perpetual and futures contracts, sort by volume
        contracts = []
        for instrument in data:
            if instrument.get("state") == "Open" and instrument.get("volume24h"):
                contracts.append({
                    "symbol": instrument["symbol"],
                    "type": instrument.get("typ", "Unknown"),
                    "underlying": instrument.get("underlying"),
                    "quote_currency": instrument.get("quoteCurrency"),
                    "volume_24h": instrument["volume24h"],
                    "last_price": instrument.get("lastPrice"),
                    "mark_price": instrument.get("markPrice"),
                    "funding_rate": instrument.get("fundingRate"),
                    "open_interest": instrument.get("openInterest"),
                    "state": instrument["state"]
                })

        # Sort by 24h volume and return top N
        contracts.sort(key=lambda x: x.get("volume_24h", 0), reverse=True)
        return contracts[:limit]

    def get_price(self, symbol: str, price_type: str = "mark") -> float:
        """
        Get current price for a contract.

        Args:
            symbol: Contract symbol (e.g., "XBTUSD")
            price_type: Type of price - "mark", "last", or "index"

        Returns:
            Current price as float
        """
        url = f"{self.base_url}/instrument"
        params = {"symbol": symbol}

        response = self.make_request(url, params=params)
        self.validate_response(response, f"Get price for {symbol}")

        data = self.safe_json_parse(response, f"Price data for {symbol}")

        if not data or len(data) == 0:
            raise ValueError(f"No data found for symbol {symbol}")

        instrument = data[0]

        # Return requested price type
        if price_type == "mark":
            price = instrument.get("markPrice")
        elif price_type == "last":
            price = instrument.get("lastPrice")
        elif price_type == "index":
            price = instrument.get("indicativeSettlePrice")
        else:
            raise ValueError(f"Invalid price_type: {price_type}")

        if price is None:
            raise ValueError(f"No {price_type} price available for {symbol}")

        return float(price)

    def get_price_history(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> List[Dict[str, Any]]:
        """
        Get historical price data for a contract.

        Args:
            symbol: Contract symbol
            start_date: Start date for history
            end_date: End date for history
            interval: Time interval (1m, 5m, 1h, 1d)

        Returns:
            List of OHLCV data points
        """
        url = f"{self.base_url}/trade/bucketed"

        # BitMEX expects ISO format timestamps
        params = {
            "symbol": symbol,
            "binSize": interval,
            "startTime": start_date.isoformat(),
            "endTime": end_date.isoformat(),
            "count": 500,  # Max 500 per request
            "reverse": False
        }

        response = self.make_request(url, params=params)
        self.validate_response(response, f"Get price history for {symbol}")

        data = self.safe_json_parse(response, f"Price history for {symbol}")

        # Format the response
        history = []
        for candle in data:
            history.append({
                "timestamp": candle["timestamp"],
                "date": candle["timestamp"][:10],  # Extract date portion
                "open": float(candle["open"]) if candle.get("open") else None,
                "high": float(candle["high"]) if candle.get("high") else None,
                "low": float(candle["low"]) if candle.get("low") else None,
                "close": float(candle["close"]) if candle.get("close") else None,
                "volume": int(candle["volume"]) if candle.get("volume") else 0,
                "trades": int(candle["trades"]) if candle.get("trades") else 0
            })

        return history

    def get_price_with_history(
        self,
        symbol: str,
        lookback_days: int = 10,
        price_type: str = "mark"
    ) -> Dict[str, Any]:
        """
        Get current price with historical data.

        Args:
            symbol: Contract symbol
            lookback_days: Number of days of history to fetch
            price_type: Type of current price to fetch

        Returns:
            Dictionary with current price and price history
        """
        # Get current price
        current_price = self.get_price(symbol, price_type)

        # Calculate date range for history
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=lookback_days)

        # Get historical data
        history = self.get_price_history(symbol, start_date, end_date, "1d")

        # Format history for consistency with other fetchers
        price_history = []
        for point in history:
            if point.get("close") is not None:
                price_history.append({
                    "date": point["date"],
                    "price": point["close"],
                    "volume": point.get("volume", 0)
                })

        return {
            "symbol": symbol,
            "current_price": current_price,
            "price_type": price_type,
            "price_history": price_history,
            "lookback_days": lookback_days
        }

    def get_funding_rate(self, symbol: str) -> Dict[str, Any]:
        """
        Get current and predicted funding rates for perpetual contracts.

        Args:
            symbol: Contract symbol

        Returns:
            Dictionary with funding rate information
        """
        url = f"{self.base_url}/instrument"
        params = {"symbol": symbol}

        response = self.make_request(url, params=params)
        self.validate_response(response, f"Get funding rate for {symbol}")

        data = self.safe_json_parse(response, f"Funding data for {symbol}")

        if not data or len(data) == 0:
            raise ValueError(f"No data found for symbol {symbol}")

        instrument = data[0]

        return {
            "symbol": symbol,
            "funding_rate": instrument.get("fundingRate") or 0.0,
            "funding_timestamp": instrument.get("fundingTimestamp"),
            "indicative_funding_rate": instrument.get("indicativeFundingRate") or 0.0,
            "funding_interval": instrument.get("fundingInterval")
        }

    def get_orderbook(self, symbol: str, depth: int = 25) -> Dict[str, Any]:
        """
        Get order book data for a contract.

        Args:
            symbol: Contract symbol
            depth: Number of price levels (max 25 for unauthenticated)

        Returns:
            Dictionary with bid/ask data
        """
        url = f"{self.base_url}/orderBook/L2"
        params = {
            "symbol": symbol,
            "depth": min(depth, 25)  # Max 25 for public API
        }

        response = self.make_request(url, params=params)
        self.validate_response(response, f"Get orderbook for {symbol}")

        data = self.safe_json_parse(response, f"Orderbook for {symbol}")

        # Separate bids and asks
        bids = []
        asks = []

        for order in data:
            entry = {
                "price": float(order["price"]),
                "size": int(order["size"])
            }

            if order["side"] == "Buy":
                bids.append(entry)
            else:
                asks.append(entry)

        # Sort bids descending, asks ascending
        bids.sort(key=lambda x: x["price"], reverse=True)
        asks.sort(key=lambda x: x["price"])

        return {
            "symbol": symbol,
            "bids": bids[:depth],
            "asks": asks[:depth],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def get_recent_trades(self, symbol: str, count: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent trades for a contract.

        Args:
            symbol: Contract symbol
            count: Number of trades to fetch (max 500)

        Returns:
            List of recent trades
        """
        url = f"{self.base_url}/trade"
        params = {
            "symbol": symbol,
            "count": min(count, 500),
            "reverse": True  # Most recent first
        }

        response = self.make_request(url, params=params)
        self.validate_response(response, f"Get recent trades for {symbol}")

        data = self.safe_json_parse(response, f"Recent trades for {symbol}")

        trades = []
        for trade in data:
            trades.append({
                "timestamp": trade["timestamp"],
                "symbol": trade["symbol"],
                "side": trade["side"],
                "size": int(trade["size"]),
                "price": float(trade["price"]),
                "tick_direction": trade.get("tickDirection"),
                "trade_id": trade.get("trdMatchID")
            })

        return trades

    def fetch(self, mode: str, **kwargs) -> Any:
        """
        Unified fetch interface matching other fetchers.

        Args:
            mode: Fetch mode (trending, price, history, orderbook, etc.)
            **kwargs: Mode-specific parameters

        Returns:
            Requested data
        """
        if mode == "trending":
            return self.get_trending_contracts(limit=kwargs.get("limit", 15))

        elif mode == "price":
            return self.get_price(
                symbol=kwargs["symbol"],
                price_type=kwargs.get("price_type", "mark")
            )

        elif mode == "price_with_history":
            return self.get_price_with_history(
                symbol=kwargs["symbol"],
                lookback_days=kwargs.get("lookback_days", 10),
                price_type=kwargs.get("price_type", "mark")
            )

        elif mode == "history":
            return self.get_price_history(
                symbol=kwargs["symbol"],
                start_date=kwargs["start_date"],
                end_date=kwargs["end_date"],
                interval=kwargs.get("interval", "1d")
            )

        elif mode == "funding":
            return self.get_funding_rate(symbol=kwargs["symbol"])

        elif mode == "orderbook":
            return self.get_orderbook(
                symbol=kwargs["symbol"],
                depth=kwargs.get("depth", 25)
            )

        elif mode == "trades":
            return self.get_recent_trades(
                symbol=kwargs["symbol"],
                count=kwargs.get("count", 100)
            )

        else:
            raise ValueError(f"Unknown fetch mode: {mode}")
