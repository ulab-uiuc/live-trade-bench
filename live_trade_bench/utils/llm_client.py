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
        api_keys = [
            os.getenv("OPENAI_API_KEY"),
            os.getenv("ANTHROPIC_API_KEY"),
            os.getenv("GEMINI_API_KEY"),
            os.getenv("XAI_API_KEY"),
            os.getenv("DEEPSEEK_API_KEY"),
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

        # Call LLM with model-specific parameters
        completion_params: Dict[str, Any] = {
            "model": model,
            "messages": formatted_messages,
        }

        # Handle GPT-5 specific requirements
        if "gpt-5" in model.lower():
            # GPT-5 only supports max_completion_tokens and default temperature
            completion_params.update({"max_completion_tokens": 200})
        else:
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
