import React, { useState, useEffect, useCallback, useMemo } from 'react';
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

interface DashboardProps {
  modelsData: Model[];
  setModelsData: (data: Model[]) => void;
  modelsLastRefresh: Date;
  setModelsLastRefresh: (date: Date) => void;
}

const Dashboard: React.FC<DashboardProps> = ({
  modelsData,
  setModelsData,
  modelsLastRefresh,
  setModelsLastRefresh
}) => {
  const [error, setError] = useState<string | null>(null);

  // 获取所有模型数据的总览
  const fetchModelsData = useCallback(() => {
    try {
      setError(null);
      
      // 所有模型的总览数据
      const allModelsData = [
        // 股票模型
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
        },
        // Polymarket模型
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
      
      setModelsData(allModelsData);
      setModelsLastRefresh(new Date());
    } catch (error) {
      console.error('Error fetching models data:', error);
      setError('Failed to load models data');
    }
  }, [setModelsData, setModelsLastRefresh]);

  // 简化的模型分类
  const { stockModels, polymarketModels } = useMemo(() => ({
    stockModels: modelsData.filter(model => model.category === 'stock'),
    polymarketModels: modelsData.filter(model => model.category === 'polymarket')
  }), [modelsData]);

  useEffect(() => {
    if (modelsData.length === 0) {
      fetchModelsData();
    }
  }, [fetchModelsData, modelsData.length]);

  if (error) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#ef4444' }}>
        <span>⚠️ {error}</span>
        <button 
          onClick={fetchModelsData} 
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
      {/* Overview页面 - 只显示排名条形图，没有P&L统计条 */}
      <div className="overview-charts">
        <div className="chart-section">
          <h3>📈 Stock Models Performance</h3>
          <div className="bar-chart">
            {stockModels
              .sort((a, b) => b.performance - a.performance)
              .map((model, index) => (
                <div key={model.id} className="bar-item">
                  <div className="bar-info">
                    <span className="rank">#{index + 1}</span>
                    <span className="model-name">{model.name}</span>
                    <span className={`performance ${model.performance >= 0 ? 'positive' : 'negative'}`}>
                      {model.performance.toFixed(1)}%
                    </span>
                  </div>
                  <div className="bar-container">
                    <div 
                      className={`bar ${model.performance >= 0 ? 'positive-bar' : 'negative-bar'}`}
                      style={{ 
                        width: `${Math.abs(model.performance) * 5}px`,
                        maxWidth: '200px'
                      }}
                    />
                  </div>
                </div>
              ))}
          </div>
        </div>

        <div className="chart-section">
          <h3>📊 Polymarket Models Performance</h3>
          <div className="bar-chart">
            {polymarketModels
              .sort((a, b) => b.performance - a.performance)
              .map((model, index) => (
                <div key={model.id} className="bar-item">
                  <div className="bar-info">
                    <span className="rank">#{index + 1}</span>
                    <span className="model-name">{model.name}</span>
                    <span className={`performance ${model.performance >= 0 ? 'positive' : 'negative'}`}>
                      {model.performance.toFixed(1)}%
                    </span>
                  </div>
                  <div className="bar-container">
                    <div 
                      className={`bar ${model.performance >= 0 ? 'positive-bar' : 'negative-bar'}`}
                      style={{ 
                        width: `${Math.abs(model.performance) * 5}px`,
                        maxWidth: '200px'
                      }}
                    />
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;