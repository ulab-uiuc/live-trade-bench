"""
Async single-call LLM demo (true parallel requests)

Fires four requests concurrently using acall_llm + asyncio.gather:
- together:Qwen/Qwen2.5-7B-Instruct-Turbo
- together:meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo
- openai:gpt-5
- openai:gpt-4o-mini

Env: set TOGETHER_API_KEY and/or OPENAI_API_KEY as needed.
"""

import asyncio
import os
import sys
from typing import Any, Dict, List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from live_trade_bench.utils.llm_client import acall_llm


def build_messages(task: str) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": "You are a concise assistant. Answer in one sentence.",
        },
        {"role": "user", "content": task},
    ]


async def main() -> None:
    print("⚡ Async LLM Demo (parallel requests)")
    print("=" * 50)

    tasks: List[Tuple[str, str]] = [
        ("Qwen (Together)", "together:Qwen/Qwen2.5-7B-Instruct-Turbo"),
        ("Llama (Together)", "together:meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"),
        ("OpenAI GPT-5", "openai:gpt-5"),
        ("OpenAI GPT-4o-mini", "openai:gpt-4o-mini"),
    ]

    prompt = "Give me a one-sentence market outlook for the next week."

    async def run_one(label: str, model: str) -> Tuple[str, Dict[str, Any]]:
        res = await acall_llm(
            build_messages(prompt), model=model, agent_name=label, timeout=30
        )
        return label, res

    coros = [run_one(label, model) for label, model in tasks]
    results = await asyncio.gather(*coros, return_exceptions=True)

    print("\n=== Results ===")
    for item in results:
        if isinstance(item, Exception):
            print(f"• ERROR: {item}")
            continue
        label, res = item
        if res.get("success"):
            content = (res.get("content") or "").strip()
            print(f"• {label}: {content[:200]}")
        else:
            print(f"• {label}: ERROR -> {res.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())
