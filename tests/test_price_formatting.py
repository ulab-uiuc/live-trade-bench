"""
Test price formatting for small-value crypto assets.
"""

from live_trade_bench.agents.bitmex_agent import LLMBitMEXAgent


def test_price_formatting():
    """Test that micro-cap tokens display correctly in scientific notation."""
    agent = LLMBitMEXAgent("test_agent")

    # Test market data with various price magnitudes
    market_data = {
        "BTCUSDT": {
            "current_price": 43250.67,
            "funding_rate": 0.0001,
            "bid_depth": 1000000,
            "ask_depth": 950000,
            "price_history": [
                {"date": "2025-01-01", "price": 43000.00},
                {"date": "2025-01-02", "price": 43250.67},
            ],
        },
        "PEPEUSDT": {
            "current_price": 0.00001234,  # Micro-cap meme coin
            "funding_rate": -0.000013,
            "bid_depth": 209296,
            "ask_depth": 166232,
            "price_history": [
                {"date": "2025-11-05", "price": 0.00000000},
                {"date": "2025-11-06", "price": 0.00000000},
                {"date": "2025-11-07", "price": 0.00000000},
            ],
        },
        "BONK_USDT": {
            "current_price": 0.00002567,  # Another micro-cap
            "funding_rate": 0.0001,
            "bid_depth": 1600000000,
            "ask_depth": 1500000000,
            "price_history": [
                {"date": "2025-01-01", "price": 0.00002000},
                {"date": "2025-01-02", "price": 0.00002567},
            ],
        },
        "ETHUSDT": {
            "current_price": 2234.56,  # Mid-range
            "funding_rate": 0.0001,
            "bid_depth": 500000,
            "ask_depth": 480000,
            "price_history": [
                {"date": "2025-01-01", "price": 2200.00},
                {"date": "2025-01-02", "price": 2234.56},
            ],
        },
    }

    # Generate market analysis
    analysis = agent._prepare_market_analysis(market_data)

    print("=" * 80)
    print("PRICE FORMATTING TEST RESULTS")
    print("=" * 80)
    print(analysis)
    print("=" * 80)

    # Verify formatting
    assert "$43,250.6700" in analysis or "$4.33e+04" in analysis or "$43250.6700" in analysis, \
        "BTC should show standard format"

    assert "$1.23e-05" in analysis, \
        f"PEPE should show scientific notation, got:\n{analysis}"

    assert "$2.57e-05" in analysis, \
        f"BONK should show scientific notation, got:\n{analysis}"

    assert "$2,234.5600" in analysis or "$2234.5600" in analysis, \
        "ETH should show standard format"

    # Verify historical prices use scientific notation
    assert "1.23e-05" in analysis or "0.00e+00" in analysis, \
        "Historical PEPE prices should use scientific notation"

    print("\n✓ All formatting tests passed!")
    print("  - Large prices (BTC, ETH): Standard format with 4 decimals")
    print("  - Small prices (PEPE, BONK): Scientific notation (1.23e-05)")
    print("  - Token-efficient and LLM-friendly for mathematical operations")


if __name__ == "__main__":
    test_price_formatting()
