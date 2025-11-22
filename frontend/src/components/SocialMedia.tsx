import React, { useState, useMemo } from 'react';
import './SocialMedia.css';
import { getAssetColor } from '../utils/colors';
import type { SocialPost } from '../App'; // Import SocialPost type
import { formatTimeAgo } from '../utils/time';

interface SocialMediaProps {
  socialData: {
    stock: SocialPost[]; // Use SocialPost type
    polymarket: SocialPost[]; // Use SocialPost type
    bitmex: SocialPost[]; // Use SocialPost type
  };
  lastRefresh: Date;
  isLoading: boolean;
}

const SocialMedia: React.FC<SocialMediaProps> = ({ socialData, lastRefresh, isLoading }) => {
  const [activeCategory, setActiveCategory] = useState<'stock' | 'polymarket' | 'bitmex'>('stock');
  const [sortBy, setSortBy] = useState<'ticker' | 'time'>('time');

  const posts = useMemo(() => {
    let rawPosts: SocialPost[] = [];

    if (activeCategory === 'stock') {
      rawPosts = socialData.stock;
    } else if (activeCategory === 'polymarket') {
      rawPosts = socialData.polymarket;
    } else if (activeCategory === 'bitmex') {
      rawPosts = socialData.bitmex;
    }

    console.log("DEBUG: activeCategory in posts useMemo", activeCategory, "posts count:", rawPosts.length); // Debug activeCategory

    const mappedPosts = rawPosts.map((post: SocialPost, index: number) => {
      if (activeCategory === 'polymarket') {
        console.log("DEBUG: Polymarket post data", { question: post.question, tag: post.tag, id: post.id });
      }
      return {
        ...post,
        id: post.id || `${activeCategory}-${index}`,
        // Removed sentiment fallback
      };
    });

    // Sort posts based on selected criteria
    return mappedPosts.sort((a, b) => {
      if (sortBy === 'ticker') {
        const tickerA = a.tag || '';
        const tickerB = b.tag || '';
        return tickerA.localeCompare(tickerB);
      } else {
        // Sort by time (newest first)
        const timeA = new Date(a.created_at || 0).getTime();
        const timeB = new Date(b.created_at || 0).getTime();
        return timeB - timeA;
      }
    });
  }, [activeCategory, socialData.stock, socialData.polymarket, socialData.bitmex, sortBy]);

  // Collect and sort all unique tags for consistent color assignment
  const allUniqueTags = useMemo(() => {
    const tags = new Set<string>();
    socialData.stock.forEach(item => {
      item.stock_symbols?.forEach((symbol: string) => tags.add(symbol));
      item.tag && tags.add(item.tag);
    });
    socialData.polymarket.forEach(item => {
      item.question && tags.add(item.question);
      item.tag && tags.add(item.tag);
    });
    socialData.bitmex.forEach(item => {
      item.tag && tags.add(item.tag);
    });
    return Array.from(tags).sort((a, b) => a.localeCompare(b));
  }, [socialData]);

  // Removed getSentimentColor function

  const getTagColor = (tag: string | null) => {
    if (!tag) return '#6b7280';
    // Find the index of the tag in the sorted list
    const index = allUniqueTags.indexOf(tag);
    if (index === -1) return '#6b7280'; // Fallback color if tag not found
    return getAssetColor(tag, index, activeCategory);
  };

  if (isLoading && posts.length === 0) {
    return (
      <div className="loading-indicator">
        <span>Loading social media feeds...</span>
      </div>
    );
  }

  return (
    <div className="social-media-container">
      <div className="social-media-header">
        <h1>Social Media</h1>
        <p className="social-media-subtitle">
          Track real-time social media discussions about stocks, polymarkets, and crypto.
        </p>
        <div className="social-media-controls">
          {/* Mobile Layout */}
          <div className="social-media-controls-mobile">
            <div className="social-media-controls-top-row">
              <div className="social-media-category-tabs">
                {(['stock', 'polymarket', 'bitmex'] as const).map((market) => (
                  <button
                    key={market}
                    onClick={() => setActiveCategory(market)}
                    className={activeCategory === market ? 'active' : ''}
                  >
                    {market === 'stock' ? 'Stock' : market === 'polymarket' ? 'Polymarket' : 'BitMEX'}
                  </button>
                ))}
              </div>

              <div className="social-media-sort-controls">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as 'ticker' | 'time')}
                  className="social-media-sort-control"
                >
                  <option value="time">Sort by Time</option>
                  <option value="ticker">Sort by Ticker A-Z</option>
                </select>
              </div>
            </div>

            <div className="social-media-stats">
              {posts.length} posts • Last updated: {lastRefresh.toLocaleTimeString()}
            </div>
          </div>

          {/* Desktop Layout */}
          <div className="social-media-controls-desktop">
            <div className="social-media-category-tabs">
              {(['stock', 'polymarket', 'bitmex'] as const).map((market) => (
                <button
                  key={market}
                  onClick={() => setActiveCategory(market)}
                  className={activeCategory === market ? 'active' : ''}
                >
                  {market === 'stock' ? 'Stock' : market === 'polymarket' ? 'Polymarket' : 'BitMEX'}
                </button>
              ))}
            </div>

            <div className="social-media-stats">
              {posts.length} posts • Last updated: {lastRefresh.toLocaleTimeString()}
            </div>

            <div className="social-media-sort-controls">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as 'ticker' | 'time')}
                className="social-media-sort-control"
              >
                <option value="time">Sort by Time</option>
                <option value="ticker">Sort by Ticker A-Z</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <div className="social-media-grid" key={activeCategory}>
        {posts.map((post) => (
          <div
            key={post.id}
            className="social-media-card"
            onClick={() => {
              if (post.url) {
                window.open(post.url, '_blank', 'noopener,noreferrer');
              }
            }}
          >
            {/* Post header */}
            <div className="social-media-card-header">
              <div className="social-media-tags">
                {/* Stock Symbol Tags */}
                {activeCategory === 'stock' && post.stock_symbols && post.stock_symbols.length > 0 && (
                  post.stock_symbols.map((symbol: string) => (
                    <span key={symbol} className="social-media-tag" style={{ color: getTagColor(symbol) }}>
                      {symbol}
                    </span>
                  ))
                )}

                {/* Stock Tag (in addition to stock_symbols) */}
                {activeCategory === 'stock' && post.tag && (
                  <span className="social-media-tag" style={{ color: getTagColor(post.tag) }}>
                    {post.tag}
                  </span>
                )}

                {/* Polymarket Question Tag */}
                {activeCategory === 'polymarket' && (post.question || post.tag) && (
                  <span className="social-media-tag" style={{ color: getTagColor(post.question || post.tag || null) }}>
                    {post.question || post.tag}
                  </span>
                )}

                {/* BitMEX Tag */}
                {activeCategory === 'bitmex' && post.tag && (
                  <span className="social-media-tag" style={{ color: getTagColor(post.tag) }}>
                    {post.tag}
                  </span>
                )}
              </div>

              <div className="social-media-time">
                {formatTimeAgo(post.created_at || '')}
              </div>
            </div>

            {/* Post content */}
            <div className="social-media-content-wrapper">
              {post.title && <h3 className="social-media-title">{post.title}</h3>}
              <p className="social-media-content">
                {post.content && post.content.length > 200 ? `${post.content.substring(0, 200)}...` : post.content}
              </p>
            </div>

            {/* Post footer */}
            <div className="social-media-footer">
              <div className="social-media-metrics">
                <span>
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="feather feather-heart"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
                  {post.upvotes || 0}
                </span>
                <span>
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="feather feather-message-square"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                  {post.num_comments || 0}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SocialMedia;
