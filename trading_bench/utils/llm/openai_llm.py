import openai
from typing import Optional, List, Dict, Any

class OpenAILLMClient:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gpt-4", base_url: Optional[str] = None):
        if api_key is None:
            import os
            api_key = os.getenv("OPENAI_API_KEY")
        if base_url:
            self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = openai.OpenAI(api_key=api_key)
        self.model_name = model_name

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.1, max_tokens: int = 300) -> Any:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response 