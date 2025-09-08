"""
Mock Systems for easy testing of different components.
"""

from live_trade_bench.accounts import PolymarketAccount, StockAccount
from live_trade_bench.mock.mock_agent import (
    create_mock_polymarket_agent,
    create_mock_stock_agent,
)
from live_trade_bench.mock.mock_fetcher import (
    fetch_current_stock_price,
    fetch_polymarket_data,
)
from live_trade_bench.systems.polymarket_system import PolymarketPortfolioSystem
from live_trade_bench.systems.stock_system import StockPortfolioSystem


class MockAgentStockSystem(StockPortfolioSystem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.agents:
            mock_agent = create_mock_stock_agent("Mock_Stock_Agent")
            mock_agent.account = StockAccount(cash_balance=1000.0)
            self.agents["Mock_Stock_Agent"] = mock_agent


class MockFetcherStockSystem(StockPortfolioSystem):
    def _fetch_market_data(self):
        return {ticker: fetch_current_stock_price(ticker) for ticker in self.tickers}


class MockAgentFetcherStockSystem(StockPortfolioSystem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.agents:
            mock_agent = create_mock_stock_agent("Mock_Stock_Agent")
            mock_agent.account = StockAccount(cash_balance=1000.0)
            self.agents["Mock_Stock_Agent"] = mock_agent

    def _fetch_market_data(self):
        return {ticker: fetch_current_stock_price(ticker) for ticker in self.tickers}


class MockAgentPolymarketSystem(PolymarketPortfolioSystem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.agents:
            mock_agent = create_mock_polymarket_agent("Mock_Polymarket_Agent")
            mock_agent.account = PolymarketAccount(cash_balance=1000.0)
            self.agents["Mock_Polymarket_Agent"] = mock_agent

    def _fetch_market_data(self):
        return fetch_polymarket_data(self.market_slugs)


class MockFetcherPolymarketSystem(PolymarketPortfolioSystem):
    def _fetch_market_data(self):
        return fetch_polymarket_data(self.market_slugs)


class MockAgentFetcherPolymarketSystem(PolymarketPortfolioSystem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.agents:
            mock_agent = create_mock_polymarket_agent("Mock_Polymarket_Agent")
            mock_agent.account = PolymarketAccount(cash_balance=1000.0)
            self.agents["Mock_Polymarket_Agent"] = mock_agent

    def _fetch_market_data(self):
        return fetch_polymarket_data(self.market_slugs)
