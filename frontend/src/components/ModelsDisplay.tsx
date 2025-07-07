import React, { useState, useEffect } from 'react';

interface Model {
  id: string;
  name: string;
  performance: number;
  accuracy: number;
  trades: number;
  profit: number;
  status: 'active' | 'inactive' | 'training';
}

interface ModelsDisplayProps {
  lastRefresh: Date;
}

const ModelsDisplay: React.FC<ModelsDisplayProps> = ({ lastRefresh }) => {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchModels = async () => {
    setLoading(true);
    try {
      // Fetch from backend API
      const response = await fetch('http://localhost:8000/api/models/');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      // Transform backend data to frontend format
      const transformedModels: Model[] = data.map((model: any) => ({
        id: model.id,
        name: model.name,
        performance: model.performance,
        accuracy: model.accuracy,
        trades: model.trades,
        profit: model.profit,
        status: model.status
      }));
      
      setModels(transformedModels);
    } catch (error) {
      console.error('Error fetching models:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, [lastRefresh]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return '#28a745';
      case 'inactive': return '#6c757d';
      case 'training': return '#ffc107';
      default: return '#6c757d';
    }
  };

  return (
    <div>
      <div className="refresh-indicator">
        <h2>Trading Models</h2>
        {loading && <div className="spinner"></div>}
        <span style={{ marginLeft: 'auto', fontSize: '0.875rem', color: '#666' }}>
          Last updated: {lastRefresh.toLocaleTimeString()}
        </span>
      </div>
      
      {models.map(model => (
        <div key={model.id} className="model-card">
          <h3>{model.name}</h3>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <p><strong>Performance:</strong> {model.performance.toFixed(1)}%</p>
              <p><strong>Accuracy:</strong> {model.accuracy.toFixed(1)}%</p>
              <p><strong>Total Trades:</strong> {model.trades}</p>
              <p><strong>Profit/Loss:</strong> 
                <span className={model.profit >= 0 ? 'trade-amount profit' : 'trade-amount loss'}>
                  ${model.profit.toFixed(2)}
                </span>
              </p>
            </div>
            <div>
              <span 
                style={{ 
                  color: getStatusColor(model.status),
                  fontWeight: 'bold',
                  textTransform: 'uppercase',
                  fontSize: '0.875rem'
                }}
              >
                {model.status}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ModelsDisplay;