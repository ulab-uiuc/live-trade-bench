"""
Test Scenarios Configuration

Contains market data, news, and expected results for LLM integration tests.
Centralizes test data for easier modification and understanding.
"""

from datetime import datetime, timedelta

# =============================================================================
# BULLISH SCENARIO: Strong Uptrend
# =============================================================================

BULLISH_SCENARIO = {
    "description": "Strong uptrend: BTC +7.7%, ETH +7.7%, SOL +4.8% over 4 days with positive news",

    "market_data": {
        "XBTUSD": {
            "current_price": 70000.0,
            "funding_rate": 0.0150,  # +1.5% - strong bullish sentiment (longs pay shorts)
            "bid_depth": 250000,      # Strong buying pressure
            "ask_depth": 120000,      # Weak selling pressure
            "open_interest": 60000,
            "price_history": [
                {"date": "2024-10-20", "price": 65000.0},
                {"date": "2024-10-21", "price": 66500.0},
                {"date": "2024-10-22", "price": 68000.0},
                {"date": "2024-10-23", "price": 70000.0}  # Clear uptrend +7.7%
            ]
        },
        "ETHUSD": {
            "current_price": 2800.0,
            "funding_rate": 0.0120,  # +1.2% - bullish sentiment
            "bid_depth": 180000,      # Strong buying
            "ask_depth": 90000,       # Weak selling
            "open_interest": 80000,
            "price_history": [
                {"date": "2024-10-20", "price": 2600.0},
                {"date": "2024-10-21", "price": 2680.0},
                {"date": "2024-10-22", "price": 2750.0},
                {"date": "2024-10-23", "price": 2800.0}  # Clear uptrend +7.7%
            ]
        },
        "SOLUSDT": {
            "current_price": 152.0,
            "funding_rate": 0.0100,  # +1.0% - moderate bullish
            "bid_depth": 40000,
            "ask_depth": 30000,
            "open_interest": 35000,
            "price_history": [
                {"date": "2024-10-20", "price": 145.0},
                {"date": "2024-10-21", "price": 147.5},
                {"date": "2024-10-22", "price": 150.0},
                {"date": "2024-10-23", "price": 152.0}  # Uptrend +4.8%
            ]
        }
    },

    "news_data": {
        "XBTUSD": [
            {
                "title": "Bitcoin Surges to New All-Time High on Institutional Demand",
                "date": int(datetime(2024, 10, 23).timestamp()),
                "snippet": "Bitcoin reached new highs as major institutions increase exposure, with BlackRock reporting record ETF inflows",
                "source": "CoinDesk"
            },
            {
                "title": "Wall Street Banks Announce Major Bitcoin Trading Desks",
                "date": int(datetime(2024, 10, 22).timestamp()),
                "snippet": "Goldman Sachs and JPMorgan expand crypto operations amid growing client demand",
                "source": "Bloomberg"
            }
        ],
        "ETHUSD": [
            {
                "title": "Ethereum Network Upgrade Drives Price Rally",
                "date": int(datetime(2024, 10, 23).timestamp()),
                "snippet": "Ethereum gains momentum after successful network upgrade improves scalability and reduces fees",
                "source": "The Block"
            },
            {
                "title": "Ethereum DeFi Total Value Locked Hits Record High",
                "date": int(datetime(2024, 10, 22).timestamp()),
                "snippet": "DeFi protocols on Ethereum see massive inflows as institutional adoption accelerates",
                "source": "CoinTelegraph"
            }
        ],
        "SOLUSDT": [
            {
                "title": "Solana Network Activity Surges 200% Week-over-Week",
                "date": int(datetime(2024, 10, 23).timestamp()),
                "snippet": "Daily transactions on Solana blockchain jumped significantly amid growing ecosystem adoption",
                "source": "Decrypt"
            }
        ]
    },

    "account_data": {
        "allocation_history": [
            {
                "timestamp": "2024-10-20T12:00:00",
                "allocations": {"XBTUSD": 0.30, "ETHUSD": 0.20, "SOLUSDT": 0.10, "CASH": 0.40},
                "performance": 1.5
            },
            {
                "timestamp": "2024-10-21T12:00:00",
                "allocations": {"XBTUSD": 0.32, "ETHUSD": 0.22, "SOLUSDT": 0.11, "CASH": 0.35},
                "performance": 3.2
            },
            {
                "timestamp": "2024-10-22T12:00:00",
                "allocations": {"XBTUSD": 0.35, "ETHUSD": 0.25, "SOLUSDT": 0.12, "CASH": 0.28},
                "performance": 5.8
            }
        ]
    }
}


# =============================================================================
# BEARISH SCENARIO: Strong Downtrend
# =============================================================================

BEARISH_SCENARIO = {
    "description": "Strong downtrend: BTC -8.8%, ETH -10.7%, SOL -9.2% over 4 days with negative news",

    "market_data": {
        "XBTUSD": {
            "current_price": 62000.0,
            "funding_rate": -0.0100,  # -1.0% - bearish sentiment (shorts pay longs)
            "bid_depth": 120000,       # Weak buying pressure
            "ask_depth": 250000,       # Strong selling pressure
            "open_interest": 58000,
            "price_history": [
                {"date": "2024-10-20", "price": 68000.0},
                {"date": "2024-10-21", "price": 66000.0},
                {"date": "2024-10-22", "price": 64000.0},
                {"date": "2024-10-23", "price": 62000.0}  # Clear downtrend -8.8%
            ]
        },
        "ETHUSD": {
            "current_price": 2500.0,
            "funding_rate": -0.0080,  # -0.8% - bearish sentiment
            "bid_depth": 90000,        # Weak buying
            "ask_depth": 180000,       # Strong selling
            "open_interest": 75000,
            "price_history": [
                {"date": "2024-10-20", "price": 2800.0},
                {"date": "2024-10-21", "price": 2700.0},
                {"date": "2024-10-22", "price": 2600.0},
                {"date": "2024-10-23", "price": 2500.0}  # Clear downtrend -10.7%
            ]
        },
        "SOLUSDT": {
            "current_price": 138.0,
            "funding_rate": -0.0050,  # -0.5% - moderate bearish
            "bid_depth": 30000,
            "ask_depth": 50000,
            "open_interest": 32000,
            "price_history": [
                {"date": "2024-10-20", "price": 152.0},
                {"date": "2024-10-21", "price": 147.0},
                {"date": "2024-10-22", "price": 142.0},
                {"date": "2024-10-23", "price": 138.0}  # Downtrend -9.2%
            ]
        }
    },

    "news_data": {
        "XBTUSD": [
            {
                "title": "Bitcoin Plunges as Regulatory Concerns Mount",
                "date": int(datetime(2024, 10, 23).timestamp()),
                "snippet": "Bitcoin dropped sharply following announcements of stricter regulatory oversight from major economies",
                "source": "CoinDesk"
            },
            {
                "title": "Major Crypto Exchange Faces Regulatory Scrutiny",
                "date": int(datetime(2024, 10, 22).timestamp()),
                "snippet": "SEC launches investigation into leading cryptocurrency exchange, triggering market selloff",
                "source": "Bloomberg"
            }
        ],
        "ETHUSD": [
            {
                "title": "Ethereum Network Congestion Drives Users to Alternatives",
                "date": int(datetime(2024, 10, 23).timestamp()),
                "snippet": "High gas fees and network congestion push DeFi users to competing blockchain platforms",
                "source": "The Block"
            },
            {
                "title": "Ethereum DeFi Protocols See Significant Outflows",
                "date": int(datetime(2024, 10, 22).timestamp()),
                "snippet": "Total value locked in Ethereum DeFi drops 15% as users exit amid market uncertainty",
                "source": "CoinTelegraph"
            }
        ],
        "SOLUSDT": [
            {
                "title": "Solana Network Experiences Multiple Outages",
                "date": int(datetime(2024, 10, 23).timestamp()),
                "snippet": "Solana blockchain suffered performance issues this week, raising reliability concerns",
                "source": "Decrypt"
            }
        ]
    },

    "account_data": {
        "allocation_history": []  # Empty to avoid anchoring LLM
    }
}


# =============================================================================
# EXPECTED TEST RESULTS
# =============================================================================

EXPECTED_RESULTS = {
    "bullish": {
        "description": "Bullish scenario: should increase crypto exposure",
        "crypto_allocation": {
            "min": 0.50,  # At least 50% in crypto
            "max": 0.90,  # At most 90% (some diversification)
        },
        "cash_allocation": {
            "min": 0.10,
            "max": 0.40,  # Max 40% cash in bull market
        },
        "btc_allocation": {
            "min": 0.20,  # BTC should have meaningful allocation
        },
        "keywords": ["up", "uptrend", "positive", "momentum", "rally", "surge", "bullish", "gain", "increase"]
    },

    "bearish": {
        "description": "Bearish scenario: should decrease crypto exposure and preserve capital",
        "crypto_allocation": {
            "min": 0.10,  # Some exposure maintained
            "max": 0.40,  # Max 40% in crypto during bear market
        },
        "cash_allocation": {
            "min": 0.50,  # At least 50% cash for capital preservation
            "max": 0.90,
        },
        "btc_allocation": {
            "max": 0.25,  # BTC should be reduced
        },
        "keywords": ["down", "downtrend", "decline", "negative", "bearish", "risk", "caution", "defensive", "fall", "drop", "plunge"]
    }
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_scenario(scenario_type: str) -> dict:
    """
    Get scenario data by type.

    Args:
        scenario_type: Either "bullish" or "bearish"

    Returns:
        Dictionary with market_data, news_data, and account_data
    """
    scenarios = {
        "bullish": BULLISH_SCENARIO,
        "bearish": BEARISH_SCENARIO
    }

    if scenario_type not in scenarios:
        raise ValueError(f"Unknown scenario type: {scenario_type}. Must be 'bullish' or 'bearish'")

    return scenarios[scenario_type]


def get_expected_results(scenario_type: str) -> dict:
    """
    Get expected test results for a scenario type.

    Args:
        scenario_type: Either "bullish" or "bearish"

    Returns:
        Dictionary with expected allocation ranges and keywords
    """
    if scenario_type not in EXPECTED_RESULTS:
        raise ValueError(f"Unknown scenario type: {scenario_type}. Must be 'bullish' or 'bearish'")

    return EXPECTED_RESULTS[scenario_type]
