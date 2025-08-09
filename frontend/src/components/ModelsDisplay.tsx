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
  modelsData: Model[];
  setModelsData: (models: Model[]) => void;
  lastRefresh: Date;
  setLastRefresh: (date: Date) => void;
}

const ModelsDisplay: React.FC<ModelsDisplayProps> = ({
  modelsData,
  setModelsData,
  lastRefresh,
  setLastRefresh
}) => {
  const [loading, setLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'polymarket' | 'stock' | 'option'>('all');

  const fetchModels = async () => {
    setLoading(true);
    try {
      // Fetch real LLM models data
      const response = await fetch('http://localhost:8000/api/models/');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();

      // Transform backend data to frontend format
      const transformedModels: Model[] = data.map((model: any) => ({
        id: model.id,
        name: model.name,
        category: model.category || 'stock', // Default to stock, but can expand to options, etc.
        performance: model.performance,
        accuracy: model.accuracy,
        trades: model.trades,
        profit: model.profit,
        status: model.status,
        market_type: model.market_type,
        ticker: model.ticker,
        strategy: model.strategy
      }));

      setModelsData(transformedModels);
      setLastRefresh(new Date());
    } catch (error) {
      console.error('Error fetching models:', error);
      // Keep existing models data on error, don't clear it
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Only fetch if we don't have data or if it's been more than a day
    const shouldFetch = modelsData.length === 0 ||
      (Date.now() - lastRefresh.getTime()) > 24 * 60 * 60 * 1000;

    if (shouldFetch) {
      fetchModels();
    }

    // Auto-refresh every day
    const interval = setInterval(fetchModels, 24 * 60 * 60 * 1000);

    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
    ? modelsData
    : modelsData.filter(model => model.category === selectedCategory);

  const categoryStats = {
    polymarket: modelsData.filter(m => m.category === 'polymarket').length,
    stock: modelsData.filter(m => m.category === 'stock').length,
    option: modelsData.filter(m => m.category === 'option').length,
    total: modelsData.length
  };

  return (
    <div>
      <div className="models-header">
        <h2 className="models-title">Trading Models</h2>
        <div className="refresh-indicator">
          {loading && <div className="spinner"></div>}
          <span>
            Last updated: {lastRefresh.toLocaleTimeString()}
          </span>
        </div>
      </div>

      {/* Category Filter */}
      <div className="news-filters" style={{ marginBottom: '1.5rem' }}>
        <button
          onClick={() => setSelectedCategory('all')}
          className={`filter-button ${selectedCategory === 'all' ? 'active' : ''}`}
        >
          All ({categoryStats.total})
        </button>
        <button
          onClick={() => setSelectedCategory('polymarket')}
          className={`filter-button ${selectedCategory === 'polymarket' ? 'active' : ''}`}
        >
          📊 Polymarket ({categoryStats.polymarket})
        </button>
        <button
          onClick={() => setSelectedCategory('stock')}
          className={`filter-button ${selectedCategory === 'stock' ? 'active' : ''}`}
        >
          📈 Stock ({categoryStats.stock})
        </button>
        <button
          onClick={() => setSelectedCategory('option')}
          className={`filter-button ${selectedCategory === 'option' ? 'active' : ''}`}
        >
          ⚡ Option ({categoryStats.option})
        </button>
      </div>

      <div className="models-grid">
        {filteredModels.map(model => (
          <div key={model.id} className="model-card">
            <div className="model-header">
              <h3 className="model-name">{model.name}</h3>
              <span className={`model-category ${model.category}`}>
                {getCategoryIcon(model.category)} {model.category}
              </span>
            </div>

            <div className="model-status">
              <span className={`status-indicator ${model.status}`}></span>
              <span className="status-text">{model.status}</span>
            </div>

            {/* Category-specific information */}
            <div style={{ marginBottom: '1rem' }}>
              {model.category === 'polymarket' && model.market_type && (
                <div className="metric-item">
                  <span className="metric-label">Market Type</span>
                  <span className="metric-value">{model.market_type}</span>
                </div>
              )}
              {model.category === 'stock' && model.ticker && (
                <div className="metric-item">
                  <span className="metric-label">Ticker</span>
                  <span className="metric-value">{model.ticker}</span>
                </div>
              )}
              {model.category === 'option' && model.ticker && (
                <div className="metric-item">
                  <span className="metric-label">Option</span>
                  <span className="metric-value">{model.ticker} {model.strategy && `- ${model.strategy}`}</span>
                </div>
              )}
            </div>

            <div className="model-metrics">
              <div className="metric-item">
                <span className="metric-label">Performance</span>
                <span className={`metric-value ${model.performance >= 0 ? 'positive' : 'negative'}`}>
                  {model.performance >= 0 ? '+' : ''}{model.performance.toFixed(1)}%
                </span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Accuracy</span>
                <span className="metric-value">{model.accuracy.toFixed(1)}%</span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Total Trades</span>
                <span className="metric-value">{model.trades}</span>
              </div>
              <div className="metric-item">
                <span className="metric-label">Profit/Loss</span>
                <span className={`metric-value ${model.profit >= 0 ? 'positive' : 'negative'}`}>
                  {model.profit >= 0 ? '+' : ''}${model.profit.toFixed(2)}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredModels.length === 0 && !loading && (
        <div className="empty-state">
          <div className="empty-state-icon">📊</div>
          <p className="empty-state-text">No models found for the selected category.</p>
        </div>
      )}
    </div>
  );
};

export default ModelsDisplay;
