import React, { useState, useEffect } from 'react';

interface Model {
  id: string;
  name: string;
  category: 'polymarket' | 'stock' | 'option';
  performance: number;
  accuracy: number;
  trades: number;
  profit: number;
  status: 'active' | 'inactive' | 'training';
  // Category-specific fields
  market_type?: string; // For polymarket models
  ticker?: string; // For stock/option models
  strategy?: string; // For option models
}

interface ModelsDisplayProps {
  lastRefresh: Date;
}

const ModelsDisplay: React.FC<ModelsDisplayProps> = ({ lastRefresh }) => {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'polymarket' | 'stock' | 'option'>('all');

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
        category: model.category || 'stock', // Default to stock if not specified
        performance: model.performance,
        accuracy: model.accuracy,
        trades: model.trades,
        profit: model.profit,
        status: model.status,
        market_type: model.market_type,
        ticker: model.ticker,
        strategy: model.strategy
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

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'polymarket': return '#8e44ad';
      case 'stock': return '#3498db';
      case 'option': return '#e67e22';
      default: return '#95a5a6';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'polymarket': return '📊';
      case 'stock': return '📈';
      case 'option': return '⚡';
      default: return '📋';
    }
  };

  const filteredModels = selectedCategory === 'all'
    ? models
    : models.filter(model => model.category === selectedCategory);

  const categoryStats = {
    polymarket: models.filter(m => m.category === 'polymarket').length,
    stock: models.filter(m => m.category === 'stock').length,
    option: models.filter(m => m.category === 'option').length,
    total: models.length
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

      {/* Category Filter */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button
            onClick={() => setSelectedCategory('all')}
            style={{
              padding: '8px 16px',
              border: '1px solid #ddd',
              borderRadius: '20px',
              background: selectedCategory === 'all' ? '#007bff' : 'white',
              color: selectedCategory === 'all' ? 'white' : '#333',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            All ({categoryStats.total})
          </button>
          <button
            onClick={() => setSelectedCategory('polymarket')}
            style={{
              padding: '8px 16px',
              border: '1px solid #8e44ad',
              borderRadius: '20px',
              background: selectedCategory === 'polymarket' ? '#8e44ad' : 'white',
              color: selectedCategory === 'polymarket' ? 'white' : '#8e44ad',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            📊 Polymarket ({categoryStats.polymarket})
          </button>
          <button
            onClick={() => setSelectedCategory('stock')}
            style={{
              padding: '8px 16px',
              border: '1px solid #3498db',
              borderRadius: '20px',
              background: selectedCategory === 'stock' ? '#3498db' : 'white',
              color: selectedCategory === 'stock' ? 'white' : '#3498db',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            📈 Stock ({categoryStats.stock})
          </button>
          <button
            onClick={() => setSelectedCategory('option')}
            style={{
              padding: '8px 16px',
              border: '1px solid #e67e22',
              borderRadius: '20px',
              background: selectedCategory === 'option' ? '#e67e22' : 'white',
              color: selectedCategory === 'option' ? 'white' : '#e67e22',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            ⚡ Option ({categoryStats.option})
          </button>
        </div>
      </div>

      {filteredModels.map(model => (
        <div key={model.id} className="model-card" style={{
          borderLeft: `4px solid ${getCategoryColor(model.category)}`,
          marginBottom: '15px',
          padding: '15px',
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          background: 'white'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '20px' }}>{getCategoryIcon(model.category)}</span>
              <h3 style={{ margin: 0, color: getCategoryColor(model.category) }}>{model.name}</h3>
            </div>
            <span
              style={{
                color: getStatusColor(model.status),
                fontWeight: 'bold',
                textTransform: 'uppercase',
                fontSize: '0.875rem',
                padding: '4px 8px',
                borderRadius: '12px',
                background: `${getStatusColor(model.status)}20`
              }}
            >
              {model.status}
            </span>
          </div>

          {/* Category-specific information */}
          <div style={{ marginBottom: '10px', fontSize: '0.9rem', color: '#666' }}>
            {model.category === 'polymarket' && model.market_type && (
              <span style={{
                background: '#8e44ad20',
                padding: '2px 8px',
                borderRadius: '12px',
                marginRight: '8px'
              }}>
                Market: {model.market_type}
              </span>
            )}
            {model.category === 'stock' && model.ticker && (
              <span style={{
                background: '#3498db20',
                padding: '2px 8px',
                borderRadius: '12px',
                marginRight: '8px'
              }}>
                Ticker: {model.ticker}
              </span>
            )}
            {model.category === 'option' && model.ticker && (
              <span style={{
                background: '#e67e2220',
                padding: '2px 8px',
                borderRadius: '12px',
                marginRight: '8px'
              }}>
                {model.ticker} {model.strategy && `- ${model.strategy}`}
              </span>
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
            <div>
              <p style={{ margin: '5px 0', fontSize: '0.9rem' }}>
                <strong>Performance:</strong>
                <span style={{ color: model.performance >= 0 ? '#28a745' : '#dc3545' }}>
                  {model.performance >= 0 ? '+' : ''}{model.performance.toFixed(1)}%
                </span>
              </p>
              <p style={{ margin: '5px 0', fontSize: '0.9rem' }}>
                <strong>Accuracy:</strong> {model.accuracy.toFixed(1)}%
              </p>
            </div>
            <div>
              <p style={{ margin: '5px 0', fontSize: '0.9rem' }}>
                <strong>Total Trades:</strong> {model.trades}
              </p>
              <p style={{ margin: '5px 0', fontSize: '0.9rem' }}>
                <strong>Profit/Loss:</strong>
                <span className={model.profit >= 0 ? 'trade-amount profit' : 'trade-amount loss'}>
                  {model.profit >= 0 ? '+' : ''}${model.profit.toFixed(2)}
                </span>
              </p>
            </div>
          </div>
        </div>
      ))}

      {filteredModels.length === 0 && !loading && (
        <div style={{
          textAlign: 'center',
          padding: '40px',
          color: '#666',
          background: '#f8f9fa',
          borderRadius: '8px'
        }}>
          <p>No models found for the selected category.</p>
        </div>
      )}
    </div>
  );
};

export default ModelsDisplay;
