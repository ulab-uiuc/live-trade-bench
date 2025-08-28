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
  const fetchStockModelsData = useCallback(() => {
    try {
      setError(null);

      // 股票模型静态数据
      const stockMockData = [
        {
          id: '1',
          name: 'Claude 3.7 Sonnet',
          category: 'stock' as const,
          status: 'active' as const,
          profit: 1500.00,
          performance: 15.0,
          accuracy: 75.5,
          trades: 25
        },
        {
          id: '2',
          name: 'GPT-5',
          category: 'stock' as const,
          status: 'active' as const,
          profit: -500.00,
          performance: -5.0,
          accuracy: 68.2,
          trades: 18
        },
        {
          id: '4',
          name: 'GPT-4o',
          category: 'stock' as const,
          status: 'active' as const,
          profit: 800.00,
          performance: 8.0,
          accuracy: 72.1,
          trades: 20
        }
      ];

      setModelsData(stockMockData);
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
