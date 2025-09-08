import random
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import requests  # type: ignore[import-untyped]
from tenacity import (
    retry,
    retry_if_exception_type,
    retry_if_result,
    stop_after_attempt,
    wait_exponential,
)


class BaseFetcher(ABC):
    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.default_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/101.0.4951.54 Safari/537.36"
            ),
            "Accept": "application/json",
        }

    def _rate_limit_delay(self) -> None:
        time.sleep(random.uniform(self.min_delay, self.max_delay))

    @staticmethod
    def is_rate_limited(response: Any) -> bool:
        try:
            return getattr(response, "status_code", None) == 429
        except Exception:
            return False

    @retry(
        retry=retry_if_result(lambda resp: BaseFetcher.is_rate_limited(resp)),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5),
    )
    def make_request(
        self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs: Any
    ) -> requests.Response:
        self._rate_limit_delay()

        if headers is None:
            headers = self.default_headers

        response = requests.get(url, headers=headers, **kwargs)
        return response

    @retry(
        retry=retry_if_exception_type((RuntimeError, Exception)),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(3),
    )
    def execute_with_retry(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    def validate_response(self, response: requests.Response, context: str = "") -> None:
        if not response.ok:
            raise RuntimeError(
                f"{context} failed with status {response.status_code}: {response.text}"
            )

    def safe_json_parse(self, response: requests.Response, context: str = "") -> Any:
        try:
            return response.json()
        except Exception as e:
            raise RuntimeError(f"{context} JSON parsing failed: {e}")

    @abstractmethod
    def fetch(self, *args: Any, **kwargs: Any) -> Any:
        pass

    def cleanup(self) -> None:
        pass

    def __enter__(self) -> "BaseFetcher":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.cleanup()
