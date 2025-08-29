import React, { useState, useEffect } from 'react';

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

const News: React.FC = () => {
  console.log('📰 News component is rendering!');

  const [selectedMarket, setSelectedMarket] = useState<'all' | 'stock' | 'polymarket'>('all');
  const [newsData, setNewsData] = useState<{
    stock: NewsItem[];
    polymarket: NewsItem[];
  }>({
    stock: [],
    polymarket: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchNews = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch news data from backend
      const response = await fetch('/api/news/?limit=50');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const allNews: NewsItem[] = await response.json();

      // Categorize news items (for now, all real news will be considered "stock" related)
      const stockNews = allNews.filter(news =>
        news.category === 'market' ||
        news.category === 'technology' ||
        news.category === 'economy' ||
        news.stock_symbol !== null
      );

      // For now, we don't have polymarket-specific news from the API
      const polymarketNews: NewsItem[] = [];

      setNewsData({
        stock: stockNews,
        polymarket: polymarketNews
      });
    } catch (error) {
      console.error('Error fetching news:', error);
      setError('Failed to load news data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNews();
  }, []);

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#10b981';
      default: return '#6b7280';
    }
  };

  const getImpactIcon = (impact: string) => {
    switch (impact) {
      case 'high': return '🔥';
      case 'medium': return '📊';
      case 'low': return '📰';
      default: return '📰';
    }
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

  if (loading) {
    return (
      <div style={{
        padding: '2rem',
        background: '#1f2937',
        color: '#ffffff',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⏳</div>
          <p style={{ fontSize: '1.125rem' }}>Loading news...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        padding: '2rem',
        background: '#1f2937',
        color: '#ffffff',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⚠️</div>
          <p style={{ fontSize: '1.125rem', marginBottom: '1rem' }}>{error}</p>
          <button
            onClick={fetchNews}
            style={{
              background: '#6366f1',
              color: 'white',
              border: 'none',
              padding: '0.75rem 1.5rem',
              borderRadius: '0.5rem',
              cursor: 'pointer',
              fontSize: '1rem'
            }}
          >
            Retry
          </button>
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
      // 强制覆盖CSS问题
      position: 'relative',
      zIndex: 1000,
      overflow: 'visible',
      display: 'block'
    }}>
      <h1 style={{
        fontSize: '2.5rem',
        color: '#ffffff',
        marginBottom: '2rem',
        borderBottom: '3px solid #6366f1',
        paddingBottom: '1rem',
        textAlign: 'center',
        // 强制覆盖
        position: 'relative',
        zIndex: 1001,
        display: 'block'
      }}>
        📰 Market News
      </h1>

      {/* 市场过滤器 */}
      <div style={{
        marginBottom: '2rem',
        display: 'flex',
        gap: '1rem',
        justifyContent: 'center',
        flexWrap: 'wrap',
        // 强制覆盖
        position: 'relative',
        zIndex: 1001,
        overflow: 'visible'
      }}>
        <button
          onClick={() => setSelectedMarket('all')}
          style={{
            background: selectedMarket === 'all' ? '#6366f1' : '#1f2937',
            color: '#ffffff',
            border: '1px solid #374151',
            padding: '0.75rem 1.5rem',
            borderRadius: '0.5rem',
            fontWeight: 'bold',
            cursor: 'pointer',
            transition: 'all 0.2s ease'
          }}
        >
          🌍 All Markets ({newsData.stock.length + newsData.polymarket.length})
        </button>
        <button
          onClick={() => setSelectedMarket('stock')}
          style={{
            background: selectedMarket === 'stock' ? '#10b981' : '#1f2937',
            color: '#ffffff',
            border: '1px solid #374151',
            padding: '0.75rem 1.5rem',
            borderRadius: '0.5rem',
            fontWeight: 'bold',
            cursor: 'pointer',
            transition: 'all 0.2s ease'
          }}
        >
          📈 Stock Market ({newsData.stock.length})
        </button>
        <button
          onClick={() => setSelectedMarket('polymarket')}
          style={{
            background: selectedMarket === 'polymarket' ? '#a78bfa' : '#1f2937',
            color: '#ffffff',
            border: '1px solid #374151',
            padding: '0.75rem 1.5rem',
            borderRadius: '0.5rem',
            fontWeight: 'bold',
            cursor: 'pointer',
            transition: 'all 0.2s ease'
          }}
        >
          🎯 Polymarket ({newsData.polymarket.length})
        </button>
      </div>

      {/* News grid */}
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
                <span style={{
                  background: getImpactColor(news.impact),
                  color: '#ffffff',
                  padding: '0.25rem 0.5rem',
                  borderRadius: '0.25rem',
                  fontSize: '0.75rem',
                  fontWeight: 'bold'
                }}>
                  {getImpactIcon(news.impact)} {news.stock_symbol}
                </span>
              </div>
              <span style={{
                color: '#9ca3af',
                fontSize: '0.75rem',
                fontWeight: '500'
              }}>
                {formatTimeAgo(news.published_at)}
              </span>
            </div>

            {/* News title */}
            <h3 style={{
              color: '#ffffff',
              fontSize: '1.125rem',
              marginBottom: '0.75rem',
              fontWeight: 'bold',
              lineHeight: '1.3'
            }}>
              {news.title}
            </h3>

            {/* News content */}
            <p style={{
              color: '#9ca3af',
              marginBottom: '1rem',
              lineHeight: '1.6',
              fontSize: '0.875rem'
            }}>
              {news.summary}
            </p>

            {/* News footer */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              paddingTop: '0.75rem',
              borderTop: '1px solid #374151'
            }}>
              <span style={{
                color: '#6366f1',
                fontSize: '0.75rem',
                fontWeight: '600'
              }}>
                📰 {news.source}
              </span>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <span style={{
                  color: getImpactColor(news.impact),
                  fontSize: '0.75rem',
                  fontWeight: '600'
                }}>
                  {news.impact.charAt(0).toUpperCase() + news.impact.slice(1)} Impact
                </span>
              </div>
            </div>
          </a>
        ))}
      </div>

      {/* Empty state */}
      {filteredNews.length === 0 && (
        <div style={{
          textAlign: 'center',
          padding: '3rem 1rem',
          color: '#94a3b8'
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📰</div>
          <p style={{ margin: 0, fontSize: '1.125rem', fontWeight: '500' }}>
            No news available for the selected market
          </p>
        </div>
      )}
    </div>
  );
};

export default News;
