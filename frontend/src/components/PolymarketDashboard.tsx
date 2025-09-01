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

interface PolymarketDashboardProps {
  modelsData: Model[];
  setModelsData: (data: Model[]) => void;
  modelsLastRefresh: Date;
  setModelsLastRefresh: (date: Date) => void;
}

const PolymarketDashboard: React.FC<PolymarketDashboardProps> = ({
  modelsData,
  setModelsData,
  modelsLastRefresh,
  setModelsLastRefresh
}) => {
  const [error, setError] = useState<string | null>(null);

  // 只获取Polymarket模型数据
  const fetchPolymarketModelsData = useCallback(async () => {
    try {
      setError(null);

      // Fetch real data from backend API
      const response = await fetch('/api/models/');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const allModels = await response.json();

      // Filter for polymarket models only
      const polymarketModels = allModels.filter((model: any) => model.category === 'polymarket');

      setModelsData(polymarketModels);
      setModelsLastRefresh(new Date());
    } catch (error) {
      console.error('Error fetching polymarket models data:', error);
      setError('Failed to load polymarket models data');
    }
  }, [setModelsData, setModelsLastRefresh]);

  // 只计算Polymarket模型的统计数据
  const polymarketStats = useMemo(() => {
    const polymarketModels = modelsData.filter(model => model.category === 'polymarket');
    const totalProfit = polymarketModels.reduce((sum, model) => sum + model.profit, 0);
    const activeModels = polymarketModels.filter(model => model.status === 'active').length;

    return { totalProfit, activeModels, totalModels: polymarketModels.length };
  }, [modelsData]);

  // 只获取Polymarket模型
  const polymarketModels = useMemo(() =>
    modelsData.filter(model => model.category === 'polymarket'),
    [modelsData]
  );

  useEffect(() => {
    if (modelsData.length === 0 || modelsData.every(model => model.category !== 'polymarket')) {
      fetchPolymarketModelsData();
    }
  }, [fetchPolymarketModelsData, modelsData]);

  if (error) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#ef4444' }}>
        <span>⚠️ {error}</span>
        <button
          onClick={fetchPolymarketModelsData}
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
          🎯 Polymarket Prediction Models
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
          AI-powered prediction market strategies and outcome forecasting
        </p>
      </div>

      {/* 只显示Polymarket模型 */}
      <ModelsDisplay
        modelsData={polymarketModels}
        stockModels={[]}
        polymarketModels={polymarketModels}
        onRefresh={fetchPolymarketModelsData}
      />

      {/* 系统监控 */}
      <SystemMonitoring />
    </div>
  );
};

export default PolymarketDashboard;
