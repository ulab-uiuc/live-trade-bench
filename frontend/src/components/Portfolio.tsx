import React, { useState, useEffect } from 'react';
import { AreaChart } from './charts';

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
  portfolio_history?: Array<{
    timestamp: string;
    holdings: { [ticker: string]: number };
    prices: { [ticker: string]: number };
    cash: number;
    totalValue: number;
  }>;
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
      const response = await fetch(`/api/models/${modelId}/portfolio`);
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
      {/* Portfolio Area Chart Only */}
      {portfolio.portfolio_history && portfolio.portfolio_history.length > 0 ? (
        <div className="portfolio-area-chart">
          <AreaChart
            portfolioHistory={portfolio.portfolio_history}
            title={`${modelName} - Portfolio Composition History`}
            size="large"
          />
        </div>
      ) : (
        <div className="portfolio-area-chart">
          <div className="no-data-message">
            <span>📊 No portfolio history available</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default Portfolio;
