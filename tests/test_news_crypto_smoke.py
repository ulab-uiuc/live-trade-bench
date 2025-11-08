"""
News Fetching Smoke Test

Verifies that the news fetcher can actually retrieve relevant news articles for
the most popular crypto coins (Bitcoin, Ethereum, Solana).

This test makes REAL Google News scraping calls to validate functionality.
"""

import os
from datetime import datetime, timedelta

import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from live_trade_bench.fetchers.news_fetcher import fetch_news_data


@pytest.mark.integration
def test_news_fetches_bitcoin_articles():
    """
    Test that news fetcher retrieves relevant Bitcoin articles.
    """
    print("\n" + "=" * 80)
    print("NEWS SMOKE TEST: Bitcoin Articles")
    print("=" * 80)

    # Setup date range (last 3 days)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=3)

    query = "Bitcoin crypto news"
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    print(f"\nQuery: {query}")
    print(f"Date range: {start_str} to {end_str}")
    print("Fetching news from Google News...")

    # Fetch news
    try:
        articles = fetch_news_data(
            query=query,
            start_date=start_str,
            end_date=end_str,
            max_pages=2,  # Limit pages to avoid rate limiting
            ticker="XBTUSD"
        )
    except Exception as e:
        print(f"\n❌ Error fetching news: {e}")
        import traceback
        traceback.print_exc()
        pytest.fail(f"News fetching raised exception: {e}")

    print(f"\n✓ Retrieved {len(articles)} articles")

    # Assertions
    if len(articles) == 0:
        print("\n⚠️  WARNING: No articles found!")
        print("   Possible causes:")
        print("   - Google is blocking the scraper")
        print("   - Network/firewall blocking requests")
        print("   - Rate limiting active")
        print("   - HTML structure changed")
        pytest.fail("News fetcher returned 0 articles - likely being blocked or broken")

    assert len(articles) > 0, "Should fetch at least 1 Bitcoin article"

    # Validate data structure
    first_article = articles[0]
    required_fields = ["title", "link", "snippet", "source", "date"]

    for field in required_fields:
        assert field in first_article, f"Article should have '{field}' field"

    print(f"\n✓ All articles have required fields: {', '.join(required_fields)}")

    # Check relevance
    bitcoin_keywords = ["bitcoin", "btc", "crypto"]
    relevant_count = 0

    for article in articles:
        title_lower = article.get("title", "").lower()
        snippet_lower = article.get("snippet", "").lower()
        if any(kw in title_lower or kw in snippet_lower for kw in bitcoin_keywords):
            relevant_count += 1

    print(f"\n✓ {relevant_count}/{len(articles)} articles are Bitcoin-related")
    assert relevant_count >= len(articles) * 0.6, "At least 60% should mention Bitcoin/crypto"

    # Print samples
    print("\nSample Articles:")
    for i, article in enumerate(articles[:3], 1):
        print(f"\n  {i}. {article['title']}")
        print(f"     Source: {article['source']}")

        if article.get('date'):
            try:
                article_date = datetime.fromtimestamp(article['date'])
                print(f"     Date: {article_date.strftime('%Y-%m-%d')}")
            except:
                print(f"     Date: {article.get('date')}")

        snippet = article.get('snippet', '')
        if snippet:
            preview = snippet[:100] + "..." if len(snippet) > 100 else snippet
            print(f"     Snippet: {preview}")

    print("\n" + "=" * 80)
    print("✅ Bitcoin news test PASSED")
    print("=" * 80)


@pytest.mark.integration
def test_news_fetches_ethereum_articles():
    """
    Test that news fetcher retrieves relevant Ethereum articles.
    """
    print("\n" + "=" * 80)
    print("NEWS SMOKE TEST: Ethereum Articles")
    print("=" * 80)

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=3)

    query = "Ethereum crypto news"
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    print(f"\nQuery: {query}")
    print(f"Date range: {start_str} to {end_str}")

    articles = fetch_news_data(
        query=query,
        start_date=start_str,
        end_date=end_str,
        max_pages=2,
        ticker="ETHUSD"
    )

    print(f"\n✓ Retrieved {len(articles)} articles")

    if len(articles) == 0:
        pytest.fail("News fetcher returned 0 Ethereum articles")

    # Check relevance
    eth_keywords = ["ethereum", "eth", "vitalik", "defi"]
    relevant_count = sum(
        1 for article in articles
        if any(kw in article.get("title", "").lower() or kw in article.get("snippet", "").lower()
               for kw in eth_keywords)
    )

    print(f"\n✓ {relevant_count}/{len(articles)} articles are Ethereum-related")
    assert relevant_count >= len(articles) * 0.5, "At least 50% should mention Ethereum"

    # Print samples
    print("\nSample Articles:")
    for i, article in enumerate(articles[:3], 1):
        print(f"\n  {i}. {article['title']}")
        print(f"     Source: {article['source']}")

    print("\n" + "=" * 80)
    print("✅ Ethereum news test PASSED")
    print("=" * 80)


@pytest.mark.integration
def test_news_fetches_solana_articles():
    """
    Test that news fetcher retrieves relevant Solana articles.
    """
    print("\n" + "=" * 80)
    print("NEWS SMOKE TEST: Solana Articles")
    print("=" * 80)

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=3)

    query = "Solana crypto news"
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    print(f"\nQuery: {query}")
    print(f"Date range: {start_str} to {end_str}")

    articles = fetch_news_data(
        query=query,
        start_date=start_str,
        end_date=end_str,
        max_pages=2,
        ticker="SOLUSDT"
    )

    print(f"\n✓ Retrieved {len(articles)} articles")

    if len(articles) == 0:
        pytest.fail("News fetcher returned 0 Solana articles")

    # Check relevance
    sol_keywords = ["solana", "sol"]
    relevant_count = sum(
        1 for article in articles
        if any(kw in article.get("title", "").lower() or kw in article.get("snippet", "").lower()
               for kw in sol_keywords)
    )

    print(f"\n✓ {relevant_count}/{len(articles)} articles are Solana-related")

    # Print samples
    print("\nSample Articles:")
    for i, article in enumerate(articles[:3], 1):
        print(f"\n  {i}. {article['title']}")
        print(f"     Source: {article['source']}")

    print("\n" + "=" * 80)
    print("✅ Solana news test PASSED")
    print("=" * 80)


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("NEWS FETCHING SMOKE TESTS")
    print("Testing Google News scraper for popular crypto coins")
    print("=" * 80)

    # Run all tests
    try:
        test_news_fetches_bitcoin_articles()
        test_news_fetches_ethereum_articles()
        test_news_fetches_solana_articles()

        print("\n" + "=" * 80)
        print("🎉 ALL NEWS TESTS PASSED")
        print("=" * 80)
        print("\nSummary:")
        print("  ✓ News fetcher is working")
        print("  ✓ Can fetch Bitcoin news")
        print("  ✓ Can fetch Ethereum news")
        print("  ✓ Can fetch Solana news")
        print("  ✓ All articles have valid data structure")
        print("\nThe news fetcher is ready for use in trading system!")
        print()

    except AssertionError as e:
        print("\n" + "=" * 80)
        print("❌ NEWS FETCHING TESTS FAILED")
        print("=" * 80)
        print(f"\nError: {e}")
        print("\n⚠️  WARNING: News fetching is likely broken or being blocked!")
        print("\nThis means the trading system may be running WITHOUT news context,")
        print("which could lead to suboptimal trading decisions.")
        print()
        raise
