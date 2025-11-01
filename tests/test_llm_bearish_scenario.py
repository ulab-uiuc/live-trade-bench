"""
LLM Integration Test: Bearish Scenario

Tests that the LLM makes appropriate trading decisions when BTC and ETH are
trending DOWN with NEGATIVE news. This test makes REAL API calls to the LLM.

Expected Behavior:
- Should DECREASE allocation to BTC/ETH (<40% combined)
- Should INCREASE cash allocation (>50%)
- Reasoning should mention bearish factors and risk management
"""

import os
import pytest
from dotenv import load_dotenv

# Load environment variables (including API keys)
load_dotenv()

from live_trade_bench.agents.bitmex_agent import LLMBitMEXAgent
from tests.scenarios_config import get_scenario, get_expected_results


def create_strong_bearish_scenario():
    """
    Create a strong bearish market scenario:
    - BTC: $68K → $62K (-8.8% over 4 days)
    - ETH: $2800 → $2500 (-10.7% over 4 days)
    - Negative funding rates (bearish sentiment)
    - Weak bid depth vs strong ask depth (selling pressure)
    - Very negative news
    """
    today = datetime(2024, 10, 23)

    market_data = {
        "XBTUSD": {
            "current_price": 62000.0,
            "funding_rate": -0.0100,  # -1.0% - bearish sentiment (shorts paying longs)
            "bid_depth": 120000,  # Weak buying
            "ask_depth": 250000,  # Strong selling
            "open_interest": 58000,
            "price_history": [
                {"date": "2024-10-20", "price": 68000.0},
                {"date": "2024-10-21", "price": 66000.0},
                {"date": "2024-10-22", "price": 64000.0},
                {"date": "2024-10-23", "price": 62000.0}  # Clear downtrend
            ]
        },
        "ETHUSD": {
            "current_price": 2500.0,
            "funding_rate": -0.0080,  # -0.8% - bearish sentiment
            "bid_depth": 90000,   # Weak buying
            "ask_depth": 180000,  # Strong selling
            "open_interest": 75000,
            "price_history": [
                {"date": "2024-10-20", "price": 2800.0},
                {"date": "2024-10-21", "price": 2700.0},
                {"date": "2024-10-22", "price": 2600.0},
                {"date": "2024-10-23", "price": 2500.0}  # Clear downtrend
            ]
        },
        "SOLUSDT": {
            "current_price": 138.0,
            "funding_rate": -0.0050,
            "bid_depth": 30000,
            "ask_depth": 50000,
            "open_interest": 32000,
            "price_history": [
                {"date": "2024-10-20", "price": 152.0},
                {"date": "2024-10-21", "price": 147.0},
                {"date": "2024-10-22", "price": 142.0},
                {"date": "2024-10-23", "price": 138.0}
            ]
        }
    }

    news_data = {
        "XBTUSD": [
            {
                "title": "Bitcoin Plunges as Regulatory Concerns Mount",
                "date": int(today.timestamp()),
                "snippet": "Bitcoin dropped sharply following announcements of stricter regulatory oversight from major economies",
                "source": "CoinDesk"
            },
            {
                "title": "Major Crypto Exchange Faces Regulatory Scrutiny",
                "date": int((today - timedelta(days=1)).timestamp()),
                "snippet": "SEC launches investigation into leading cryptocurrency exchange, triggering market selloff",
                "source": "Bloomberg"
            }
        ],
        "ETHUSD": [
            {
                "title": "Ethereum Network Congestion Drives Users to Alternatives",
                "date": int(today.timestamp()),
                "snippet": "High gas fees and network congestion push DeFi users to competing blockchain platforms",
                "source": "The Block"
            },
            {
                "title": "Ethereum DeFi Protocols See Significant Outflows",
                "date": int((today - timedelta(days=1)).timestamp()),
                "snippet": "Total value locked in Ethereum DeFi drops 15% as users exit amid market uncertainty",
                "source": "CoinTelegraph"
            }
        ],
        "SOLUSDT": [
            {
                "title": "Solana Network Experiences Multiple Outages",
                "date": int(today.timestamp()),
                "snippet": "Solana blockchain suffered performance issues this week, raising reliability concerns",
                "source": "Decrypt"
            }
        ]
    }

    account_data = {
        "allocation_history": []  # Empty history to avoid anchoring
    }

    return market_data, news_data, account_data


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"),
    reason="Requires OPENAI_API_KEY or ANTHROPIC_API_KEY"
)
def test_strong_bearish_scenario():
    """
    Test that LLM decreases crypto allocation in strong bearish scenario.

    Scenario:
    - BTC down 8.8%, ETH down 10.7% over 4 days
    - Very negative news (regulatory concerns, network issues)
    - Negative funding rates indicating bearish sentiment

    Expected: LLM should significantly reduce crypto allocation and increase CASH
    """
    print("\n" + "=" * 80)
    print("BEARISH SCENARIO INTEGRATION TEST")
    print("=" * 80)

    # Setup
    model = os.getenv("TEST_MODEL", "openai/gpt-4o-mini")  # Must prefix with provider
    agent = LLMBitMEXAgent("bearish-test-agent", model)

    # Load scenario from config
    scenario = get_scenario("bearish")
    expected = get_expected_results("bearish")
    market_data = scenario["market_data"]
    news_data = scenario["news_data"]
    account_data = scenario["account_data"]

    print(f"\nUsing Model: {model}")
    print("\nMarket Conditions:")
    print("  BTC: $68,000 → $62,000 (-8.8% over 4 days)")
    print("  ETH: $2,800 → $2,500 (-10.7% over 4 days)")
    print("  SOL: $152 → $138 (-9.2% over 4 days)")
    print("  Funding Rates: BTC -1.00%, ETH -0.80% (bearish)")
    print("  Order Book: Weak bid depth, strong ask depth (selling pressure)")
    print("\nNews Headlines:")
    print("  - Bitcoin Plunges as Regulatory Concerns Mount")
    print("  - Major Crypto Exchange Faces Regulatory Scrutiny")
    print("  - Ethereum Network Congestion Drives Users to Alternatives")
    print("  - Ethereum DeFi Protocols See Significant Outflows")
    print("\nPrevious Allocation:")
    print("  BTC: 28%, ETH: 20%, SOL: 8%, CASH: 44%")

    # Execute - REAL LLM API CALL
    print("\n" + "-" * 80)
    print("Calling LLM (this will make a real API call)...")
    print("-" * 80)

    allocation = agent.generate_allocation(
        market_data,
        account_data,
        date="2024-10-23",
        news_data=news_data
    )

    # Get LLM reasoning
    reasoning = ""
    if hasattr(agent, 'last_llm_output') and agent.last_llm_output:
        llm_response = agent.last_llm_output.get("content", "")
        # Try to extract reasoning from JSON response
        try:
            import json
            if "{" in llm_response:
                json_start = llm_response.find("{")
                json_end = llm_response.rfind("}") + 1
                response_json = json.loads(llm_response[json_start:json_end])
                reasoning = response_json.get("reasoning", llm_response)
            else:
                reasoning = llm_response
        except:
            reasoning = llm_response

    # Display Results
    print("\n" + "=" * 80)
    print("LLM DECISION")
    print("=" * 80)

    if allocation:
        print("\nAllocations:")
        for asset, weight in sorted(allocation.items(), key=lambda x: x[1], reverse=True):
            print(f"  {asset:10s}: {weight:5.1%}")

        print(f"\nLLM Reasoning:")
        print(f"  {reasoning}")

        # Calculate metrics
        crypto_total = allocation.get("XBTUSD", 0) + allocation.get("ETHUSD", 0) + allocation.get("SOLUSDT", 0)
        btc_allocation = allocation.get("XBTUSD", 0)
        eth_allocation = allocation.get("ETHUSD", 0)
        cash_allocation = allocation.get("CASH", 0)

        print("\n" + "=" * 80)
        print("ASSERTIONS")
        print("=" * 80)

        # Assertion 1: Total crypto allocation should be low
        print(f"\n1. Total crypto allocation: {crypto_total:.1%}")
        crypto_max = expected["crypto_allocation"]["max"]
        if crypto_total < crypto_max:
            print(f"   ✅ PASS: Crypto allocation < {crypto_max:.0%} (expected in bear market)")
        else:
            print(f"   ❌ FAIL: Crypto allocation ≥ {crypto_max:.0%} (too aggressive for strong bear market)")
            pytest.fail(f"Expected <{crypto_max:.0%} crypto allocation in bear market, got {crypto_total:.1%}")

        # Assertion 2: Cash should be high (risk management)
        print(f"\n2. CASH allocation: {cash_allocation:.1%}")
        cash_min = expected["cash_allocation"]["min"]
        if cash_allocation > cash_min:
            print(f"   ✅ PASS: CASH > {cash_min:.0%} (expected in bear market for risk management)")
        else:
            print(f"   ❌ FAIL: CASH ≤ {cash_min:.0%} (insufficient risk management for strong bear market)")
            pytest.fail(f"Expected >{cash_min:.0%} CASH in bear market, got {cash_allocation:.1%}")

        # Assertion 3: BTC allocation should be reduced
        print(f"\n3. BTC allocation: {btc_allocation:.1%}")
        btc_max = expected["btc_allocation"]["max"]
        if btc_allocation < btc_max:
            print(f"   ✅ PASS: BTC < {btc_max:.0%} (appropriately reduced given downtrend)")
        else:
            print(f"   ⚠️  WARNING: BTC ≥ {btc_max:.0%} (might be overweight given sharp decline)")

        # Assertion 4: Check reasoning mentions bearish factors
        print(f"\n4. Reasoning content analysis:")
        reasoning_lower = reasoning.lower()
        found_keywords = [kw for kw in expected["keywords"] if kw in reasoning_lower]

        if found_keywords:
            print(f"   ✅ PASS: Reasoning mentions bearish factors: {', '.join(found_keywords)}")
        else:
            print(f"   ⚠️  WARNING: Reasoning doesn't clearly mention bearish factors")

        # Check for contradictory bullish mentions
        if "uptrend" in reasoning_lower or "bullish" in reasoning_lower:
            print(f"   ⚠️  WARNING: Reasoning mentions bullish factors in bearish scenario")

        # Soft warnings
        print("\n" + "=" * 80)
        print("ADDITIONAL OBSERVATIONS")
        print("=" * 80)

        if cash_allocation < 0.60:
            print(f"\n⚠️  OBSERVATION: CASH allocation of {cash_allocation:.1%} could be higher given strong downtrend")

        if crypto_total > 0.30:
            print(f"\n⚠️  OBSERVATION: Total crypto allocation of {crypto_total:.1%} seems aggressive given strong downtrend")

        if len(reasoning) < 100:
            print(f"\n⚠️  OBSERVATION: Reasoning is quite short ({len(reasoning)} chars) - might indicate superficial analysis")

        print("\n" + "=" * 80)
        print("✅ TEST PASSED: LLM appropriately decreased crypto allocation in bearish scenario")
        print("=" * 80 + "\n")

    else:
        print("\n❌ ERROR: LLM failed to return allocation")
        pytest.fail("LLM did not return a valid allocation")


if __name__ == "__main__":
    # Run the test directly
    test_strong_bearish_scenario()
