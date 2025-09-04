import React, { useMemo } from 'react';
import ModelsDisplay from './ModelsDisplay';
import SystemMonitoring from './SystemMonitoring';
import './Dashboard.css';
import { Model } from '../types';

interface StockDashboardProps {
  modelsData: Model[];
  modelsLastRefresh: Date;
}

const StockDashboard: React.FC<StockDashboardProps> = ({ modelsData, modelsLastRefresh }) => {
  const stockModels = useMemo(() => 
    modelsData.filter(m => m.category === 'stock'),
    [modelsData]
  );

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
          📈 Stock Models
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
          AI-powered stock portfolio management
        </p>
      </div>

      {/* 只显示股票模型卡片 - 没有统计条 */}
      <ModelsDisplay
        modelsData={stockModels}
        stockModels={stockModels}
        polymarketModels={[]}
        onRefresh={undefined}
      />

      {/* 系统监控 */}
      <SystemMonitoring />
    </div>
  );
};

export default StockDashboard;
