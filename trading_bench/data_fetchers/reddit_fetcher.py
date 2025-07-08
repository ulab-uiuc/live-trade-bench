"""
Reddit data fetcher for trading bench.

This module provides functions to fetch Reddit posts and comments data
from local JSONL files organized by categories and subreddits.
"""

import os
import re
import json
from datetime import datetime
from typing import Annotated, List, Dict, Optional


# Company name mapping for ticker symbols
TICKER_TO_COMPANY = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Google",
    "AMZN": "Amazon",
    "TSLA": "Tesla",
    "NVDA": "Nvidia",
    "TSM": "Taiwan Semiconductor Manufacturing Company OR TSMC",
    "JPM": "JPMorgan Chase OR JP Morgan",
    "JNJ": "Johnson & Johnson OR JNJ",
    "V": "Visa",
    "WMT": "Walmart",
    "META": "Meta OR Facebook",
    "AMD": "AMD",
    "INTC": "Intel",
    "QCOM": "Qualcomm",
    "BABA": "Alibaba",
    "ADBE": "Adobe",
    "NFLX": "Netflix",
    "CRM": "Salesforce",
    "PYPL": "PayPal",
    "PLTR": "Palantir",
    "MU": "Micron",
    "SQ": "Block OR Square",
    "ZM": "Zoom",
    "CSCO": "Cisco",
    "SHOP": "Shopify",
    "ORCL": "Oracle",
    "X": "Twitter OR X",
    "SPOT": "Spotify",
    "AVGO": "Broadcom",
    "ASML": "ASML ",
    "TWLO": "Twilio",
    "SNAP": "Snap Inc.",
    "TEAM": "Atlassian",
    "SQSP": "Squarespace",
    "UBER": "Uber",
    "ROKU": "Roku",
    "PINS": "Pinterest",
}


def fetch_top_from_category(
    category: Annotated[
        str, "Category to fetch top post from. Collection of subreddits."
    ],
    date: Annotated[str, "Date to fetch top posts from."],
    max_limit: Annotated[int, "Maximum number of posts to fetch."],
    query: Annotated[str, "Optional query to search for in the subreddit."] = None,
) -> List[Dict]:
    """
    Fetches top Reddit posts from a specific category and date.
    
    Args:
        category: Category to fetch top post from. Collection of subreddits.
        date: Date to fetch top posts from in YYYY-MM-DD format.
        max_limit: Maximum number of posts to fetch.
        query: Optional ticker symbol to search for in company news.
    
    Returns:
        List of dictionaries containing post data with title, content, url, upvotes, and posted_date.
    
    Raises:
        ValueError: If max_limit is less than the number of files in the category.
        FileNotFoundError: If the data path or category directory doesn't exist.
    """
    base_path = "reddit_data"
    
    # Validate data path exists
    if not os.path.exists(base_path):
        raise FileNotFoundError(f"Data path '{base_path}' does not exist")
    
    category_path = os.path.join(base_path, category)
    if not os.path.exists(category_path):
        raise FileNotFoundError(f"Category path '{category_path}' does not exist")
    
    all_content = []
    
    # Get list of JSONL files in the category
    jsonl_files = [f for f in os.listdir(category_path) if f.endswith('.jsonl')]
    
    if not jsonl_files:
        raise ValueError(f"No JSONL files found in category '{category}'")
    
    if max_limit < len(jsonl_files):
        raise ValueError(
            "REDDIT FETCHING ERROR: max limit is less than the number of files in the category. "
            "Will not be able to fetch any posts"
        )
    
    limit_per_subreddit = max_limit // len(jsonl_files)
    
    for data_file in jsonl_files:
        all_content_curr_subreddit = []
        
        file_path = os.path.join(category_path, data_file)
        
        try:
            with open(file_path, "rb") as f:
                for line in f:
                    # Skip empty lines
                    if not line.strip():
                        continue
                    
                    try:
                        parsed_line = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    
                    # Select only lines that are from the date
                    post_date = datetime.utcfromtimestamp(
                        parsed_line["created_utc"]
                    ).strftime("%Y-%m-%d")
                    
                    if post_date != date:
                        continue
                    
                    # If is company_news, check that the title or the content has the company's name (query) mentioned
                    if "company" in category and query:
                        search_terms = []
                        if query in TICKER_TO_COMPANY:
                            if "OR" in TICKER_TO_COMPANY[query]:
                                search_terms = TICKER_TO_COMPANY[query].split(" OR ")
                            else:
                                search_terms = [TICKER_TO_COMPANY[query]]
                        
                        search_terms.append(query)
                        
                        found = False
                        for term in search_terms:
                            if re.search(
                                term, parsed_line["title"], re.IGNORECASE
                            ) or re.search(term, parsed_line["selftext"], re.IGNORECASE):
                                found = True
                                break
                        
                        if not found:
                            continue
                    
                    post = {
                        "title": parsed_line["title"],
                        "content": parsed_line["selftext"],
                        "url": parsed_line["url"],
                        "upvotes": parsed_line["ups"],
                        "posted_date": post_date,
                        "subreddit": data_file.replace('.jsonl', ''),
                        "score": parsed_line.get("score", 0),
                        "num_comments": parsed_line.get("num_comments", 0),
                        "author": parsed_line.get("author", ""),
                        "created_utc": parsed_line["created_utc"]
                    }
                    
                    all_content_curr_subreddit.append(post)
                    
        except Exception as e:
            print(f"Error reading file {data_file}: {e}")
            continue
        
        # Sort by upvotes in descending order
        all_content_curr_subreddit.sort(key=lambda x: x["upvotes"], reverse=True)
        
        all_content.extend(all_content_curr_subreddit[:limit_per_subreddit])
    
    return all_content


def fetch_reddit_posts_by_ticker(
    ticker: str,
    date: str,
    max_limit: int = 50
) -> List[Dict]:
    """
    Fetches Reddit posts specifically mentioning a given ticker symbol.
    
    Args:
        ticker: Stock ticker symbol to search for.
        date: Date to fetch posts from in YYYY-MM-DD format.
        max_limit: Maximum number of posts to fetch.
    
    Returns:
        List of dictionaries containing post data.
    """
    return fetch_top_from_category(
        category="company_news",
        date=date,
        max_limit=max_limit,
        query=ticker
    )


def fetch_reddit_sentiment_data(
    category: str,
    date: str,
    max_limit: int = 100
) -> List[Dict]:
    """
    Fetches Reddit posts for sentiment analysis.
    
    Args:
        category: Category of subreddits to fetch from.
        date: Date to fetch posts from in YYYY-MM-DD format.
        max_limit: Maximum number of posts to fetch.
    
    Returns:
        List of dictionaries containing post data with sentiment-relevant fields.
    """
    posts = fetch_top_from_category(
        category=category,
        date=date,
        max_limit=max_limit
    )
    
    # Add sentiment analysis fields
    for post in posts:
        post["text_for_sentiment"] = f"{post['title']} {post['content']}"
        post["engagement_score"] = post["upvotes"] + (post["num_comments"] * 2)
    
    return posts


def get_available_categories() -> List[str]:
    """
    Get list of available categories in the Reddit data.
    
    Returns:
        List of available category names.
    """
    data_path = "reddit_data"
    if not os.path.exists(data_path):
        return []
    
    return [d for d in os.listdir(data_path) 
            if os.path.isdir(os.path.join(data_path, d))]


def get_available_dates(category: str) -> List[str]:
    """
    Get list of available dates for a specific category.
    
    Args:
        category: Category name.
    
    Returns:
        List of available dates in YYYY-MM-DD format.
    """
    data_path = "reddit_data"
    category_path = os.path.join(data_path, category)
    if not os.path.exists(category_path):
        return []
    
    dates = set()
    
    for data_file in os.listdir(category_path):
        if not data_file.endswith('.jsonl'):
            continue
            
        file_path = os.path.join(category_path, data_file)
        
        try:
            with open(file_path, "rb") as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    try:
                        parsed_line = json.loads(line)
                        post_date = datetime.utcfromtimestamp(
                            parsed_line["created_utc"]
                        ).strftime("%Y-%m-%d")
                        dates.add(post_date)
                    except (json.JSONDecodeError, KeyError):
                        continue
                        
        except Exception:
            continue
    
    return sorted(list(dates))


def get_reddit_statistics(
    category: str,
    date: str
) -> Dict:
    """
    Get statistics about Reddit posts for a category and date.
    
    Args:
        category: Category name.
        date: Date in YYYY-MM-DD format.
    
    Returns:
        Dictionary containing statistics about the posts.
    """
    posts = fetch_top_from_category(
        category=category,
        date=date,
        max_limit=1000  # Get all posts for statistics
    )
    
    if not posts:
        return {
            "total_posts": 0,
            "total_upvotes": 0,
            "total_comments": 0,
            "avg_upvotes": 0,
            "avg_comments": 0,
            "top_post": None,
            "subreddits": []
        }
    
    total_upvotes = sum(post["upvotes"] for post in posts)
    total_comments = sum(post["num_comments"] for post in posts)
    subreddits = list(set(post["subreddit"] for post in posts))
    
    # Find top post
    top_post = max(posts, key=lambda x: x["upvotes"])
    
    return {
        "total_posts": len(posts),
        "total_upvotes": total_upvotes,
        "total_comments": total_comments,
        "avg_upvotes": total_upvotes / len(posts),
        "avg_comments": total_comments / len(posts),
        "top_post": {
            "title": top_post["title"],
            "upvotes": top_post["upvotes"],
            "subreddit": top_post["subreddit"]
        },
        "subreddits": subreddits
    } 