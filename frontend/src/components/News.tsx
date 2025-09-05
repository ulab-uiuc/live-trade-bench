import React, { useState } from 'react';
import './News.css';

interface NewsItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  published_at: string;
  impact: string;
  category: string;
  url: string;
  stock_symbol: string | null;
}

interface NewsProps {
  newsData: {
    stock: any[];
    polymarket: any[];
  };
  lastRefresh: Date;
  isLoading: boolean;
}

const News: React.FC<NewsProps> = ({ newsData, lastRefresh, isLoading }) => {
  const [activeCategory, setActiveCategory] = useState<'stock' | 'polymarket'>('stock');
  
  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#10b981';
      default: return '#6b7280';
    }
  };

  const getStockColor = (stockSymbol: string | null) => {
    if (!stockSymbol) return '#6b7280';
    const colorPalette = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
    let hash = 0;
    for (let i = 0; i < stockSymbol.length; i++) {
      hash = stockSymbol.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colorPalette[Math.abs(hash) % colorPalette.length];
  };

  const formatTimeAgo = (publishedAt: string) => {
    const diff = new Date().getTime() - new Date(publishedAt).getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    if (hours < 1) return 'Just now';
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  const newsItems = activeCategory === 'stock' ? newsData.stock : newsData.polymarket;

  if (isLoading && newsItems.length === 0) {
    return (
      <div className="loading-indicator">
        <span>Loading news...</span>
      </div>
    );
  }

  return (
    <div className="news-container">
      <div className="news-header">
        <h1>📰 Market News</h1>
        <div className="news-controls">
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
                  fontWeight: activeCategory === market ? 'bold' : 'normal'
                }}
              >
                {market === 'stock' ? 'Stock Market' : 'Polymarket'}
              </button>
            ))}
          </div>

          <div style={{
            fontSize: '0.875rem',
            color: '#9ca3af'
          }}>
            {newsItems.length} articles • Last updated: {lastRefresh.toLocaleTimeString()}
          </div>
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
        gap: '1.5rem'
      }}>
        {newsItems.map((news) => (
          <a
            key={news.id}
            href={news.url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              background: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '0.5rem',
              padding: '1.5rem',
              transition: 'all 0.2s ease',
              cursor: 'pointer',
              textDecoration: 'none',
              color: 'inherit',
              display: 'block'
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
                {news.stock_symbol && (
                  <span style={{
                    background: getStockColor(news.stock_symbol),
                    color: '#ffffff',
                    padding: '0.25rem 0.5rem',
                    borderRadius: '0.25rem',
                    fontSize: '0.75rem',
                    fontWeight: 'bold'
                  }}>
                    {news.stock_symbol}
                  </span>
                )}
                {/* Impact Tag */}
                <span style={{
                  background: getImpactColor(news.impact),
                  color: '#ffffff',
                  padding: '0.25rem 0.5rem',
                  borderRadius: '0.25rem',
                  fontSize: '0.75rem',
                  fontWeight: 'bold',
                  textTransform: 'uppercase'
                }}>
                  {news.impact}
                </span>
              </div>

              <span style={{
                fontSize: '0.75rem',
                color: '#9ca3af'
              }}>
                {formatTimeAgo(news.published_at)}
              </span>
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

            <p style={{
              fontSize: '0.875rem',
              color: '#d1d5db',
              lineHeight: '1.5',
              marginBottom: '1rem'
            }}>
              {news.summary}
            </p>

            {/* News footer */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontSize: '0.75rem',
              color: '#9ca3af'
            }}>
              <span>{news.source}</span>
              <span>
                {news.category === 'stock' ? '📈' : '🎯'} {news.category}
              </span>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
};

export default News;
