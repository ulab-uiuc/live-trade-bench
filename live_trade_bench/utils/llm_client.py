"""
LLM utilities for trading decisions using litellm
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple


def _resolve_provider_and_model(model: str) -> Tuple[Optional[str], str, Optional[str]]:
    """
    Best-effort provider routing for model strings.

    Supported patterns:
    - Explicit prefixes:
        • together:<model_id>  -> provider=together_ai
        • openai:/anthropic:   -> respective providers (passthrough)
    - Heuristics (when no prefix):
        • contains 'qwen'  -> route to together_ai
        • contains 'llama' or 'meta-llama' -> route to together_ai

    Returns: (provider, normalized_model, api_key_env_var)
    """
    raw = model.strip()
    lower = raw.lower()

    # Explicit provider prefix parsing
    if ":" in raw and not raw.startswith("http"):
        prefix, rest = raw.split(":", 1)
        pfx = prefix.strip().lower()
        if pfx == "together":
            return "together_ai", rest.strip(), "TOGETHER_API_KEY"
        if pfx == "openai":
            return "openai", rest.strip(), "OPENAI_API_KEY"
        if pfx == "anthropic":
            return "anthropic", rest.strip(), "ANTHROPIC_API_KEY"
    # For any unsupported provider prefixes (e.g., dashscope/aliyun/xai/deepseek),
    # we do not route them; caller should use together:/openai:/anthropic:

    # Heuristic detection
    if "qwen" in lower:
        return "together_ai", raw, "TOGETHER_API_KEY"

    if "llama" in lower or "meta-llama" in lower:
        return "together_ai", raw, "TOGETHER_API_KEY"

    # Unknown / default -> let litellm infer
    return None, raw, None


def call_llm(
    messages: List[Dict[str, str]], model: str = "gpt-4o-mini", agent_name: str = "AI"
) -> Dict[str, Any]:
    """
    Call LLM using litellm

    Args:
        messages: List of message dicts with role and content
        model: Model name (e.g., "gpt-4o-mini", "claude-3-sonnet")
        agent_name: Name of the agent for error reporting

    Returns:
        Dict with success, content, and error info
    """
    try:
        import litellm

        # Check for API keys (Together/OpenAI/Anthropic/Gemini)
        api_keys = [
            os.getenv("OPENAI_API_KEY"),
            os.getenv("ANTHROPIC_API_KEY"),
            os.getenv("GEMINI_API_KEY"),
            os.getenv("TOGETHER_API_KEY"),
        ]
        if not any(api_keys):
            return {"success": False, "content": "", "error": "No API key found"}

        # Ensure proper message format for OpenAI API
        formatted_messages = []
        for msg in messages:
            content = msg.get("content", "")

            # Keep content as string for standard OpenAI API
            formatted_messages.append(
                {"role": msg["role"], "content": str(content)}  # Ensure it's a string
            )

        # Resolve provider/model and call LLM with provider-specific parameters
        provider, normalized_model, api_key_env = _resolve_provider_and_model(model)

        completion_params: Dict[str, Any] = {
            "model": normalized_model,
            "messages": formatted_messages,
        }

        # If we determined a provider (e.g., together_ai / aliyun), set it
        if provider:
            completion_params["custom_llm_provider"] = provider
        # Pass explicit API key when available
        if api_key_env and os.getenv(api_key_env):
            completion_params["api_key"] = os.getenv(api_key_env)

        # Handle GPT-5 specific requirements
        if "gpt-5" not in normalized_model.lower():
            # All other models use standard parameters
            completion_params.update({"temperature": 0.3, "max_tokens": 200})

        response = litellm.completion(**completion_params)

        content = response.choices[0].message.content
        return {"success": True, "content": content, "error": None}

    except ImportError:
        return {"success": False, "content": "", "error": "litellm not installed"}
    except Exception as e:
        print(f"⚠️ {agent_name}: LLM error: {e}")
        return {"success": False, "content": "", "error": str(e)}


def parse_trading_response(content: str) -> Dict[str, Any]:
    """Parse LLM response into trading decision format"""
    try:
        # Try to parse JSON response
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
        else:
            # If parsed is not a dict, create a dict with the parsed value
            return {"response": parsed}

    except json.JSONDecodeError:
        # Fallback parsing for non-JSON responses
        content_lower = content.lower()

        if "buy" in content_lower:
            action = "buy"
        elif "sell" in content_lower:
            action = "sell"
        else:
            action = "hold"

        return {
            "action": action,
            "quantity": 1,
            "confidence": 0.5,
            "reasoning": "Parsed from LLM response",
        }


def parse_portfolio_response(content: str) -> Dict[str, Any]:
    """Parse LLM response into portfolio allocation format"""
    try:
        # Clean the content - remove extra whitespace and newlines
        cleaned_content = content.strip()

        # Try to find JSON in the content
        start_idx = cleaned_content.find("{")
        end_idx = cleaned_content.rfind("}")

        if start_idx != -1 and end_idx != -1:
            json_content = cleaned_content[start_idx : end_idx + 1]
            parsed = json.loads(json_content)

            if isinstance(parsed, dict):
                # Validate that we have allocations
                if "allocations" in parsed and isinstance(parsed["allocations"], dict):
                    return parsed
                else:
                    print("⚠️ No 'allocations' field found in response")
                    return {"allocations": {}, "reasoning": "Invalid response format"}
            else:
                return {"allocations": {}, "reasoning": "Response is not a dictionary"}
        else:
            print("⚠️ No JSON object found in response")
            return {"allocations": {}, "reasoning": "No JSON object found"}

    except json.JSONDecodeError as e:
        print(f"⚠️ JSON parse failed: {e}")
        print(f"📝 Raw content: {content[:200]}...")

        # Try to extract allocation information from text
        content_lower = content.lower()
        if "allocation" in content_lower or "weight" in content_lower:
            print("⚠️ Using default allocation due to JSON parse failure")
            return {
                "allocations": {"default": 1.0},
                "reasoning": "Parsed from LLM response - default allocation",
            }
        else:
            return {
                "allocations": {},
                "reasoning": "Parsed from LLM response - no allocation change",
            }
