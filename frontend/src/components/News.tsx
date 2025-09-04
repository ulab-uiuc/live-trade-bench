import React, { useState } from 'react';

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
    stock: NewsItem[];
    polymarket: NewsItem[];
  };
  lastRefresh: Date;
}

const News: React.FC<NewsProps> = ({ newsData, lastRefresh }) => {
  console.log('📰 News component rendering with background data!');

  const [selectedMarket, setSelectedMarket] = useState<'all' | 'stock' | 'polymarket'>('all');

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#10b981';
      default: return '#6b7280';
    }
  };

  // Generate unique color for each stock symbol
  const getStockColor = (stockSymbol: string | null) => {
    if (!stockSymbol) return '#6b7280';

    const colorPalette = [
      '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4',
      '#84cc16', '#f97316', '#ec4899', '#6366f1', '#14b8a6', '#a855f7',
      '#22c55e', '#eab308', '#dc2626', '#7c3aed', '#0891b2', '#65a30d',
      '#ea580c', '#be185d'
    ];

    let hash = 0;
    for (let i = 0; i < stockSymbol.length; i++) {
      const char = stockSymbol.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }

    const colorIndex = Math.abs(hash) % colorPalette.length;
    return colorPalette[colorIndex];
  };

  const formatTimeAgo = (publishedAt: string) => {
    const now = new Date();
    const published = new Date(publishedAt);
    const diffInHours = Math.floor((now.getTime() - published.getTime()) / (1000 * 60 * 60));

    if (diffInHours < 1) return 'Less than 1 hour ago';
    if (diffInHours === 1) return '1 hour ago';
    if (diffInHours < 24) return `${diffInHours} hours ago`;

    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays === 1) return '1 day ago';
    return `${diffInDays} days ago`;
  };

  const filteredNews = selectedMarket === 'all'
    ? [...newsData.stock, ...newsData.polymarket]
    : newsData[selectedMarket];

  console.log(`📊 Displaying ${filteredNews.length} news items (${selectedMarket})`);

  // Show loading state if no data yet
  if (filteredNews.length === 0) {
    return (
      <div
        style={{
          padding: '2rem',
          background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%)',
          color: '#ffffff',
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📰</div>
          <p style={{ fontSize: '1.125rem' }}>Loading news in background...</p>
          <p style={{ fontSize: '0.875rem', opacity: 0.7 }}>
            Last updated: {lastRefresh.toLocaleTimeString()}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      padding: '2rem',
      background: '#1f2937',
      color: '#ffffff',
      minHeight: '100vh',
      fontFamily: 'Arial, sans-serif',
      fontSize: '16px',
      position: 'relative',
      zIndex: 1000,
      overflow: 'visible',
      display: 'block'
    }}>
      <div style={{
        marginBottom: '2rem',
        borderBottom: '1px solid #374151',
        paddingBottom: '1rem'
      }}>
        <h1 style={{
          fontSize: '2rem',
          fontWeight: 'bold',
          marginBottom: '1rem',
          background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text'
        }}>
          📰 Market News
        </h1>

        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem'
        }}>
          <div style={{
            display: 'flex',
            gap: '0.5rem',
            background: '#374151',
            borderRadius: '0.5rem',
            padding: '0.25rem'
          }}>
            {(['all', 'stock', 'polymarket'] as const).map((market) => (
              <button
                key={market}
                onClick={() => setSelectedMarket(market)}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '0.375rem',
                  border: 'none',
                  background: selectedMarket === market ? '#6366f1' : 'transparent',
                  color: selectedMarket === market ? '#ffffff' : '#d1d5db',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  fontSize: '0.875rem',
                  fontWeight: selectedMarket === market ? 'bold' : 'normal'
                }}
              >
                {market === 'all' ? 'All Markets' :
                 market === 'stock' ? 'Stock Market' : 'Polymarket'}
              </button>
            ))}
          </div>

          <div style={{
            fontSize: '0.875rem',
            color: '#9ca3af'
          }}>
            {filteredNews.length} articles • Last updated: {lastRefresh.toLocaleTimeString()}
          </div>
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
        gap: '1.5rem'
      }}>
        {filteredNews.map((news) => (
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
