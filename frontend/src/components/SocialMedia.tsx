import React from 'react';

const SocialMedia: React.FC = () => {
  console.log('📱 Social Media component is rendering!');

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

      {/* 平台过滤器 */}
      <div style={{
        marginBottom: '2rem',
        display: 'flex',
        gap: '1rem',
        flexWrap: 'wrap',
        // 强制覆盖
        position: 'relative',
        zIndex: 1001,
        overflow: 'visible'
      }}>
        <button style={{
          background: '#6366f1',
          color: '#ffffff',
          border: 'none',
          padding: '0.75rem 1.5rem',
          borderRadius: '0.5rem',
          fontWeight: 'bold',
          cursor: 'pointer'
        }}>
          🐦 Twitter
        </button>
        <button style={{
          background: '#1f2937',
          color: '#9ca3af',
          border: '1px solid #374151',
          padding: '0.75rem 1.5rem',
          borderRadius: '0.5rem',
          fontWeight: 'bold',
          cursor: 'pointer'
        }}>
          💼 LinkedIn
        </button>
        <button style={{
          background: '#1f2937',
          color: '#9ca3af',
          border: '1px solid #374151',
          padding: '0.75rem 1.5rem',
          borderRadius: '0.5rem',
          fontWeight: 'bold',
          cursor: 'pointer'
        }}>
          📘 Facebook
        </button>
        <button style={{
          background: '#1f2937',
          color: '#9ca3af',
          border: '1px solid #374151',
          padding: '0.75rem 1.5rem',
          borderRadius: '0.5rem',
          fontWeight: 'bold',
          cursor: 'pointer'
        }}>
          📷 Instagram
        </button>
      </div>

      {/* 社交媒体帖子 */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '1.5rem',
        // 强制覆盖
        position: 'relative',
        zIndex: 1001,
        overflow: 'visible'
      }}>
        {/* 帖子1 */}
        <div style={{
          background: '#1f2937',
          border: '1px solid #374151',
          borderRadius: '0.5rem',
          padding: '1.5rem',
          // 强制覆盖
          position: 'relative',
          zIndex: 1001,
          overflow: 'visible'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem' }}>
            <div style={{
              width: '48px',
              height: '48px',
              background: '#6366f1',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginRight: '1rem',
              fontSize: '1.5rem'
            }}>
              🐦
            </div>
            <div>
              <h3 style={{ color: '#ffffff', margin: '0 0 0.25rem 0', fontWeight: 'bold' }}>Market Analyst Pro</h3>
              <p style={{ color: '#9ca3af', margin: 0, fontSize: '0.875rem' }}>@marketanalyst • 2 hours ago</p>
            </div>
          </div>
          <p style={{ color: '#ffffff', marginBottom: '1rem', lineHeight: '1.6' }}>
            🚀 Tech stocks are showing incredible momentum! $AAPL, $MSFT, and $GOOGL all breaking resistance levels.
            This could be the start of a major rally. #TechStocks #StockMarket #Investing
          </p>
          <div style={{ display: 'flex', gap: '1rem', color: '#9ca3af', fontSize: '0.875rem' }}>
            <span>❤️ 245</span>
            <span>🔄 89</span>
            <span>💬 23</span>
          </div>
        </div>

        {/* 帖子2 */}
        <div style={{
          background: '#1f2937',
          border: '1px solid #374151',
          borderRadius: '0.5rem',
          padding: '1.5rem',
          // 强制覆盖
          position: 'relative',
          zIndex: 1001,
          overflow: 'visible'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem' }}>
            <div style={{
              width: '48px',
              height: '48px',
              background: '#10b981',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginRight: '1rem',
              fontSize: '1.5rem'
            }}>
              💼
            </div>
            <div>
              <h3 style={{ color: '#ffffff', margin: '0 0 0.25rem 0', fontWeight: 'bold' }}>Finance Insights</h3>
              <p style={{ color: '#9ca3af', margin: 0, fontSize: '0.875rem' }}>@financeinsights • 4 hours ago</p>
            </div>
          </div>
          <p style={{ color: '#ffffff', marginBottom: '1rem', lineHeight: '1.6' }}>
            📊 Q4 earnings season is heating up! Companies are reporting strong results across multiple sectors.
            The market sentiment is turning bullish. What's your take on the current market conditions?
            #Earnings #Q4 #MarketAnalysis
          </p>
          <div style={{ display: 'flex', gap: '1rem', color: '#9ca3af', fontSize: '0.875rem' }}>
            <span>❤️ 189</span>
            <span>🔄 67</span>
            <span>💬 45</span>
          </div>
        </div>

        {/* 帖子3 */}
        <div style={{
          background: '#1f2937',
          border: '1px solid #374151',
          borderRadius: '0.5rem',
          padding: '1.5rem',
          // 强制覆盖
          position: 'relative',
          zIndex: 1001,
          overflow: 'visible'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem' }}>
            <div style={{
              width: '48px',
              height: '48px',
              background: '#f59e0b',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginRight: '1rem',
              fontSize: '1.5rem'
            }}>
              🌍
            </div>
            <div>
              <h3 style={{ color: '#ffffff', margin: '0 0 0.25rem 0', fontWeight: 'bold' }}>Global Markets</h3>
              <p style={{ color: '#9ca3af', margin: 0, fontSize: '0.875rem' }}>@globalmarkets • 6 hours ago</p>
            </div>
          </div>
          <p style={{ color: '#ffffff', marginBottom: '1rem', lineHeight: '1.6' }}>
            🌍 European markets are showing signs of recovery! The ECB's latest policy decisions are creating
            positive momentum. This could be a great opportunity for international diversification.
            #EuropeanMarkets #ECB #GlobalInvesting
          </p>
          <div style={{ display: 'flex', gap: '1rem', color: '#9ca3af', fontSize: '0.875rem' }}>
            <span>❤️ 156</span>
            <span>🔄 34</span>
            <span>💬 12</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SocialMedia;
