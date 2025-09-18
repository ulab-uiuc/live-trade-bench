from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from live_trade_bench.fetchers.base_fetcher import BaseFetcher


class NewsFetcher(BaseFetcher):
    def __init__(self, min_delay: float = 2.0, max_delay: float = 6.0):
        super().__init__(min_delay, max_delay)

    def _normalize_date(
        self, s: str, fallback_now: Optional[datetime] = None
    ) -> tuple[str, datetime]:
        if fallback_now is None:
            fallback_now = datetime.now()
        s = s.strip()
        if "-" in s:
            dt = datetime.strptime(s, "%Y-%m-%d")
            return dt.strftime("%m/%d/%Y"), dt
        if "/" in s:
            try:
                dt = datetime.strptime(s, "%m/%d/%Y")
                return s, dt
            except ValueError:
                pass
        return fallback_now.strftime("%m/%d/%Y"), fallback_now

    def _parse_relative_or_absolute(self, text: str, ref: datetime) -> float:
        t = text.strip().lower()
        m = re.match(r"^\s*(\d+)\s+(second|minute|hour|day)s?\s+ago\s*$", t)
        if m:
            num = int(m.group(1))
            unit = m.group(2)
            delta = {
                "second": timedelta(seconds=num),
                "minute": timedelta(minutes=num),
                "hour": timedelta(hours=num),
                "day": timedelta(days=num),
            }[unit]
            return (ref - delta).timestamp()
        for fmt in ("%b %d, %Y", "%B %d, %Y"):
            try:
                return datetime.strptime(text.strip(), fmt).timestamp()
            except ValueError:
                continue
        return ref.timestamp()

    def _clean_google_href(self, href: str) -> str:
        if href.startswith("/url?"):
            qs = parse_qs(urlparse(href).query)
            if "q" in qs and qs["q"]:
                return qs["q"][0]
        return href

    def fetch(
        self, query: str, start_date: str, end_date: str, max_pages: int = 10
    ) -> List[Dict[str, Any]]:
        start_fmt, _ = self._normalize_date(start_date)
        end_fmt, ref_date = self._normalize_date(end_date)

        results: List[Dict[str, Any]] = []
        for page in range(max_pages):
            url = (
                f"https://www.google.com/search?q={query}"
                f"&tbs=cdr:1,cd_min:{start_fmt},cd_max:{end_fmt}"
                f"&tbm=nws&start={page * 10}"
            )
            try:
                resp = self.make_request(url, timeout=15)
                soup = BeautifulSoup(resp.content, "html.parser")
            except Exception as e:
                print(f"Request/parse failed: {e}")
                break

            cards = soup.select("div.SoaBEf")
            if not cards:
                break

            for el in cards:
                try:
                    a = el.find("a")
                    if not a or "href" not in a.attrs:
                        continue
                    link = self._clean_google_href(a["href"])

                    title_el = el.select_one("div.MBeuO")
                    snippet_el = el.select_one(".GI74Re")
                    date_el = el.select_one(".LfVVr")
                    source_el = el.select_one(".NUnG9d span")
                    if not (title_el and snippet_el and date_el and source_el):
                        continue

                    ts = self._parse_relative_or_absolute(
                        date_el.get_text(strip=True), ref_date
                    )

                    results.append(
                        {
                            "link": link,
                            "title": title_el.get_text(strip=True),
                            "snippet": snippet_el.get_text(strip=True),
                            "date": ts,
                            "source": source_el.get_text(strip=True),
                        }
                    )
                except Exception as e:
                    print(f"Error processing result: {e}")
                    continue

            if not soup.find("a", id="pnnext"):
                break

        return results


def fetch_news_data(
    query: str,
    start_date: str,
    end_date: str,
    max_pages: int = 1,
    ticker: Optional[str] = None,
    target_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    fetcher = NewsFetcher()
    print(f"  - News fetcher with query '{query}'")
    news_items = fetcher.fetch(query, start_date, end_date, max_pages)

    if ticker:
        for it in news_items:
            it["tag"] = ticker

    valid_news = [it for it in news_items if it.get("date") is not None]

    if target_date and valid_news:
        try:
            target_ts = datetime.strptime(target_date, "%Y-%m-%d").timestamp()
            sorted_news = sorted(valid_news, key=lambda x: abs(x["date"] - target_ts))
        except Exception:
            sorted_news = sorted(valid_news, key=lambda x: x["date"], reverse=True)
    else:
        sorted_news = sorted(valid_news, key=lambda x: x["date"], reverse=True)

    return sorted_news
