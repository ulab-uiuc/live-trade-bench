import React, { useState, useEffect } from 'react';
import Portfolio from './Portfolio';
import { PieChart, LineChart } from './charts';

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
  // Chart data
  holdings?: { [ticker: string]: number };
  profit_history?: Array<{
    timestamp: string;
    profit: number;
    totalValue: number;
  }>;
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
      const transformedModels: Model[] = await Promise.all(
        data.map(async (model: any) => {
          // Fetch chart data for each model
          let chartData = { holdings: {}, profit_history: [] };
          try {
            const chartResponse = await fetch(`/api/models/${model.id}/chart-data`);
            if (chartResponse.ok) {
              chartData = await chartResponse.json();
            }
          } catch (chartError) {
            console.warn(`Failed to fetch chart data for model ${model.id}:`, chartError);
          }

          return {
            id: model.id,
            name: model.name,
            category: model.category || 'stock',
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
            strategy: model.strategy,
            // Chart data
            holdings: chartData.holdings,
            profit_history: chartData.profit_history
          };
        })
      );

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
              <div className="model-title-row">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <h3 className="model-name">{model.name}</h3>
                  <span className={`model-category ${model.category}`}>
                    {getCategoryIcon(model.category)} {model.category}
                  </span>
                  <span className={`status-indicator ${model.status}`} style={{ marginLeft: '8px' }}></span>
                  <span className="status-text" style={{ fontSize: '0.8rem', textTransform: 'capitalize' }}>{model.status}</span>
                </div>
              </div>
              <button
                onClick={() => setExpandedModel(expandedModel === model.id ? null : model.id)}
                className="portfolio-toggle"
              >
                {expandedModel === model.id ? 'Hide Portfolio' : 'View Portfolio'}
              </button>
            </div>


            {/* Category-specific information */}
            <div style={{ marginBottom: '1rem' }}>
              {model.category === 'stock' && model.ticker && (
                <div className="metric-item">
                  <span className="metric-label">Ticker</span>
                  <span className="metric-value">{model.ticker}</span>
                </div>
              )}
            </div>

            {/* Model Charts Layout */}
            <div className="model-charts-layout">
              {/* Charts Section */}
              <div className="charts-section">
                <div className="chart-container">
                  <PieChart
                    holdings={model.holdings || {}}
                    totalValue={model.total_value || 1000}
                    title="Allocation"
                    size="small"
                  />
                </div>
                <div className="chart-container">
                  <LineChart
                    profitHistory={model.profit_history || []}
                    title="Profit Trend"
                    size="small"
                  />
                </div>
              </div>
            </div>


            {/* Expanded Portfolio View - Area Chart Only */}
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
