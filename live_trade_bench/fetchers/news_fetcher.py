from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, quote_plus, urlparse

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

        # English patterns: "5 days ago", "1 hour ago"
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

        # Polish patterns: "5 dni temu", "16 godzin temu", "dzień temu"
        # Handle special case "dzień temu" (day ago) without number
        if t == "dzień temu":
            return (ref - timedelta(days=1)).timestamp()
        if t == "godzinę temu":
            return (ref - timedelta(hours=1)).timestamp()

        m = re.match(
            r"^\s*(\d+)\s+(sekund[ya]?|minut[ya]?|godzin[ya]?|dni)\s+temu\s*$", t
        )
        if m:
            num = int(m.group(1))
            unit = m.group(2)
            # Map Polish units to timedelta
            if unit.startswith("sekund"):
                delta = timedelta(seconds=num)
            elif unit.startswith("minut"):
                delta = timedelta(minutes=num)
            elif unit.startswith("godzin"):
                delta = timedelta(hours=num)
            elif unit == "dni":
                delta = timedelta(days=num)
            else:
                delta = timedelta(0)
            return (ref - delta).timestamp()

        # Absolute date formats
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

    def _extract_snippet_from_url(self, url: str) -> str:
        try:
            # Add small delay to avoid rate limiting
            import time

            time.sleep(0.5)

            # Fetch the article page with timeout
            resp = self.make_request(url, timeout=10)
            if resp.status_code != 200:
                return ""

            soup = BeautifulSoup(resp.text, "html.parser")

            # Try to find article content in common containers
            content_selectors = [
                "article p",
                "[itemprop='articleBody'] p",
                ".article-content p",
                ".post-content p",
                "main p",
                "p",
            ]

            for selector in content_selectors:
                paragraphs = soup.select(selector)
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    # Return first paragraph with substantial content (>50 chars)
                    if len(text) > 50:
                        # Limit snippet to 300 chars
                        return text[:300] if len(text) > 300 else text

            return ""

        except Exception:
            # Silently fail - snippet extraction is optional
            return ""

    def fetch(
        self, query: str, start_date: str, end_date: str, max_pages: int = 10
    ) -> List[Dict[str, Any]]:
        start_fmt, _ = self._normalize_date(start_date)
        end_fmt, ref_date = self._normalize_date(end_date)

        # Use HTML-specific headers for Google News scraping
        html_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",  # Removed 'br' - brotli package not installed
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        results: List[Dict[str, Any]] = []
        for page in range(max_pages):
            # URL-encode the query to handle spaces and special characters
            encoded_query = quote_plus(query)
            url = (
                f"https://www.google.com/search?q={encoded_query}"
                f"&tbs=cdr:1,cd_min:{start_fmt},cd_max:{end_fmt}"
                f"&tbm=nws&start={page * 10}"
            )
            try:
                resp = self.make_request(url, headers=html_headers, timeout=15)
                # Use resp.text instead of resp.content to handle gzip encoding properly
                soup = BeautifulSoup(resp.text, "html.parser")
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
                    # Try multiple snippet selectors (Google frequently changes these)
                    snippet_el = (
                        el.select_one(".GI74Re")
                        or el.select_one(".yXK7lf")
                        or el.select_one(".st")
                    )
                    date_el = el.select_one(".LfVVr")
                    source_el = el.select_one(".NUnG9d span")

                    # Snippet is optional - title, date, and source are required
                    if not (title_el and date_el and source_el):
                        continue

                    # Get snippet with 3-tier fallback
                    snippet = ""
                    if snippet_el:
                        snippet = snippet_el.get_text(strip=True)
                    elif (
                        link and page == 0
                    ):  # Only fetch from URL for first page to avoid slowdown
                        snippet = self._extract_snippet_from_url(link)

                    ts = self._parse_relative_or_absolute(
                        date_el.get_text(strip=True), ref_date
                    )

                    results.append(
                        {
                            "link": link,
                            "title": title_el.get_text(strip=True),
                            "snippet": snippet,
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
    print(
        f"  - News fetcher with query '{query}' and start_date '{start_date}' and end_date '{end_date}'"
    )
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
