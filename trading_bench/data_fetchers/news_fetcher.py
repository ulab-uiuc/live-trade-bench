"""
News data fetcher for trading bench.

This module provides functions to fetch news data from Google News
using web scraping techniques.
"""

import random
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from tenacity import retry, retry_if_result, stop_after_attempt, wait_exponential


def is_rate_limited(response):
    """Check if the response indicates rate limiting (status code 429)"""
    return response.status_code == 429


@retry(
    retry=(retry_if_result(is_rate_limited)),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5),
)
def make_request(url, headers):
    """Make a request with retry logic for rate limiting"""
    # Random delay before each request to avoid detection
    time.sleep(random.uniform(2, 6))
    response = requests.get(url, headers=headers)
    return response


def fetch_news_data(
    query: str, start_date: str, end_date: str, max_pages: int = 10
) -> list:
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
    if '-' in start_date:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        start_date = start_date_obj.strftime('%m/%d/%Y')
    if '-' in end_date:
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        end_date = end_date_obj.strftime('%m/%d/%Y')

    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/101.0.4951.54 Safari/537.36'
        )
    }

    news_results = []
    page = 0

    while page < max_pages:
        offset = page * 10
        url = (
            f'https://www.google.com/search?q={query}'
            f'&tbs=cdr:1,cd_min:{start_date},cd_max:{end_date}'
            f'&tbm=nws&start={offset}'
        )

        try:
            response = make_request(url, headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            results_on_page = soup.select('div.SoaBEf')

            if not results_on_page:
                break  # No more results found

            for el in results_on_page:
                try:
                    link = el.find('a')['href']
                    title = el.select_one('div.MBeuO').get_text()
                    snippet = el.select_one('.GI74Re').get_text()
                    date = el.select_one('.LfVVr').get_text()
                    source = el.select_one('.NUnG9d span').get_text()
                    news_results.append(
                        {
                            'link': link,
                            'title': title,
                            'snippet': snippet,
                            'date': date,
                            'source': source,
                        }
                    )
                except Exception as e:
                    print(f'Error processing result: {e}')
                    # If one of the fields is not found, skip this result
                    continue

            # Check for the "Next" link (pagination)
            next_link = soup.find('a', id='pnnext')
            if not next_link:
                break

            page += 1

        except Exception as e:
            print(f'Failed after multiple retries: {e}')
            break

    # be polite with any rate limits
    time.sleep(1)

    return news_results
