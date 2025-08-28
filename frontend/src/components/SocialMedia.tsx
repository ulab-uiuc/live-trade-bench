import React, { useState } from 'react';

const SocialMedia: React.FC = () => {
  console.log('📱 Social Media component is rendering!');
  
  const [selectedMarket, setSelectedMarket] = useState<'all' | 'stock' | 'polymarket'>('all');

  // 模拟社交媒体数据 - 按市场分类
  const socialData = {
    stock: [
      {
        id: '1',
        platform: 'Twitter',
        username: '@marketanalyst',
        displayName: 'Market Analyst Pro',
        content: '🚀 Tech stocks are showing incredible momentum! $AAPL, $MSFT, and $GOOGL all breaking resistance levels. This could be the start of a major rally. #TechStocks #StockMarket #Investing',
        time: '2 hours ago',
        likes: 245,
        retweets: 89,
        replies: 23,
        sentiment: 'positive',
        avatar: '🐦'
      },
      {
        id: '2',
        platform: 'LinkedIn',
        username: '@financeinsights',
        displayName: 'Finance Insights',
        content: '📊 Q4 earnings season is heating up! Companies are reporting strong results across multiple sectors. The market sentiment is turning bullish. What\'s your take on the current market conditions? #Earnings #Q4 #MarketAnalysis',
        time: '4 hours ago',
        likes: 189,
        retweets: 67,
        replies: 45,
        sentiment: 'positive',
        avatar: '💼'
      },
      {
        id: '3',
        platform: 'Reddit',
        username: 'u/stocktrader123',
        displayName: 'Stock Trader 123',
        content: 'Just bought more $TSLA after their earnings call! The EV market is exploding and Tesla is leading the charge. Anyone else bullish on electric vehicles? 🚗⚡ #Tesla #EV #Investing',
        time: '6 hours ago',
        likes: 156,
        retweets: 34,
        replies: 67,
        sentiment: 'positive',
        avatar: '📈'
      }
    ],
    polymarket: [
      {
        id: '4',
        platform: 'Discord',
        username: '@polytrader',
        displayName: 'Poly Trader',
        content: '🗳️ Election predictions are heating up! The market is showing interesting patterns. I\'m betting on some surprising outcomes. What do you think about the current odds? #Polymarket #Elections #Predictions',
        time: '1 hour ago',
        likes: 98,
        retweets: 23,
        replies: 12,
        sentiment: 'neutral',
        avatar: '🎯'
      },
      {
        id: '5',
        platform: 'Telegram',
        username: '@sportsbettor',
        displayName: 'Sports Bettor Pro',
        content: '⚽ Championship finals are here! The prediction markets are going crazy. I\'ve placed some high-stakes bets on underdogs. High risk, high reward! #Sports #Betting #Championship',
        time: '3 hours ago',
        likes: 134,
        retweets: 45,
        replies: 28,
        sentiment: 'positive',
        avatar: '⚽'
      },
      {
        id: '6',
        platform: 'Twitter',
        username: '@climateinvestor',
        displayName: 'Climate Investor',
        content: '🌍 New climate policies are creating amazing opportunities in carbon trading! The prediction markets are showing strong support for green initiatives. Time to go green! #Climate #CarbonTrading #GreenInvesting',
        time: '5 hours ago',
        likes: 89,
        retweets: 32,
        replies: 15,
        sentiment: 'positive',
        avatar: '🌍'
      }
    ]
  };

  const getPlatformColor = (platform: string) => {
    switch (platform.toLowerCase()) {
      case 'twitter': return '#1da1f2';
      case 'linkedin': return '#0077b5';
      case 'reddit': return '#ff4500';
      case 'discord': return '#7289da';
      case 'telegram': return '#0088cc';
      default: return '#6366f1';
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return '#10b981';
      case 'negative': return '#ef4444';
      case 'neutral': return '#6b7280';
      default: return '#6b7280';
    }
  };

  const filteredSocial = selectedMarket === 'all' 
    ? [...socialData.stock, ...socialData.polymarket]
    : socialData[selectedMarket];

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
        📱 Social Media Feed
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
          🌍 All Markets ({socialData.stock.length + socialData.polymarket.length})
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
          📈 Stock Market ({socialData.stock.length})
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
          🎯 Polymarket ({socialData.polymarket.length})
        </button>
      </div>

      {/* 社交媒体帖子网格 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
        gap: '1.5rem',
        // 强制覆盖
        position: 'relative',
        zIndex: 1001,
        overflow: 'visible'
      }}>
        {filteredSocial.map((post) => (
          <div key={post.id} style={{
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
            {/* 帖子头部 */}
            <div style={{
              display: 'flex',
              alignItems: 'flex-start',
              marginBottom: '1rem',
              gap: '0.75rem'
            }}>
              <div style={{
                width: '48px',
                height: '48px',
                background: getPlatformColor(post.platform),
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.5rem',
                flexShrink: 0
              }}>
                {post.avatar}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'flex-start',
                  marginBottom: '0.25rem'
                }}>
                  <h3 style={{
                    color: '#ffffff',
                    margin: '0 0 0.25rem 0',
                    fontWeight: 'bold',
                    fontSize: '1rem'
                  }}>
                    {post.displayName}
                  </h3>
                  <span style={{
                    background: getPlatformColor(post.platform),
                    color: '#ffffff',
                    padding: '0.125rem 0.375rem',
                    borderRadius: '0.25rem',
                    fontSize: '0.625rem',
                    fontWeight: '600',
                    textTransform: 'uppercase'
                  }}>
                    {post.platform}
                  </span>
                </div>
                <p style={{
                  color: '#9ca3af',
                  margin: 0,
                  fontSize: '0.75rem'
                }}>
                  {post.username} • {post.time}
                </p>
              </div>
            </div>

            {/* 帖子内容 */}
            <p style={{
              color: '#ffffff',
              marginBottom: '1rem',
              lineHeight: '1.6',
              fontSize: '0.875rem'
            }}>
              {post.content}
            </p>

            {/* 互动统计 */}
            <div style={{
              display: 'flex',
              gap: '1rem',
              color: '#9ca3af',
              fontSize: '0.75rem',
              marginBottom: '1rem'
            }}>
              <span>❤️ {post.likes}</span>
              <span>🔄 {post.retweets}</span>
              <span>💬 {post.replies}</span>
            </div>

            {/* 帖子底部 */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              paddingTop: '0.75rem',
              borderTop: '1px solid #374151'
            }}>
              <span style={{
                color: getPlatformColor(post.platform),
                fontSize: '0.75rem',
                fontWeight: '600'
              }}>
                📱 {post.platform}
              </span>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <span style={{
                  color: getSentimentColor(post.sentiment),
                  fontSize: '0.75rem',
                  fontWeight: '600'
                }}>
                  {post.sentiment.charAt(0).toUpperCase() + post.sentiment.slice(1)}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 空状态 */}
      {filteredSocial.length === 0 && (
        <div style={{
          textAlign: 'center',
          padding: '3rem 1rem',
          color: '#94a3b8'
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📱</div>
          <p style={{ margin: 0, fontSize: '1.125rem', fontWeight: '500' }}>
            No social media posts available for the selected market
          </p>
        </div>
      )}
    </div>
  );
};

export default SocialMedia;
