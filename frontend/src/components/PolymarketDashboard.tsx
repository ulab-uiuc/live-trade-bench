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
  const fetchPolymarketModelsData = useCallback(() => {
    try {
      setError(null);
      
      // Polymarket模型静态数据
      const polymarketMockData = [
        {
          id: '3',
          name: 'Polymarket Agent',
          category: 'polymarket' as const,
          status: 'active' as const,
          profit: 800.00,
          performance: 8.0,
          accuracy: 82.1,
          trades: 12
        },
        {
          id: '5',
          name: 'Election Predictor',
          category: 'polymarket' as const,
          status: 'active' as const,
          profit: 1200.00,
          performance: 12.0,
          accuracy: 85.3,
          trades: 15
        },
        {
          id: '6',
          name: 'Sports Betting AI',
          category: 'polymarket' as const,
          status: 'active' as const,
          profit: -300.00,
          performance: -3.0,
          accuracy: 65.8,
          trades: 8
        }
      ];
      
      setModelsData(polymarketMockData);
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
