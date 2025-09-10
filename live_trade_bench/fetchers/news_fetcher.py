from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from live_trade_bench.fetchers.base_fetcher import BaseFetcher
from live_trade_bench.fetchers.reddit_fetcher import TICKER_TO_COMPANY # Import TICKER_TO_COMPANY


class NewsFetcher(BaseFetcher):
    def __init__(self, min_delay: float = 2.0, max_delay: float = 6.0):
        super().__init__(min_delay, max_delay)

    def _parse_relative_time(self, date_str: str) -> Optional[float]:
        """Parses relative time strings (e.g., '2 hours ago') to Unix timestamp."""
        now = datetime.now()
        if "hour" in date_str:
            hours_ago = int(date_str.split(" ")[0])
            return (now - timedelta(hours=hours_ago)).timestamp()
        elif "day" in date_str:
            days_ago = int(date_str.split(" ")[0])
            return (now - timedelta(days=days_ago)).timestamp()
        elif "minute" in date_str:
            minutes_ago = int(date_str.split(" ")[0])
            return (now - timedelta(minutes=minutes_ago)).timestamp()
        elif "second" in date_str:
            seconds_ago = int(date_str.split(" ")[0])
            return (now - timedelta(seconds=seconds_ago)).timestamp()
        return None

    def fetch(
        self, query: str, start_date: str, end_date: str, max_pages: int = 10
    ) -> List[Dict[str, Any]]:
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
                    break

                for el in results_on_page:
                    try:
                        link_el = el.find("a")
                        if (
                            not link_el
                            or not hasattr(link_el, "attrs")
                            or "href" not in link_el.attrs
                        ):
                            continue
                        link = link_el.attrs["href"]

                        title_el = el.select_one("div.MBeuO")
                        if not title_el:
                            continue
                        title = title_el.get_text()

                        snippet_el = el.select_one(".GI74Re")
                        if not snippet_el:
                            continue
                        snippet = snippet_el.get_text()

                        date_el = el.select_one(".LfVVr")
                        if not date_el:
                            continue
                        date = date_el.get_text()

                        source_el = el.select_one(".NUnG9d span")
                        if not source_el:
                            continue
                        source = source_el.get_text()

                        # Convert relative time to Unix timestamp
                        parsed_date = self._parse_relative_time(date)
                        if parsed_date is None:
                            # Fallback if relative time parsing fails (e.g., specific date string)
                            try:
                                # Attempt to parse as a standard date string if it's not relative
                                parsed_date = datetime.strptime(date, "%b %d, %Y").timestamp() # e.g., 'Sep 09, 2025'
                            except ValueError:
                                parsed_date = datetime.now().timestamp() # Default to now if all parsing fails

                        news_results.append(
                            {
                                "link": link,
                                "title": title,
                                "snippet": snippet,
                                "date": parsed_date, # Store as Unix timestamp
                                "source": source,
                            }
                        )
                    except Exception as e:
                        print(f"Error processing result: {e}")
                        continue

                next_link = soup.find("a", id="pnnext")
                if not next_link:
                    break

                page += 1

            except Exception as e:
                print(f"Failed after multiple retries: {e}")
                break

        return news_results


def fetch_news_data(
    query: str, start_date: str, end_date: str, max_pages: int = 10, ticker: Optional[str] = None # Corrected type hint
) -> List[Dict[str, Any]]:
    fetcher = NewsFetcher()

    augmented_query = query
    if ticker and ticker.upper() in TICKER_TO_COMPANY:
        company_name = TICKER_TO_COMPANY[ticker.upper()]
        augmented_query = f"{query} OR {company_name}"
        print(f"  - News fetcher: Query augmented for ticker '{ticker}': '{augmented_query}'")
    
    news_items = fetcher.fetch(augmented_query, start_date, end_date, max_pages)

    # Add ticker tag to each news item if provided
    if ticker:
        for item in news_items:
            item["tag"] = ticker

    return news_items
