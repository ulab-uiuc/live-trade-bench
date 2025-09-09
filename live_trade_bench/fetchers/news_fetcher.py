from datetime import datetime
from typing import Any, Dict, List

from bs4 import BeautifulSoup

from live_trade_bench.fetchers.base_fetcher import BaseFetcher


class NewsFetcher(BaseFetcher):
    def __init__(self, min_delay: float = 2.0, max_delay: float = 6.0):
        super().__init__(min_delay, max_delay)

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
    query: str, start_date: str, end_date: str, max_pages: int = 10, ticker: str = None
) -> List[Dict[str, Any]]:
    fetcher = NewsFetcher()
    news_items = fetcher.fetch(query, start_date, end_date, max_pages)

    # Add ticker tag to each news item if provided
    if ticker:
        for item in news_items:
            item["tag"] = ticker

    return news_items
