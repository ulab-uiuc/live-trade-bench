#!/usr/bin/env python3
"""
Stock Price Simulator - Mock StockFetcher for Backend Testing

This replaces the real StockFetcher with simulated price data for testing.
Provides the exact same interface as StockFetcher but with simulated data.
"""

import random
import time
from datetime import datetime
from typing import Any, List, Optional, Union

import pandas as pd


class StockPriceSimulator:
    """Simulates stock price data with the same interface as StockFetcher"""

    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """Initialize the stock price simulator."""
        self.min_delay = min_delay
        self.max_delay = max_delay

        # Simulated stock prices - starting values
        self.current_prices = {
            "AAPL": 150.0,
            "MSFT": 300.0,
            "NVDA": 400.0,
            "JPM": 120.0,
            "V": 250.0,
            "JNJ": 160.0,
            "UNH": 450.0,
            "PG": 140.0,
            "KO": 55.0,
            "XOM": 80.0,
            "CAT": 200.0,
            "WMT": 145.0,
            "META": 280.0,
            "TSLA": 220.0,
            "AMZN": 130.0,
        }

        # Volatility settings per stock
        self.volatility = {
            "AAPL": 0.02,
            "MSFT": 0.015,
            "NVDA": 0.035,
            "JPM": 0.02,
            "V": 0.015,
            "JNJ": 0.01,
            "UNH": 0.02,
            "PG": 0.01,
            "KO": 0.01,
            "XOM": 0.025,
            "CAT": 0.02,
            "WMT": 0.015,
            "META": 0.025,
            "TSLA": 0.045,
            "AMZN": 0.03,
        }

    def _rate_limit_delay(self) -> None:
        """Simulate rate limiting delay"""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)

    def _simulate_price_movement(self, ticker: str) -> float:
        """Simulate realistic price movement using geometric Brownian motion"""
        current_price = self.current_prices.get(ticker, 100.0)
        volatility = self.volatility.get(ticker, 0.02)

        # Random walk with slight upward bias
        drift = 0.0001
        random_shock = random.gauss(0, volatility)

        # Apply geometric Brownian motion
        price_change = current_price * (drift + random_shock)
        new_price = current_price + price_change

        # Keep prices reasonable
        new_price = max(new_price, current_price * 0.9)  # Max 10% drop per update
        new_price = min(new_price, current_price * 1.1)  # Max 10% gain per update
        new_price = max(new_price, 1.0)  # Never go below $1

        # Update stored price
        self.current_prices[ticker] = new_price
        return new_price

    def fetch(self, mode: str, **kwargs: Any) -> Union[List[str], Optional[float]]:
        """Main fetch method - same interface as StockFetcher"""
        if mode == "trending_stocks":
            return self.get_trending_stocks(limit=int(kwargs.get("limit", 15)))
        elif mode == "stock_price":
            ticker = kwargs.get("ticker")
            if ticker is None:
                raise ValueError("ticker is required for stock_price")
            return self.get_current_stock_price(str(ticker))
        else:
            raise ValueError(f"Unknown fetch mode: {mode}")

    def get_trending_stocks(self, limit: int = 15) -> List[str]:
        """Return same diversified stock list as real fetcher"""
        diversified_tickers = [
            # Technology (3 stocks)
            "AAPL",  # Apple - Consumer Electronics
            "MSFT",  # Microsoft - Software
            "NVDA",  # NVIDIA - Semiconductor
            # Financial Services (2 stocks)
            "JPM",  # JPMorgan Chase - Banking
            "V",  # Visa - Payment Processing
            # Healthcare (2 stocks)
            "JNJ",  # Johnson & Johnson - Pharmaceuticals
            "UNH",  # UnitedHealth - Health Insurance
            # Consumer Goods (2 stocks)
            "PG",  # Procter & Gamble - Consumer Products
            "KO",  # Coca-Cola - Beverages
            # Energy (1 stock)
            "XOM",  # ExxonMobil - Oil & Gas
            # Industrial (1 stock)
            "CAT",  # Caterpillar - Heavy Machinery
            # Retail (1 stock)
            "WMT",  # Walmart - Retail
            # Communication (1 stock)
            "META",  # Meta - Social Media
            # Automotive (1 stock)
            "TSLA",  # Tesla - Electric Vehicles
            # E-commerce (1 stock)
            "AMZN",  # Amazon - Online Retail
        ]
        return diversified_tickers[:limit]

    def get_current_stock_price(self, ticker: str) -> Optional[float]:
        """Get simulated current price for a ticker"""
        return self.get_current_price(ticker)

    def get_current_price(self, ticker: str) -> Optional[float]:
        """Simulate getting current price - same interface as real fetcher"""
        try:
            # Simulate some processing time
            self._rate_limit_delay()

            # Update price with simulated movement
            new_price = self._simulate_price_movement(ticker)

            print(f"🎲 Simulated price for {ticker}: ${new_price:.2f}")
            return new_price

        except Exception as e:
            print(f"⚠️ Error simulating price for {ticker}: {e}")
            return None

    def fetch_stock_data(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        interval: str = "1d",
    ) -> Any:
        """Simulate fetching historical stock data - returns DataFrame like real fetcher"""
        try:
            self._rate_limit_delay()

            # Generate simulated historical data
            current_price = self.current_prices.get(ticker, 100.0)

            # Create simple DataFrame with one data point (current)
            data = {
                "Open": [current_price],
                "High": [current_price * 1.02],
                "Low": [current_price * 0.98],
                "Close": [current_price],
                "Volume": [1000000],
            }

            df = pd.DataFrame(data, index=[datetime.now()])
            print(f"🎲 Generated simulated data for {ticker}")
            return df

        except Exception as e:
            print(f"Error generating simulated stock data for {ticker}: {e}")
            raise


# Factory functions - same interface as real fetcher
def fetch_trending_stocks(limit: int = 15) -> List[str]:
    """Factory function - same interface as real fetcher"""
    fetcher = StockPriceSimulator()
    stocks = fetcher.get_trending_stocks(limit=limit)
    print(f"🎲 Simulated {len(stocks)} trending stocks")
    return stocks


def fetch_current_stock_price(ticker: str) -> Optional[float]:
    """Factory function - same interface as real fetcher"""
    fetcher = StockPriceSimulator()
    price = fetcher.get_current_stock_price(ticker)
    if price:
        print(f"Simulated stock price 🎲 {ticker}: {price}")
    return price


# Main class alias for drop-in replacement
class StockFetcher(StockPriceSimulator):
    """Alias class for drop-in replacement of real StockFetcher"""

    pass


if __name__ == "__main__":
    # Test the simulator
    print("🎯 TESTING STOCK PRICE SIMULATOR")
    print("=" * 50)

    simulator = StockPriceSimulator()

    # Test trending stocks
    print("\n📊 Testing trending stocks:")
    stocks = simulator.get_trending_stocks(5)
    print(f"Stocks: {stocks}")

    # Test price fetching
    print("\n💰 Testing price fetching:")
    for ticker in stocks[:3]:
        price = simulator.get_current_stock_price(ticker)
        print(f"{ticker}: ${price:.2f}")

    # Test historical data
    print("\n📈 Testing historical data:")
    data = simulator.fetch_stock_data("AAPL", "2024-01-01", "2024-01-02")
    print(f"Data shape: {data.shape}")
    print(data.head())
