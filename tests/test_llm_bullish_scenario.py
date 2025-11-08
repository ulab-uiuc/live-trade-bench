"""
LLM Integration Test: Bullish Scenario

Tests that the LLM makes appropriate trading decisions when BTC and ETH are
trending UP with POSITIVE news. This test makes REAL API calls to the LLM.

Expected Behavior:
- Should INCREASE allocation to BTC/ETH (>50% combined)
- Should DECREASE cash allocation (<40%)
- Reasoning should mention bullish factors
"""

import os

import pytest
from dotenv import load_dotenv

# Load environment variables (including API keys)
load_dotenv()

from live_trade_bench.agents.bitmex_agent import LLMBitMEXAgent
from tests.scenarios_config import get_expected_results, get_scenario


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"),
    reason="Requires OPENAI_API_KEY or ANTHROPIC_API_KEY"
)
def test_strong_bullish_scenario():
    """
    Test that LLM increases crypto allocation in strong bullish scenario.

    Scenario:
    - BTC up 7.7%, ETH up 7.7% over 4 days
    - Very positive news (institutional adoption, network upgrades)
    - Positive funding rates indicating bullish sentiment

    Expected: LLM should significantly increase crypto allocation
    """
    print("\n" + "=" * 80)
    print("BULLISH SCENARIO INTEGRATION TEST")
    print("=" * 80)

    # Setup
    model = os.getenv("TEST_MODEL", "openai/gpt-4o-mini")  # Must prefix with provider
    agent = LLMBitMEXAgent("bullish-test-agent", model)

    # Load scenario from config
    scenario = get_scenario("bullish")
    expected = get_expected_results("bullish")
    market_data = scenario["market_data"]
    news_data = scenario["news_data"]
    account_data = scenario["account_data"]

    print(f"\nUsing Model: {model}")
    print("\nMarket Conditions:")
    print("  BTC: $65,000 → $70,000 (+7.7% over 4 days)")
    print("  ETH: $2,600 → $2,800 (+7.7% over 4 days)")
    print("  SOL: $145 → $152 (+4.8% over 4 days)")
    print("  Funding Rates: BTC +1.50%, ETH +1.20% (bullish)")
    print("  Order Book: Strong bid depth, weak ask depth (buying pressure)")
    print("\nNews Headlines:")
    print("  - Bitcoin Surges to New All-Time High on Institutional Demand")
    print("  - Wall Street Banks Announce Major Bitcoin Trading Desks")
    print("  - Ethereum Network Upgrade Drives Price Rally")
    print("  - Ethereum DeFi Total Value Locked Hits Record High")
    print("\nPrevious Allocation:")
    print("  BTC: 35%, ETH: 25%, SOL: 12%, CASH: 28%")

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

        # Assertion 1: Total crypto allocation should be high
        print(f"\n1. Total crypto allocation: {crypto_total:.1%}")
        crypto_min = expected["crypto_allocation"]["min"]
        if crypto_total > crypto_min:
            print(f"   ✅ PASS: Crypto allocation > {crypto_min:.0%} (expected in bull market)")
        else:
            print(f"   ❌ FAIL: Crypto allocation ≤ {crypto_min:.0%} (too conservative for strong bull market)")
            pytest.fail(f"Expected >{crypto_min:.0%} crypto allocation in bull market, got {crypto_total:.1%}")

        # Assertion 2: Cash should be reduced
        print(f"\n2. CASH allocation: {cash_allocation:.1%}")
        cash_max = expected["cash_allocation"]["max"]
        if cash_allocation < cash_max:
            print(f"   ✅ PASS: CASH < {cash_max:.0%} (expected in bull market)")
        else:
            print(f"   ❌ FAIL: CASH ≥ {cash_max:.0%} (too defensive for strong bull market)")
            pytest.fail(f"Expected <{cash_max:.0%} CASH in bull market, got {cash_allocation:.1%}")

        # Assertion 3: BTC should have meaningful allocation
        print(f"\n3. BTC (leading asset) allocation: {btc_allocation:.1%}")
        btc_min = expected["btc_allocation"]["min"]
        if btc_allocation > btc_min:
            print(f"   ✅ PASS: BTC > {btc_min:.0%} (expected for strong BTC rally)")
        else:
            print(f"   ⚠️  WARNING: BTC ≤ {btc_min:.0%} (might be underweight given strong rally)")

        # Assertion 4: Check reasoning mentions bullish factors
        print(f"\n4. Reasoning content analysis:")
        reasoning_lower = reasoning.lower()
        found_keywords = [kw for kw in expected["keywords"] if kw in reasoning_lower]

        if found_keywords:
            print(f"   ✅ PASS: Reasoning mentions bullish factors: {', '.join(found_keywords)}")
        else:
            print(f"   ⚠️  WARNING: Reasoning doesn't clearly mention bullish factors")

        # Check for contradictory bearish mentions
        if "downtrend" in reasoning_lower or "bearish" in reasoning_lower:
            print(f"   ⚠️  WARNING: Reasoning mentions bearish factors in bullish scenario")

        # Soft warnings
        print("\n" + "=" * 80)
        print("ADDITIONAL OBSERVATIONS")
        print("=" * 80)

        if cash_allocation > 0.30:
            print(f"\n⚠️  OBSERVATION: CASH allocation of {cash_allocation:.1%} is relatively high for a strong bull market")

        if crypto_total < 0.60:
            print(f"\n⚠️  OBSERVATION: Total crypto allocation of {crypto_total:.1%} seems conservative given strong uptrend")

        if len(reasoning) < 100:
            print(f"\n⚠️  OBSERVATION: Reasoning is quite short ({len(reasoning)} chars) - might indicate superficial analysis")

        print("\n" + "=" * 80)
        print("✅ TEST PASSED: LLM appropriately increased crypto allocation in bullish scenario")
        print("=" * 80 + "\n")

    else:
        print("\n❌ ERROR: LLM failed to return allocation")
        pytest.fail("LLM did not return a valid allocation")


if __name__ == "__main__":
    # Run the test directly
    test_strong_bullish_scenario()
