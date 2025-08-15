"""
News data fetcher for trading bench.

This module provides functions to fetch news data from Google News
using web scraping techniques.
"""

from datetime import datetime
from typing import Any, Dict, List

from bs4 import BeautifulSoup

from live_trade_bench.fetchers.base_fetcher import BaseFetcher


class NewsFetcher(BaseFetcher):
    """Fetcher for news data from Google News."""

    def __init__(self, min_delay: float = 2.0, max_delay: float = 6.0):
        """Initialize the news fetcher with longer delays for web scraping."""
        super().__init__(min_delay, max_delay)

    def fetch(
        self, query: str, start_date: str, end_date: str, max_pages: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetches news data for a given query and date range via Google News scraping.
        Args:
            query:      Search query string.
            start_date: YYYY-MM-DD or MM/DD/YYYY format.
            end_date:   YYYY-MM-DD or MM/DD/YYYY format.
            max_pages:  Maximum number of pages to scrape (default: 10).
        Returns:
            list: List of news articles with link, title, snippet, date, and source.
        """
        # Convert date format if needed
        if "-" in start_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
            start_date = start_date_obj.strftime("%m/%d/%Y")
        if "-" in end_date:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
            end_date = end_date_obj.strftime("%m/%d/%Y")

        news_results = []
        page = 0

        while page < max_pages:
            offset = page * 10
            url = (
                f"https://www.google.com/search?q={query}"
                f"&tbs=cdr:1,cd_min:{start_date},cd_max:{end_date}"
                f"&tbm=nws&start={offset}"
            )

            try:
                response = self.make_request(url)
                soup = BeautifulSoup(response.content, "html.parser")
                results_on_page = soup.select("div.SoaBEf")

                if not results_on_page:
                    break  # No more results found

                for el in results_on_page:
                    try:
                        link = el.find("a")["href"]
                        title = el.select_one("div.MBeuO").get_text()
                        snippet = el.select_one(".GI74Re").get_text()
                        date = el.select_one(".LfVVr").get_text()
                        source = el.select_one(".NUnG9d span").get_text()
                        news_results.append(
                            {
                                "link": link,
                                "title": title,
                                "snippet": snippet,
                                "date": date,
                                "source": source,
                            }
                        )
                    except Exception as e:
                        print(f"Error processing result: {e}")
                        # If one of the fields is not found, skip this result
                        continue

                # Check for the "Next" link (pagination)
                next_link = soup.find("a", id="pnnext")
                if not next_link:
                    break

                page += 1

            except Exception as e:
                print(f"Failed after multiple retries: {e}")
                break

        return news_results


def fetch_news_data(
    query: str, start_date: str, end_date: str, max_pages: int = 10
) -> List[Dict[str, Any]]:
    """
    Fetches news data for a given query and date range via Google News scraping.
    Args:
        query:      Search query string.
        start_date: YYYY-MM-DD or MM/DD/YYYY format.
        end_date:   YYYY-MM-DD or MM/DD/YYYY format.
        max_pages:  Maximum number of pages to scrape (default: 10).
    Returns:
        list: List of news articles with link, title, snippet, date, and source.
    """
    fetcher = NewsFetcher()
    return fetcher.fetch(query, start_date, end_date, max_pages)
