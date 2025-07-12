"""
Base fetcher class for trading bench.

This module provides a base class that all data fetchers should inherit from,
containing common functionality like retry logic, rate limiting, and error handling.
"""

import random
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Union

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    retry_if_result,
    stop_after_attempt,
    wait_exponential,
)


class BaseFetcher(ABC):
    """
    Base class for all data fetchers.

    Provides common functionality like:
    - Rate limiting with random delays
    - Retry logic for failed requests
    - Error handling and logging
    - Request headers management
    """

    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """
        Initialize the base fetcher.

        Args:
            min_delay: Minimum delay between requests in seconds
            max_delay: Maximum delay between requests in seconds
        """
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
        """Apply random delay to avoid rate limiting."""
        time.sleep(random.uniform(self.min_delay, self.max_delay))

    @staticmethod
    def is_rate_limited(response: requests.Response) -> bool:
        """Check if the response indicates rate limiting."""
        return response.status_code == 429

    @retry(
        retry=retry_if_result(lambda resp: BaseFetcher.is_rate_limited(resp)),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5),
    )
    def make_request(
        self, url: str, headers: Union[Dict[str, str], None] = None, **kwargs
    ) -> requests.Response:
        """
        Make a request with retry logic for rate limiting.

        Args:
            url: URL to request
            headers: Optional headers to use
            **kwargs: Additional arguments for requests.get

        Returns:
            requests.Response: The response object
        """
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
    def execute_with_retry(self, func, *args, **kwargs) -> Any:
        """
        Execute a function with retry logic.

        Args:
            func: Function to execute
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function execution
        """
        return func(*args, **kwargs)

    def validate_response(self, response: requests.Response, context: str = "") -> None:
        """
        Validate that a response is successful.

        Args:
            response: Response to validate
            context: Context string for error messages

        Raises:
            RuntimeError: If response is not successful
        """
        if not response.ok:
            raise RuntimeError(
                f"{context} failed with status {response.status_code}: {response.text}"
            )

    def safe_json_parse(self, response: requests.Response, context: str = "") -> Any:
        """
        Safely parse JSON response.

        Args:
            response: Response to parse
            context: Context string for error messages

        Returns:
            Parsed JSON data

        Raises:
            RuntimeError: If JSON parsing fails
        """
        try:
            return response.json()
        except Exception as e:
            raise RuntimeError(f"{context} JSON parsing failed: {e}")

    @abstractmethod
    def fetch(self, *args, **kwargs) -> Any:
        """
        Abstract method that all fetchers must implement.

        Returns:
            Fetched data in the appropriate format
        """
        pass

    def cleanup(self) -> None:
        """Cleanup method for any resources that need to be released."""
        # Default implementation does nothing
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()
