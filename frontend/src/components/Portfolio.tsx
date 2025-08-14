import React, { useState, useEffect } from 'react';

interface PortfolioData {
  model_id: string;
  model_name: string;
  cash: number;
  holdings: { [ticker: string]: number };
  total_value: number;
  total_value_realtime?: number;
  return_pct: number;
  return_pct_realtime?: number;
  unrealized_pnl: number;
  unrealized_pnl_realtime?: number;
  positions: { [ticker: string]: any };
  market_data_available: boolean;
  last_updated: string;
}

interface PortfolioProps {
  modelId: string;
  modelName: string;
}

const Portfolio: React.FC<PortfolioProps> = ({ modelId, modelName }) => {
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const fetchPortfolio = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`http://localhost:5000/api/system-log/portfolios/${modelId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setPortfolio(data);
      setLastRefresh(new Date());
    } catch (error) {
      console.error('Error fetching portfolio:', error);
      setError('Failed to load portfolio data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPortfolio();
    // Refresh every 30 seconds for real-time data
    const interval = setInterval(fetchPortfolio, 30000);
    return () => clearInterval(interval);
  }, [modelId]);

  if (loading && !portfolio) {
    return (
      <div className="portfolio-loading">
        <div className="spinner"></div>
        <span>Loading portfolio...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="portfolio-error">
        <span>⚠️ {error}</span>
        <button onClick={fetchPortfolio} className="retry-button">
          Retry
        </button>
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className="portfolio-empty">
        <span>No portfolio data available</span>
      </div>
    );
  }

  const useRealtimeData = portfolio.market_data_available && portfolio.total_value_realtime !== undefined;
  const totalValue = useRealtimeData ? portfolio.total_value_realtime! : portfolio.total_value;
  const returnPct = useRealtimeData ? portfolio.return_pct_realtime! : portfolio.return_pct;
  const unrealizedPnl = useRealtimeData ? portfolio.unrealized_pnl_realtime! : portfolio.unrealized_pnl;

  return (
    <div className="portfolio-container">
      <div className="portfolio-header">
        <h3 className="portfolio-title">{modelName} Portfolio</h3>
        <div className="portfolio-refresh">
          {loading && <div className="spinner small"></div>}
          <span className="refresh-time">
            Last updated: {lastRefresh.toLocaleTimeString()}
          </span>
          {useRealtimeData && (
            <span className="realtime-indicator">
              🔴 Real-time
            </span>
          )}
        </div>
      </div>

      <div className="portfolio-summary">
        <div className="summary-card">
          <div className="summary-label">Total Value</div>
          <div className="summary-value">
            ${totalValue.toFixed(2)}
            {useRealtimeData && portfolio.total_value !== totalValue && (
              <span className="historical-value">
                (${portfolio.total_value.toFixed(2)})
              </span>
            )}
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-label">Cash Balance</div>
          <div className="summary-value">
            ${portfolio.cash.toFixed(2)}
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-label">Return</div>
          <div className={`summary-value ${returnPct >= 0 ? 'positive' : 'negative'}`}>
            {returnPct >= 0 ? '+' : ''}{returnPct.toFixed(2)}%
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-label">Unrealized P&L</div>
          <div className={`summary-value ${unrealizedPnl >= 0 ? 'positive' : 'negative'}`}>
            {unrealizedPnl >= 0 ? '+' : ''}${unrealizedPnl.toFixed(2)}
          </div>
        </div>
      </div>

      {Object.keys(portfolio.holdings).length > 0 && (
        <div className="holdings-section">
          <h4>Holdings</h4>
          <div className="holdings-list">
            {Object.entries(portfolio.holdings).map(([ticker, quantity]) => {
              const positionData = portfolio.positions[ticker];
              const currentPrice = useRealtimeData && positionData?.current_price_realtime
                ? positionData.current_price_realtime
                : positionData?.current_price || 0;
              const currentValue = useRealtimeData && positionData?.current_value_realtime
                ? positionData.current_value_realtime
                : quantity * currentPrice;
              const unrealizedPnlPosition = useRealtimeData && positionData?.unrealized_pnl_realtime
                ? positionData.unrealized_pnl_realtime
                : positionData?.unrealized_pnl || 0;

              return (
                <div key={ticker} className="holding-item">
                  <div className="holding-header">
                    <span className="holding-ticker">{ticker}</span>
                    <span className="holding-quantity">{quantity} shares</span>
                  </div>
                  <div className="holding-details">
                    <div className="holding-metric">
                      <span className="metric-label">Price</span>
                      <span className="metric-value">
                        ${currentPrice.toFixed(2)}
                      </span>
                    </div>
                    <div className="holding-metric">
                      <span className="metric-label">Value</span>
                      <span className="metric-value">
                        ${currentValue.toFixed(2)}
                      </span>
                    </div>
                    <div className="holding-metric">
                      <span className="metric-label">P&L</span>
                      <span className={`metric-value ${unrealizedPnlPosition >= 0 ? 'positive' : 'negative'}`}>
                        {unrealizedPnlPosition >= 0 ? '+' : ''}${unrealizedPnlPosition.toFixed(2)}
                      </span>
                    </div>
                    {positionData?.avg_price && (
                      <div className="holding-metric">
                        <span className="metric-label">Avg Cost</span>
                        <span className="metric-value">
                          ${positionData.avg_price.toFixed(2)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {Object.keys(portfolio.holdings).length === 0 && (
        <div className="no-holdings">
          <span>No current holdings</span>
        </div>
      )}
    </div>
  );
};

export default Portfolio;
