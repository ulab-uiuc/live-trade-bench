#!/usr/bin/env python3
"""
Test script to verify all configured LLM models work with litellm
"""

import os
import sys

sys.path.append("live_trade_bench")

from live_trade_bench.utils.llm_client import call_llm

# Model configurations from trading_system.py
MODELS_TO_TEST = [
    ("claude-3.7-sonnet", "claude-3-7-sonnet-20250219"),
    ("gpt-5", "openai/gpt-5"),
    ("gpt-4o", "gpt-4o"),
    ("gemini-2.5-flash", "gemini/gemini-2.5-flash"),
    ("claude-4-sonnet", "claude-sonnet-4-20250514"),
    ("grok-4", "xai/grok-4-0709"),
    ("deepseek-chat", "deepseek/deepseek-chat"),
]

# Simple test message
TEST_MESSAGES = [
    {"role": "user", "content": "What is 2+2? Answer with just the number."}
]


def test_model(model_name: str, model_id: str) -> bool:
    """Test a single model"""
    print(f"\n🧪 Testing {model_name} ({model_id})...")

    try:
        result = call_llm(TEST_MESSAGES, model=model_id, agent_name="TestAgent")

        if result["success"]:
            print(f"✅ {model_name}: SUCCESS")
            print(f"   Response: {result['content']}")
            return True
        else:
            print(f"❌ {model_name}: FAILED")
            print(f"   Error: {result['error']}")
            return False

    except Exception as e:
        print(f"❌ {model_name}: EXCEPTION")
        print(f"   Error: {str(e)}")
        return False


def main() -> None:
    """Test all models"""
    print("🚀 Testing LLM Models with litellm")
    print("=" * 50)

    # Check for API keys
    api_keys = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "XAI_API_KEY": os.getenv("XAI_API_KEY"),
        "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY"),
    }

    print("🔑 API Key Status:")
    for key, value in api_keys.items():
        status = "✅ SET" if value else "❌ NOT SET"
        print(f"   {key}: {status}")

    print("\n📋 Testing Models:")
    print("-" * 30)

    results = {}
    for model_name, model_id in MODELS_TO_TEST:
        results[model_name] = test_model(model_name, model_id)

    print("\n📊 Summary:")
    print("=" * 30)
    working_models = sum(results.values())
    total_models = len(results)

    for model_name, success in results.items():
        status = "✅ WORKING" if success else "❌ FAILED"
        print(f"   {model_name}: {status}")

    print(f"\n🎯 Result: {working_models}/{total_models} models working")

    if working_models == total_models:
        print("🎉 All models are working correctly!")
    else:
        print("⚠️  Some models failed - check API keys and model names")


if __name__ == "__main__":
    main()
