from .config import (
    STOCK_MOCK_MODE,
    POLYMARKET_MOCK_MODE,
    MockMode,
)
from live_trade_bench.systems import (
    create_polymarket_portfolio_system,
    create_stock_portfolio_system,
    StockPortfolioSystem,
    PolymarketPortfolioSystem,
)
from live_trade_bench.mock.mock_system import (
    create_mock_agent_stock_system,
    create_mock_fetcher_stock_system,
    create_mock_agent_fetcher_stock_system,
    create_mock_agent_polymarket_system,
    create_mock_fetcher_polymarket_system,
    create_mock_agent_fetcher_polymarket_system,
)


def get_system(
    market_type: str,
) -> StockPortfolioSystem | PolymarketPortfolioSystem:
    """
    Factory function to get a system instance based on market type and mock mode.
    This is thread-safe as it always creates new instances.
    """
    is_stock = market_type == "stock"
    mock_mode = STOCK_MOCK_MODE if is_stock else POLYMARKET_MOCK_MODE

    if mock_mode == MockMode.NONE:
        return create_stock_portfolio_system() if is_stock else create_polymarket_portfolio_system()
    
    print(f"--- Running in {mock_mode} mode for {market_type.upper()} ---")
    
    if is_stock:
        if mock_mode == MockMode.MOCK_AGENTS:
            return create_mock_agent_stock_system()
        elif mock_mode == MockMode.MOCK_FETCHERS:
            return create_mock_fetcher_stock_system()
        elif mock_mode == MockMode.MOCK_AGENTS_AND_FETCHERS:
            return create_mock_agent_fetcher_stock_system()
    else:  # polymarket
        if mock_mode == MockMode.MOCK_AGENTS:
            return create_mock_agent_polymarket_system()
        elif mock_mode == MockMode.MOCK_FETCHERS:
            return create_mock_fetcher_polymarket_system()
        elif mock_mode == MockMode.MOCK_AGENTS_AND_FETCHERS:
            return create_mock_agent_fetcher_polymarket_system()

    # Fallback to real system
    return create_stock_portfolio_system() if is_stock else create_polymarket_portfolio_system()
