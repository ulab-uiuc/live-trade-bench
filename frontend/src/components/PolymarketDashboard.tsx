import React from 'react';
import ModelsDisplay from './ModelsDisplay';
import SystemMonitoring from './SystemMonitoring';
import './Dashboard.css';
import { useModelsByCategory } from '../hooks/useModels';

const PolymarketDashboard: React.FC<any> = () => {
  const { models, error, refresh } = useModelsByCategory('polymarket');

  if (error) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#ef4444' }}>
        <span>⚠️ {error}</span>
        <button
          onClick={refresh}
          style={{
            marginLeft: '1rem',
            padding: '0.5rem 1rem',
            background: '#ef4444',
            color: 'white',
            border: 'none',
            borderRadius: '0.25rem',
            cursor: 'pointer'
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="dashboard-ultra-simple">
      {/* 页面标题 */}
      <div style={{
        textAlign: 'center',
        marginBottom: '2rem',
        padding: '2rem 0',
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%)',
        borderRadius: '0.5rem',
        border: '1px solid #374151'
      }}>
        <h1 style={{
          color: '#ffffff',
          fontSize: '2.5rem',
          margin: '0 0 0.5rem 0',
          fontWeight: '700',
          display: 'block',
          visibility: 'visible',
          opacity: 1,
          position: 'relative',
          zIndex: 1000
        }}>
          🎯 Polymarket Model
        </h1>
        <p style={{
          color: '#ffffff',
          fontSize: '1rem',
          margin: 0,
          fontWeight: '500',
          display: 'block',
          visibility: 'visible',
          opacity: 1,
          position: 'relative',
          zIndex: 1000
        }}>
          AI-powered prediction market portfolio management
        </p>
      </div>

      {/* 只显示Polymarket模型 */}
      <ModelsDisplay
        modelsData={models}
        stockModels={[]}
        polymarketModels={models}
        onRefresh={refresh}
      />

      {/* 系统监控 */}
      <SystemMonitoring />
    </div>
  );
};

export default PolymarketDashboard;
