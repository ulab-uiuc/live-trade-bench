import React, { useState, useMemo } from 'react';
import './News.css';
import { getAssetColor } from '../utils/colors';
import type { NewsItem } from '../App'; // Import NewsItem type
import { formatTimeAgo } from '../utils/time'; // Import formatTimeAgo

interface NewsProps {
  newsData: {
    stock: NewsItem[]; // Use NewsItem type
    polymarket: NewsItem[]; // Use NewsItem type
  };
  lastRefresh: Date;
  isLoading: boolean;
}

const News: React.FC<NewsProps> = ({ newsData, lastRefresh, isLoading }) => {
  const [activeCategory, setActiveCategory] = useState<'stock' | 'polymarket'>('stock');
  const [sortBy, setSortBy] = useState<'ticker' | 'time'>('time');

  const getBrief = (news: NewsItem): string => {
    const text = news?.snippet || '';
    if (!text) return '';
    const s = String(text).trim();
    return s.length > 280 ? s.slice(0, 277) + '…' : s;
  };

  // Removed getPublished function

  // Collect and sort all unique tags for consistent color assignment
  const allUniqueTags = useMemo(() => {
    const tags = new Set<string>();
    newsData.stock.forEach(item => item.tag && tags.add(item.tag));
    newsData.polymarket.forEach(item => item.tag && tags.add(item.tag));
    return Array.from(tags).sort((a, b) => a.localeCompare(b));
  }, [newsData]);

  // Sort news items based on selected criteria
  const sortedNews = useMemo(() => {
    const news = newsData[activeCategory];
    if (!news) return [];

    return [...news].sort((a, b) => {
      if (sortBy === 'ticker') {
        const tickerA = a.tag || '';
        const tickerB = b.tag || '';
        return tickerA.localeCompare(tickerB);
      } else {
        // Sort by time (newest first)
        const timeA = new Date(a.date || 0).getTime();
        const timeB = new Date(b.date || 0).getTime();
        return timeB - timeA;
      }
    });
  }, [newsData, activeCategory, sortBy]);

  const getTagColor = (tag: string | null) => {
    if (!tag) return '#6b7280';
    // Find the index of the tag in the sorted list
    const index = allUniqueTags.indexOf(tag);
    if (index === -1) return '#6b7280'; // Fallback color if tag not found
    // 复用和 allocation 一致的颜色算法
    return getAssetColor(tag, index, activeCategory);
  };


  // Use sortedNews instead of direct newsData access

  if (isLoading && sortedNews.length === 0) {
    return (
      <div className="loading-indicator">
        <span>Loading news...</span>
      </div>
    );
  }

  return (
    <div className="news-container">
      <div className="news-header">
        <h1>Market News</h1>
        <p className="news-subtitle">
          Stay updated with the latest news affecting stock and polymarket prices.
        </p>
        <div className="news-controls">
          {/* Mobile Layout */}
          <div className="news-controls-mobile">
            <div className="news-controls-top-row">
              <div className="news-category-tabs">
                {(['stock', 'polymarket'] as const).map((market) => (
                  <button
                    key={market}
                    onClick={() => setActiveCategory(market)}
                    style={{
                      padding: '0.5rem 1rem',
                      borderRadius: '0.375rem',
                      border: 'none',
                      background: activeCategory === market ? '#6366f1' : 'transparent',
                      color: activeCategory === market ? '#ffffff' : '#d1d5db',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      fontSize: '0.875rem',
                      fontWeight: activeCategory === market ? 'bold' : 'normal',
                      minWidth: '100px',
                      textAlign: 'center'
                    }}
                  >
                    {market === 'stock' ? 'Stock' : 'Polymarket'}
                  </button>
                ))}
              </div>

              <div className="news-sort-controls">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as 'ticker' | 'time')}
                  className="news-sort-control"
                >
                  <option value="time">Sort by Time</option>
                  <option value="ticker">Sort by Ticker A-Z</option>
                </select>
              </div>
            </div>

            <div className="news-stats">
              {sortedNews.length} articles • Last updated: {lastRefresh.toLocaleTimeString()}
            </div>
          </div>

          {/* Desktop Layout */}
          <div className="news-controls-desktop">
            <div className="news-category-tabs">
              {(['stock', 'polymarket'] as const).map((market) => (
                <button
                  key={market}
                  onClick={() => setActiveCategory(market)}
                  style={{
                    padding: '0.5rem 1rem',
                    borderRadius: '0.375rem',
                    border: 'none',
                    background: activeCategory === market ? '#6366f1' : 'transparent',
                    color: activeCategory === market ? '#ffffff' : '#d1d5db',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    fontSize: '0.875rem',
                    fontWeight: activeCategory === market ? 'bold' : 'normal',
                    minWidth: '100px',
                    textAlign: 'center'
                  }}
                >
                  {market === 'stock' ? 'Stock' : 'Polymarket'}
                </button>
              ))}
            </div>

            <div className="news-stats">
              {sortedNews.length} articles • Last updated: {lastRefresh.toLocaleTimeString()}
            </div>

            <div className="news-sort-controls">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as 'ticker' | 'time')}
                className="news-sort-control"
              >
                <option value="time">Sort by Time</option>
                <option value="ticker">Sort by Ticker A-Z</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
        gap: '1.5rem'
      }}>
        {sortedNews.map((news) => (
          <a
            key={news.id}
            href={news.link}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              background: '#0f1419',
              border: '1px solid #374151',
              borderRadius: '0.5rem',
              padding: '1.5rem',
              transition: 'all 0.2s ease',
              cursor: 'pointer',
              textDecoration: 'none',
              color: 'inherit',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'flex-start',
              height: '100%'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = '#3b82f6';
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.15)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = '#374151';
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = 'none';
            }}
            onClick={(e) => {
              const target = e.currentTarget;
              target.style.transform = 'translateY(-1px) scale(0.98)';
              target.style.boxShadow = '0 2px 8px rgba(59, 130, 246, 0.25)';

              setTimeout(() => {
                if (target) {
                  target.style.transform = 'translateY(-2px)';
                  target.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.15)';
                }
              }, 150);
            }}
          >
            {/* News header */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              marginBottom: '1rem'
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                {/* Stock Symbol Tag */}
                {news.tag && (
                  <span style={{
                    color: getTagColor(news.tag),
                    fontSize: '0.75rem',
                    fontWeight: 'bold'
                  }}>
                    {news.tag.replace(/_(YES|NO)$/, '')}
                  </span>
                )}
              </div>

              <div style={{
                fontSize: '0.75rem',
                color: '#9ca3af',
                whiteSpace: 'nowrap',
                flexShrink: 0
              }}>
                {formatTimeAgo(news.date || '')}
              </div>
            </div>

            {/* News content */}
            <h3 style={{
              fontSize: '1.125rem',
              fontWeight: 'bold',
              marginBottom: '0.75rem',
              lineHeight: '1.4',
              color: '#ffffff'
            }}>
              {news.title}
            </h3>

            {getBrief(news) && (
              <p style={{
                fontSize: '0.875rem',
                color: '#d1d5db',
                lineHeight: '1.5',
                marginBottom: '1rem'
              }}>
                {getBrief(news)}
              </p>
            )}

            {/* News footer - stick to card bottom */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontSize: '0.75rem',
                color: '#9ca3af',
                marginTop: 'auto'
              }}
            >
              <span>{news.source}</span>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
};

export default News;
