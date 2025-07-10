import React, { useState, useEffect } from 'react';

interface Trade {
  id: string;
  timestamp: Date;
  symbol: string;
  type: 'buy' | 'sell';
  amount: number;
  price: number;
  profit: number;
  model: string;
}

interface TradingHistoryProps {
  lastRefresh: Date;
}

const TradingHistory: React.FC<TradingHistoryProps> = ({ lastRefresh }) => {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchTradingHistory = async () => {
    setLoading(true);
    try {
      // Fetch real trading data instead of sample data
      const response = await fetch('http://localhost:8000/api/trades/real?ticker=NVDA&days=7');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();

      // Transform backend data to frontend format
      const transformedTrades: Trade[] = data.map((trade: any) => ({
        id: trade.id,
        timestamp: new Date(trade.timestamp),
        symbol: trade.symbol,
        type: trade.type,
        amount: trade.amount,
        price: trade.price,
        profit: trade.profit,
        model: trade.model
      }));

      setTrades(transformedTrades);
    } catch (error) {
      console.error('Error fetching trading history:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTradingHistory();
  }, [lastRefresh]);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const totalProfit = trades.reduce((sum, trade) => sum + trade.profit, 0);

  return (
    <div className="trading-history">
      <div className="refresh-indicator">
        <h2>Trading History</h2>
        {loading && <div className="spinner"></div>}
      </div>

      <div style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
        <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1rem' }}>Total P&L Today</h3>
        <div className={`trade-amount ${totalProfit >= 0 ? 'profit' : 'loss'}`} style={{ fontSize: '1.25rem' }}>
          ${totalProfit.toFixed(2)}
        </div>
      </div>

      <div style={{ maxHeight: 'calc(100vh - 300px)', overflowY: 'auto' }}>
        {trades.map(trade => (
          <div key={trade.id} className={`trade-item ${trade.profit >= 0 ? 'profit' : 'loss'}`}>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong>{trade.symbol}</strong>
                <span className={`trade-amount ${trade.profit >= 0 ? 'profit' : 'loss'}`}>
                  {trade.profit >= 0 ? '+' : ''}${trade.profit.toFixed(2)}
                </span>
              </div>
              <div style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.25rem' }}>
                {trade.type.toUpperCase()} {trade.amount} @ ${trade.price.toFixed(2)}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#999', marginTop: '0.25rem' }}>
                {formatTime(trade.timestamp)} • {trade.model}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ fontSize: '0.875rem', color: '#666', marginTop: '1rem', textAlign: 'center' }}>
        Last updated: {lastRefresh.toLocaleTimeString()}
      </div>
    </div>
  );
};

export default TradingHistory;
