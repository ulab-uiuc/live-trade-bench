import React, { useState, useEffect, useCallback, useMemo } from 'react';
import ModelsDisplay from './ModelsDisplay';
import SystemMonitoring from './SystemMonitoring';
import './Dashboard.css';

interface Model {
  id: string;
  name: string;
  category: 'polymarket' | 'stock';
  performance: number;
  accuracy: number;
  trades: number;
  profit: number;
  status: 'active' | 'inactive' | 'training';
}

interface StockDashboardProps {
  modelsData: Model[];
  setModelsData: (data: Model[]) => void;
  modelsLastRefresh: Date;
  setModelsLastRefresh: (date: Date) => void;
}

const StockDashboard: React.FC<StockDashboardProps> = ({
  modelsData,
  setModelsData,
  modelsLastRefresh,
  setModelsLastRefresh
}) => {
  const [error, setError] = useState<string | null>(null);

  // 获取股票模型数据
  const fetchStockModelsData = useCallback(async () => {
    try {
      setError(null);

      // Fetch real data from backend API
      const response = await fetch('/api/models/');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const allModels = await response.json();

      // Filter for stock models only
      const stockModels = allModels.filter((model: any) => model.category === 'stock');

      setModelsData(stockModels);
      setModelsLastRefresh(new Date());
    } catch (error) {
      console.error('Error fetching stock models data:', error);
      setError('Failed to load stock models data');
    }
  }, [setModelsData, setModelsLastRefresh]);

  // 获取股票模型
  const stockModels = useMemo(() =>
    modelsData.filter(model => model.category === 'stock'),
    [modelsData]
  );

  useEffect(() => {
    if (modelsData.length === 0 || modelsData.every(model => model.category !== 'stock')) {
      fetchStockModelsData();
    }
  }, [fetchStockModelsData, modelsData]);

  if (error) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#ef4444' }}>
        <span>⚠️ {error}</span>
        <button
          onClick={fetchStockModelsData}
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
          📈 Stock Model
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
        onRefresh={fetchStockModelsData}
      />

      {/* 系统监控 */}
      <SystemMonitoring />
    </div>
  );
};

export default StockDashboard;
