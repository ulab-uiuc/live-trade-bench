import React from 'react';

const News: React.FC = () => {
  console.log('📰 News component is rendering!');

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
        📰 Stocks News
      </h1>


      {/* 模拟新闻数据 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '1.5rem',
        // 强制覆盖
        position: 'relative',
        zIndex: 1001,
        overflow: 'visible'
      }}>
        {/* 新闻项目1 */}
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
          <h3 style={{ color: '#ffffff', fontSize: '1.25rem', marginBottom: '1rem', fontWeight: 'bold' }}>
            🚀 Tech Stocks Rally on AI Breakthrough
          </h3>
          <p style={{ color: '#9ca3af', marginBottom: '1rem', lineHeight: '1.6' }}>
            Major technology companies saw significant gains following the announcement of a new artificial intelligence breakthrough that could revolutionize the industry.
          </p>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ color: '#6366f1', fontSize: '0.875rem', fontWeight: 'bold' }}>Technology</span>
            <span style={{ color: '#9ca3af', fontSize: '0.875rem' }}>2 hours ago</span>
          </div>
        </div>

        {/* 新闻项目2 */}
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
          <h3 style={{ color: '#ffffff', fontSize: '1.25rem', marginBottom: '1rem', fontWeight: 'bold' }}>
            📈 Market Analysis: Q4 Earnings Preview
          </h3>
          <p style={{ color: '#9ca3af', marginBottom: '1rem', lineHeight: '1.6' }}>
            Analysts predict strong Q4 earnings across multiple sectors, with particular focus on consumer goods and financial services companies.
          </p>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ color: '#10b981', fontSize: '0.875rem', fontWeight: 'bold' }}>Analysis</span>
            <span style={{ color: '#9ca3af', fontSize: '0.875rem' }}>4 hours ago</span>
          </div>
        </div>

        {/* 新闻项目3 */}
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
          <h3 style={{ color: '#ffffff', fontSize: '1.25rem', marginBottom: '1rem', fontWeight: 'bold' }}>
            🌍 Global Markets: European Recovery
          </h3>
          <p style={{ color: '#9ca3af', marginBottom: '1rem', lineHeight: '1.6' }}>
            European markets show signs of recovery as economic indicators improve and central banks maintain supportive monetary policies.
          </p>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ color: '#f59e0b', fontSize: '0.875rem', fontWeight: 'bold' }}>Global</span>
            <span style={{ color: '#9ca3af', fontSize: '0.875rem' }}>6 hours ago</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default News;
