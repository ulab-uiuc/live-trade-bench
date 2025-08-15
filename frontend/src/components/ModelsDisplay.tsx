import React, { useState, useEffect } from 'react';
import Portfolio from './Portfolio';

interface Model {
  id: string;
  name: string;
  category: 'polymarket' | 'stock';
  performance: number;
  accuracy: number;
  trades: number;
  profit: number;
  status: 'active' | 'inactive' | 'training';
  // Enhanced fields from Phase 2
  total_value?: number;
  cash_balance?: number;
  active_positions?: number;
  is_activated?: boolean;
  recent_performance?: {
    daily_actions: number;
    weekly_actions: number;
    recent_win_rate: number;
    last_action_time?: string;
  };
  llm_available?: boolean;
  // Category-specific fields
  market_type?: string; // For polymarket models
  ticker?: string; // For stock models
  strategy?: string;
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
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'polymarket' | 'stock'>('all');
  const [expandedModel, setExpandedModel] = useState<string | null>(null);

  const fetchModels = async () => {
    setLoading(true);
    try {
      // Fetch real LLM models data
      const response = await fetch('/api/models/');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();

      // Transform backend data to frontend format with enhanced fields
      const transformedModels: Model[] = data.map((model: any) => ({
        id: model.id,
        name: model.name,
        category: model.category || 'stock', // Default to stock, but can expand to options, etc.
        performance: model.performance,
        accuracy: model.accuracy,
        trades: model.trades,
        profit: model.profit,
        status: model.status,
        // Enhanced Phase 2 fields
        total_value: model.total_value,
        cash_balance: model.cash_balance,
        active_positions: model.active_positions,
        is_activated: model.is_activated,
        recent_performance: model.recent_performance,
        llm_available: model.llm_available,
        // Category-specific fields
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

    // Auto-refresh every 30 seconds for real-time data
    const interval = setInterval(fetchModels, 30 * 1000);

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
      default: return '#95a5a6';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'polymarket': return '📊';
      case 'stock': return '📈';
      default: return '📋';
    }
  };

  const filteredModels = selectedCategory === 'all'
    ? modelsData
    : modelsData.filter(model => model.category === selectedCategory);

  const categoryStats = {
    polymarket: modelsData.filter(m => m.category === 'polymarket').length,
    stock: modelsData.filter(m => m.category === 'stock').length,
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
              <div className="status-row">
                <span className={`status-indicator ${model.status}`}></span>
                <span className="status-text">{model.status}</span>
                {model.is_activated !== undefined && (
                  <span className={`activation-badge ${model.is_activated ? 'active' : 'inactive'}`}>
                    {model.is_activated ? '🟢 Active' : '⚪ Inactive'}
                  </span>
                )}
              </div>
              {model.llm_available !== undefined && (
                <div className="llm-status">
                  <span className={`llm-indicator ${model.llm_available ? 'available' : 'unavailable'}`}>
                    {model.llm_available ? '🤖 LLM Available' : '⚠️ LLM Unavailable'}
                  </span>
                </div>
              )}
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

              {/* Enhanced Phase 2 Metrics */}
              {model.total_value !== undefined && (
                <div className="metric-item">
                  <span className="metric-label">Portfolio Value</span>
                  <span className="metric-value">${model.total_value.toFixed(2)}</span>
                </div>
              )}
              {model.cash_balance !== undefined && (
                <div className="metric-item">
                  <span className="metric-label">Cash</span>
                  <span className="metric-value">${model.cash_balance.toFixed(2)}</span>
                </div>
              )}
              {model.active_positions !== undefined && (
                <div className="metric-item">
                  <span className="metric-label">Positions</span>
                  <span className="metric-value">{model.active_positions}</span>
                </div>
              )}
            </div>

            {/* Recent Performance */}
            {model.recent_performance && (
              <div className="recent-performance">
                <h4>Recent Activity</h4>
                <div className="performance-metrics">
                  <div className="perf-metric">
                    <span className="perf-label">Daily Actions</span>
                    <span className="perf-value">{model.recent_performance.daily_actions}</span>
                  </div>
                  <div className="perf-metric">
                    <span className="perf-label">Weekly Actions</span>
                    <span className="perf-value">{model.recent_performance.weekly_actions}</span>
                  </div>
                  <div className="perf-metric">
                    <span className="perf-label">Recent Win Rate</span>
                    <span className="perf-value">{model.recent_performance.recent_win_rate.toFixed(1)}%</span>
                  </div>
                  {model.recent_performance.last_action_time && (
                    <div className="perf-metric">
                      <span className="perf-label">Last Action</span>
                      <span className="perf-value">
                        {new Date(model.recent_performance.last_action_time).toLocaleTimeString()}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Portfolio Toggle */}
            <div className="model-actions">
              <button
                onClick={() => setExpandedModel(expandedModel === model.id ? null : model.id)}
                className="portfolio-toggle"
              >
                {expandedModel === model.id ? 'Hide Portfolio' : 'View Portfolio'}
              </button>
            </div>

            {/* Expanded Portfolio View */}
            {expandedModel === model.id && (
              <div className="portfolio-section">
                <Portfolio modelId={model.id} modelName={model.name} />
              </div>
            )}
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
