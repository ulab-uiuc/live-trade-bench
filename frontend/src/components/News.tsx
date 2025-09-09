import React, { useState } from 'react';
import './News.css';

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


  const getStockColor = (tag: string | null) => {
    if (!tag) return '#6b7280';
    const colorPalette = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
    let hash = 0;
    for (let i = 0; i < tag.length; i++) {
      hash = tag.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colorPalette[Math.abs(hash) % colorPalette.length];
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
        <h1>Market News</h1>
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
            href={news.link}
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
                    background: getStockColor(news.tag),
                    color: '#ffffff',
                    padding: '0.25rem 0.5rem',
                    borderRadius: '0.25rem',
                    fontSize: '0.75rem',
                    fontWeight: 'bold'
                  }}>
                    {news.tag}
                  </span>
                )}
              </div>

              <span style={{
                fontSize: '0.75rem',
                color: '#9ca3af'
              }}>
                {news.published_at}
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
