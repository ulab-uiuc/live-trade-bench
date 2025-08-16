"""
LLM utilities for trading decisions using litellm
"""

import json
import os
from typing import Any, Dict, List


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

        # Check for API keys
        if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
            return {"success": False, "content": "", "error": "No API key found"}

        # Ensure proper message format for OpenAI API
        formatted_messages = []
        for msg in messages:
            content = msg.get("content", "")

            # Keep content as string for standard OpenAI API
            formatted_messages.append(
                {"role": msg["role"], "content": str(content)}  # Ensure it's a string
            )

        # Call LLM with retry for different models
        try:
            response = litellm.completion(
                model=model,
                messages=formatted_messages,
                temperature=0.3,
                max_tokens=200,
            )
        except Exception as model_error:
            raise model_error

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
        return json.loads(content)

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
