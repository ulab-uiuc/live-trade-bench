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
  category: 'polymarket' | 'stock';
  status: 'completed' | 'pending' | 'cancelled' | 'failed';
  fees: number;
  totalValue: number;
}

interface TradingHistoryProps {
  tradesData: Trade[];
  setTradesData: (trades: Trade[]) => void;
  lastRefresh: Date;
  setLastRefresh: (date: Date) => void;
}

const TradingHistoryPage: React.FC<TradingHistoryProps> = ({ tradesData, setTradesData, lastRefresh, setLastRefresh }) => {
  const [loading, setLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'polymarket' | 'stock'>('all');
  const [selectedType, setSelectedType] = useState<'all' | 'buy' | 'sell'>('all');
  const [selectedStatus, setSelectedStatus] = useState<'all' | 'completed' | 'pending' | 'cancelled' | 'failed'>('all');

  const fetchTradingHistory = async () => {
    setLoading(true);
    try {
      // Fetch real LLM trading actions from model-actions endpoint
      const response = await fetch('/api/model-actions/?limit=100&hours=168');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();

      // Transform model-actions data to Trade format
      const transformedTrades: Trade[] = data.map((action: any) => ({
        id: action.id,
        timestamp: new Date(action.timestamp),
        symbol: action.symbol,
        type: action.action, // 'buy' or 'sell'
        amount: action.quantity,
        price: action.price,
        profit: 0, // Calculate based on current portfolio value if needed
        model: action.modelName,
        category: action.category || 'stock',
        status: action.status === 'executed' ? 'completed' : 'failed',
        fees: 0, // Model actions don't include fees
        totalValue: action.quantity * action.price
      }));

      setTradesData(transformedTrades);
      setLastRefresh(new Date());
    } catch (error) {
      console.error('Error fetching trading history:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Only fetch if we don't have data or if it's been more than an hour
    const shouldFetch = tradesData.length === 0 ||
      (Date.now() - lastRefresh.getTime()) > 60 * 60 * 1000;

    if (shouldFetch) {
      fetchTradingHistory();
    }

    // Set up hourly refresh interval
    const interval = setInterval(() => {
      fetchTradingHistory();
    }, 60 * 60 * 1000); // Refresh every hour

    return () => clearInterval(interval);
  }, []);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString();
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'buy': return '#28a745';
      case 'sell': return '#dc3545';
      default: return '#6c757d';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#28a745';
      case 'pending': return '#ffc107';
      case 'cancelled': return '#6c757d';
      case 'failed': return '#dc3545';
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

  const filteredTrades = tradesData.filter(trade => {
    const categoryMatch = selectedCategory === 'all' || trade.category === selectedCategory;
    const typeMatch = selectedType === 'all' || trade.type === selectedType;
    const statusMatch = selectedStatus === 'all' || trade.status === selectedStatus;
    return categoryMatch && typeMatch && statusMatch;
  });

  const sortedTrades = filteredTrades.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

  const totalProfit = sortedTrades.reduce((sum, trade) => sum + trade.profit, 0);
  const totalFees = sortedTrades.reduce((sum, trade) => sum + trade.fees, 0);
  const totalTrades = sortedTrades.length;
  const buyTrades = sortedTrades.filter(t => t.type === 'buy').length;
  const sellTrades = sortedTrades.filter(t => t.type === 'sell').length;

  const categoryStats = {
    polymarket: tradesData.filter(t => t.category === 'polymarket').length,
    stock: tradesData.filter(t => t.category === 'stock').length,
    total: tradesData.length
  };

  const typeStats = {
    buy: tradesData.filter(t => t.type === 'buy').length,
    sell: tradesData.filter(t => t.type === 'sell').length,
    total: tradesData.length
  };

  return (
    <div className="trading-history-page">
      <div className="refresh-indicator">
        <h1>Trading History</h1>
        {loading && <div className="spinner"></div>}
        <span style={{ marginLeft: 'auto', fontSize: '0.875rem', color: '#666' }}>
          Last updated: {lastRefresh.toLocaleTimeString()}
        </span>
      </div>

      {/* Summary Statistics */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '15px',
        marginBottom: '20px'
      }}>
        <div style={{
          background: totalProfit >= 0 ? '#e8f5e8' : '#ffe8e8',
          padding: '15px',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: totalProfit >= 0 ? '#28a745' : '#dc3545' }}>
            ${totalProfit.toFixed(2)}
          </div>
          <div style={{ fontSize: '0.9rem', color: '#666' }}>Total P&L</div>
        </div>
        <div style={{
          background: '#f8f9fa',
          padding: '15px',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#007bff' }}>
            {totalTrades}
          </div>
          <div style={{ fontSize: '0.9rem', color: '#666' }}>Total Trades</div>
        </div>
        <div style={{
          background: '#e8f5e8',
          padding: '15px',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#28a745' }}>
            {buyTrades}
          </div>
          <div style={{ fontSize: '0.9rem', color: '#666' }}>Buy Trades</div>
        </div>
        <div style={{
          background: '#ffe8e8',
          padding: '15px',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#dc3545' }}>
            {sellTrades}
          </div>
          <div style={{ fontSize: '0.9rem', color: '#666' }}>Sell Trades</div>
        </div>
        <div style={{
          background: '#fff3cd',
          padding: '15px',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#ffc107' }}>
            ${totalFees.toFixed(2)}
          </div>
          <div style={{ fontSize: '0.9rem', color: '#666' }}>Total Fees</div>
        </div>
      </div>

      {/* Filters */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap', marginBottom: '15px' }}>
          <div>
            <label style={{ fontSize: '0.9rem', fontWeight: 'bold', marginBottom: '5px', display: 'block' }}>
              Category
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value as any)}
              style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
            >
              <option value="all">All Categories ({categoryStats.total})</option>
              <option value="polymarket">Polymarket ({categoryStats.polymarket})</option>
              <option value="stock">Stock ({categoryStats.stock})</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: '0.9rem', fontWeight: 'bold', marginBottom: '5px', display: 'block' }}>
              Type
            </label>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value as any)}
              style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
            >
              <option value="all">All Types ({typeStats.total})</option>
              <option value="buy">Buy ({typeStats.buy})</option>
              <option value="sell">Sell ({typeStats.sell})</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: '0.9rem', fontWeight: 'bold', marginBottom: '5px', display: 'block' }}>
              Status
            </label>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value as any)}
              style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
            >
              <option value="all">All Status</option>
              <option value="completed">Completed</option>
              <option value="pending">Pending</option>
              <option value="cancelled">Cancelled</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </div>
      </div>

      {/* Trades List */}
      <div style={{ maxHeight: 'calc(100vh - 400px)', overflowY: 'auto' }}>
        {sortedTrades.map(trade => (
          <div key={trade.id} className="news-item" style={{
            borderLeft: `4px solid ${getTypeColor(trade.type)}`
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '5px' }}>
                  <span style={{ fontWeight: 'bold', fontSize: '1.1rem' }}>{trade.symbol}</span>
                  <span
                    style={{
                      backgroundColor: getTypeColor(trade.type),
                      color: 'white',
                      padding: '2px 8px',
                      borderRadius: '12px',
                      fontSize: '0.8rem',
                      fontWeight: 'bold',
                      textTransform: 'uppercase'
                    }}
                  >
                    {trade.type}
                  </span>
                  <span
                    style={{
                      backgroundColor: getCategoryColor(trade.category),
                      color: 'white',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontSize: '0.7rem',
                      fontWeight: 'bold',
                      textTransform: 'uppercase'
                    }}
                  >
                    {trade.category}
                  </span>
                  <span
                    style={{
                      backgroundColor: getStatusColor(trade.status),
                      color: 'white',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontSize: '0.7rem',
                      fontWeight: 'bold',
                      textTransform: 'uppercase'
                    }}
                  >
                    {trade.status}
                  </span>
                </div>
                <div style={{ fontSize: '0.9rem', color: '#666' }}>
                  {trade.amount} shares @ ${trade.price.toFixed(2)} = ${trade.totalValue.toFixed(2)}
                </div>
                <div style={{ fontSize: '0.8rem', color: '#999' }}>
                  {formatDate(trade.timestamp)} at {formatTime(trade.timestamp)} • {trade.model}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div className={`trade-amount ${trade.profit >= 0 ? 'profit' : 'loss'}`} style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>
                  {trade.profit >= 0 ? '+' : ''}${trade.profit.toFixed(2)}
                </div>
                {trade.fees > 0 && (
                  <div style={{ fontSize: '0.8rem', color: '#666' }}>
                    Fees: ${trade.fees.toFixed(2)}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {sortedTrades.length === 0 && !loading && (
        <div style={{
          textAlign: 'center',
          padding: '40px',
          color: '#666',
          background: '#f8f9fa',
          borderRadius: '8px'
        }}>
          <p>No trades found for the selected filters.</p>
        </div>
      )}
    </div>
  );
};

export default TradingHistoryPage;
