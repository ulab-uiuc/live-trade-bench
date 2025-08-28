import React, { useState } from 'react';

const News: React.FC = () => {
  console.log('📰 News component is rendering!');
  
  const [selectedMarket, setSelectedMarket] = useState<'all' | 'stock' | 'polymarket'>('all');

  // 模拟新闻数据 - 按市场分类
  const newsData = {
    stock: [
      {
        id: '1',
        title: '🚀 Tech Stocks Rally on AI Breakthrough',
        content: 'Major technology companies saw significant gains following the announcement of a new artificial intelligence breakthrough that could revolutionize the industry.',
        category: 'Technology',
        time: '2 hours ago',
        source: 'Reuters',
        sentiment: 'positive'
      },
      {
        id: '2',
        title: '📈 Market Analysis: Q4 Earnings Preview',
        content: 'Analysts predict strong Q4 earnings across multiple sectors, with particular focus on consumer goods and financial services companies.',
        category: 'Analysis',
        time: '4 hours ago',
        source: 'Bloomberg',
        sentiment: 'positive'
      },
      {
        id: '3',
        title: '🏦 Federal Reserve Signals Potential Rate Cuts',
        content: 'The Federal Reserve indicated it may consider interest rate reductions in the coming months amid economic uncertainty.',
        category: 'Economic',
        time: '6 hours ago',
        source: 'CNBC',
        sentiment: 'neutral'
      }
    ],
    polymarket: [
      {
        id: '4',
        title: '🗳️ Election Predictions: Market Impact',
        content: 'Polymarket traders are placing bets on election outcomes, with significant implications for market volatility.',
        category: 'Politics',
        time: '1 hour ago',
        source: 'Polymarket',
        sentiment: 'neutral'
      },
      {
        id: '5',
        title: '⚽ Sports Betting: Championship Finals',
        content: 'High-stakes betting on championship finals is driving significant trading volume in prediction markets.',
        category: 'Sports',
        time: '3 hours ago',
        source: 'SportsBook',
        sentiment: 'positive'
      },
      {
        id: '6',
        title: '🌍 Climate Policy: Carbon Trading',
        content: 'New climate policies are creating opportunities in carbon trading and environmental prediction markets.',
        category: 'Environment',
        time: '5 hours ago',
        source: 'ClimateWire',
        sentiment: 'positive'
      }
    ]
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return '#10b981';
      case 'negative': return '#ef4444';
      case 'neutral': return '#6b7280';
      default: return '#6b7280';
    }
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return '📈';
      case 'negative': return '📉';
      case 'neutral': return '➡️';
      default: return '➡️';
    }
  };

  const filteredNews = selectedMarket === 'all' 
    ? [...newsData.stock, ...newsData.polymarket]
    : newsData[selectedMarket];

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

      {/* 新闻模块网格 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
        gap: '1.5rem',
        // 强制覆盖
        position: 'relative',
        zIndex: 1001,
        overflow: 'visible'
      }}>
        {filteredNews.map((news) => (
          <div key={news.id} style={{
            background: '#1f2937',
            border: '1px solid #374151',
            borderRadius: '0.5rem',
            padding: '1.5rem',
            // 强制覆盖
            position: 'relative',
            zIndex: 1001,
            overflow: 'visible',
            transition: 'all 0.2s ease',
            cursor: 'pointer'
          }}>
            {/* 新闻头部 */}
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
                  background: getSentimentColor(news.sentiment),
                  color: '#ffffff',
                  padding: '0.25rem 0.5rem',
                  borderRadius: '0.25rem',
                  fontSize: '0.75rem',
                  fontWeight: 'bold'
                }}>
                  {getSentimentIcon(news.sentiment)} {news.category}
                </span>
              </div>
              <span style={{
                color: '#9ca3af',
                fontSize: '0.75rem',
                fontWeight: '500'
              }}>
                {news.time}
              </span>
            </div>

            {/* 新闻标题 */}
            <h3 style={{
              color: '#ffffff',
              fontSize: '1.125rem',
              marginBottom: '0.75rem',
              fontWeight: 'bold',
              lineHeight: '1.3'
            }}>
              {news.title}
            </h3>

            {/* 新闻内容 */}
            <p style={{
              color: '#9ca3af',
              marginBottom: '1rem',
              lineHeight: '1.6',
              fontSize: '0.875rem'
            }}>
              {news.content}
            </p>

            {/* 新闻底部 */}
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
                  color: getSentimentColor(news.sentiment),
                  fontSize: '0.75rem',
                  fontWeight: '600'
                }}>
                  {news.sentiment.charAt(0).toUpperCase() + news.sentiment.slice(1)}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 空状态 */}
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
