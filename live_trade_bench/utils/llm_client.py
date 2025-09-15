from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple


def _resolve_provider_and_model(model: str) -> Tuple[Optional[str], str, Optional[str]]:
    raw = model.strip()

    if "/" in raw and not raw.startswith("http"):
        prefix, rest = raw.split("/", 1)
        pfx = prefix.strip().lower()
        if pfx == "together":
            return "together_ai", rest.strip(), "TOGETHER_API_KEY"
        if pfx == "openai":
            if rest == ("gpt-oss-120b"):
                return "together_ai", raw, "TOGETHER_API_KEY"
            return "openai", rest.strip(), "OPENAI_API_KEY"
        if pfx == "anthropic":
            return "anthropic", rest.strip(), "ANTHROPIC_API_KEY"

    return "together_ai", raw, "TOGETHER_API_KEY"

    # return None, raw, None


def call_llm(
    messages: List[Dict[str, str]],
    model: str = "gpt-4o-mini",
    agent_name: str = "default_agent",
) -> Dict[str, Any]:
    try:
        import litellm

        provider, normalized_model, api_key_env = _resolve_provider_and_model(model)

        completion_params: Dict[str, Any] = {
            "model": normalized_model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 16000,
        }

        if (
            "gpt-5" in normalized_model.lower()
            or "o3-2025-04-16" in normalized_model.lower()
        ):
            del completion_params["temperature"]
            del completion_params["max_tokens"]
        if provider:
            completion_params["custom_llm_provider"] = provider
        if api_key_env and os.getenv(api_key_env):
            completion_params["api_key"] = os.getenv(api_key_env)

        response = litellm.completion(**completion_params)
        content = response.choices[0].message.content
        print(f"✅ LLM ({agent_name}) call successful")
        return {"success": True, "content": content}

    except Exception as e:
        print(f"❌ LLM ({agent_name}) call failed: {e}")
        # Log the exception for debugging purposes
        import traceback

        traceback.print_exc()
        return {"success": False, "content": None, "error": str(e)}


def parse_trading_response(content: str) -> Dict[str, Any]:
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else {"response": parsed}
    except json.JSONDecodeError:
        content_lower = content.lower()
        action = (
            "buy"
            if "buy" in content_lower
            else "sell"
            if "sell" in content_lower
            else "hold"
        )
        return {
            "action": action,
            "quantity": 1,
            "confidence": 0.5,
            "reasoning": "Parsed from LLM response",
        }


def parse_allocation_response(content: str) -> Dict[str, Any]:
    try:
        cleaned_content = content.strip()
        start_idx = cleaned_content.find("{")
        end_idx = cleaned_content.rfind("}")

        if start_idx != -1 and end_idx != -1:
            json_content = cleaned_content[start_idx : end_idx + 1]
            parsed = json.loads(json_content)
            if (
                isinstance(parsed, dict)
                and "allocations" in parsed
                and isinstance(parsed["allocations"], dict)
            ):
                return parsed
    except json.JSONDecodeError:
        pass

    return {"allocations": {}, "reasoning": "Invalid response format"}
