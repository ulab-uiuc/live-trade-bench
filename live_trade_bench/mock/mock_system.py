"""
Mock Systems for easy testing of different components.
"""

from live_trade_bench.accounts import create_polymarket_account, create_stock_account
from live_trade_bench.mock.mock_agent import (
    create_mock_polymarket_agent,
    create_mock_stock_agent,
)
from live_trade_bench.mock.mock_fetcher import (
    fetch_current_stock_price,
    fetch_news_data,
    fetch_polymarket_data,
)
from live_trade_bench.systems.polymarket_system import PolymarketPortfolioSystem
from live_trade_bench.systems.stock_system import StockPortfolioSystem


class MockAgentStockSystem(StockPortfolioSystem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.agents:
            mock_agent = create_mock_stock_agent("Mock_Stock_Agent")
            account = create_stock_account(1000.0)
            self.agents["Mock_Stock_Agent"] = mock_agent
            self.accounts["Mock_Stock_Agent"] = account

    @classmethod
    def get_instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance


class MockFetcherStockSystem(StockPortfolioSystem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.agents:
            mock_agent = create_mock_stock_agent("Mock_Stock_Agent")
            account = create_stock_account(1000.0)
            self.agents["Mock_Stock_Agent"] = mock_agent
            self.accounts["Mock_Stock_Agent"] = account

    @classmethod
    def get_instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance

    def _fetch_market_data(self, for_date=None):
        market_data = {}
        for ticker in self.universe:
            price = fetch_current_stock_price(ticker)
            if price:
                market_data[ticker] = {
                    "ticker": ticker,
                    "name": self.stock_info[ticker]["name"],
                    "sector": self.stock_info[ticker]["sector"],
                    "current_price": price,
                    "market_cap": self.stock_info[ticker]["market_cap"],
                }
        return market_data

    def _fetch_news_data(self, market_data, for_date=None):
        print("  - Fetching news data...")
        news_data_map = {}

        for ticker in market_data.keys():
            # Use mock news fetcher
            mock_articles = fetch_news_data(
                query=ticker,
                start_date="2024-01-01",
                end_date="2024-12-31",
                max_pages=2,
            )

            if mock_articles:
                # Pick the first article to match real system behavior
                article = mock_articles[0]
                cleaned_snippet = (
                    article["snippet"][:300] + "..."
                    if len(article["snippet"]) > 300
                    else article["snippet"]
                )
                news_data_map[ticker] = {
                    "title": article["title"],
                    "snippet": cleaned_snippet,
                    "source": article["source"],
                    "date": article["date"],
                    "link": article["link"],
                }
                print(f"    - News for {ticker}: {article['title'][:50]}...")

        print("  - ✅ News data fetched")
        return news_data_map


class MockAgentFetcherStockSystem(StockPortfolioSystem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.agents:
            # Replace the default LLM agent with mock agent
            mock_agent = create_mock_stock_agent("Mock_Stock_Agent")
            account = create_stock_account(1000.0)
            self.agents["Mock_Stock_Agent"] = mock_agent
            self.accounts["Mock_Stock_Agent"] = account

    @classmethod
    def get_instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance

    def _fetch_market_data(self, for_date=None):
        market_data = {}
        for ticker in self.universe:
            price = fetch_current_stock_price(ticker)
            if price:
                market_data[ticker] = {
                    "ticker": ticker,
                    "name": self.stock_info[ticker]["name"],
                    "sector": self.stock_info[ticker]["sector"],
                    "current_price": price,
                    "market_cap": self.stock_info[ticker]["market_cap"],
                }
        return market_data

    def _fetch_news_data(self, market_data, for_date=None):
        print("  - Fetching news data...")
        news_data_map = {}

        for ticker in market_data.keys():
            # Use mock news fetcher
            mock_articles = fetch_news_data(
                query=ticker,
                start_date="2024-01-01",
                end_date="2024-12-31",
                max_pages=2,
            )

            if mock_articles:
                # Pick the first article to match real system behavior
                article = mock_articles[0]
                cleaned_snippet = (
                    article["snippet"][:300] + "..."
                    if len(article["snippet"]) > 300
                    else article["snippet"]
                )
                news_data_map[ticker] = {
                    "title": article["title"],
                    "snippet": cleaned_snippet,
                    "source": article["source"],
                    "date": article["date"],
                    "link": article["link"],
                }
                print(f"    - News for {ticker}: {article['title'][:50]}...")

        print("  - ✅ News data fetched")
        return news_data_map


class MockAgentPolymarketSystem(PolymarketPortfolioSystem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.agents:
            # Replace the default LLM agent with mock agent
            mock_agent = create_mock_polymarket_agent("Mock_Polymarket_Agent")
            account = create_polymarket_account(1000.0)
            self.agents["Mock_Polymarket_Agent"] = mock_agent
            self.accounts["Mock_Polymarket_Agent"] = account

    @classmethod
    def get_instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance

    def _fetch_market_data(self, for_date=None):
        return fetch_polymarket_data(self.universe)


class MockFetcherPolymarketSystem(PolymarketPortfolioSystem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.agents:
            mock_agent = create_mock_polymarket_agent("Mock_Polymarket_Agent")
            account = create_polymarket_account(1000.0)
            self.agents["Mock_Polymarket_Agent"] = mock_agent
            self.accounts["Mock_Polymarket_Agent"] = account

    @classmethod
    def get_instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance

    def _fetch_market_data(self, for_date=None):
        return fetch_polymarket_data(self.universe)

    def _fetch_news_data(self, market_data, for_date=None):
        print("  - Fetching news data...")
        news_data_map = {}

        for market_id in market_data.keys():
            # Use mock news fetcher with market ID as query
            mock_articles = fetch_news_data(
                query=f"market_{market_id}",
                start_date="2024-01-01",
                end_date="2024-12-31",
                max_pages=2,
            )

            if mock_articles:
                # Pick the first article to match real system behavior
                article = mock_articles[0]
                cleaned_snippet = (
                    article["snippet"][:300] + "..."
                    if len(article["snippet"]) > 300
                    else article["snippet"]
                )
                news_data_map[market_id] = {
                    "title": article["title"],
                    "snippet": cleaned_snippet,
                    "source": article["source"],
                    "date": article["date"],
                    "link": article["link"],
                }
                print(f"    - News for {market_id}: {article['title'][:50]}...")

        print("  - ✅ News data fetched")
        return news_data_map


class MockAgentFetcherPolymarketSystem(PolymarketPortfolioSystem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.agents:
            # Replace the default LLM agent with mock agent
            mock_agent = create_mock_polymarket_agent("Mock_Polymarket_Agent")
            account = create_polymarket_account(1000.0)
            self.agents["Mock_Polymarket_Agent"] = mock_agent
            self.accounts["Mock_Polymarket_Agent"] = account

    @classmethod
    def get_instance(cls):
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance

    def _fetch_market_data(self, for_date=None):
        return fetch_polymarket_data(self.universe)

    def _fetch_news_data(self, market_data, for_date=None):
        print("  - Fetching news data...")
        news_data_map = {}

        for market_id in market_data.keys():
            # Use mock news fetcher with market ID as query
            mock_articles = fetch_news_data(
                query=f"market_{market_id}",
                start_date="2024-01-01",
                end_date="2024-12-31",
                max_pages=2,
            )

            if mock_articles:
                # Pick the first article to match real system behavior
                article = mock_articles[0]
                cleaned_snippet = (
                    article["snippet"][:300] + "..."
                    if len(article["snippet"]) > 300
                    else article["snippet"]
                )
                news_data_map[market_id] = {
                    "title": article["title"],
                    "snippet": cleaned_snippet,
                    "source": article["source"],
                    "date": article["date"],
                    "link": article["link"],
                }
                print(f"    - News for {market_id}: {article['title'][:50]}...")

        print("  - ✅ News data fetched")
        return news_data_map


# Factory functions for thread-safe instantiation
def create_mock_agent_stock_system():
    return MockAgentStockSystem()


def create_mock_fetcher_stock_system():
    return MockFetcherStockSystem()


def create_mock_agent_fetcher_stock_system():
    return MockAgentFetcherStockSystem()


def create_mock_agent_polymarket_system():
    return MockAgentPolymarketSystem()


def create_mock_fetcher_polymarket_system():
    return MockFetcherPolymarketSystem()


def create_mock_agent_fetcher_polymarket_system():
    return MockAgentFetcherPolymarketSystem()
