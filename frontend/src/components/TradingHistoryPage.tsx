import React, { useState, useEffect } from 'react';
import type { Trade } from '../types';

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
    <div style={{
      padding: '2rem',
      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%)',
      color: '#ffffff',
      minHeight: '100vh',
      fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
      position: 'relative',
      zIndex: 1000
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '2rem',
        borderBottom: '1px solid #374151',
        paddingBottom: '1rem'
      }}>
        <h1 style={{
          fontSize: '2.5rem',
          color: '#ffffff',
          margin: 0,
          fontWeight: '800',
          background: 'linear-gradient(135deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text'
        }}>Trading History</h1>
        {loading && <div style={{
          width: '24px',
          height: '24px',
          border: '3px solid #374151',
          borderTop: '3px solid #60a5fa',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }}></div>}
        <span style={{ fontSize: '0.875rem', color: '#94a3b8' }}>
          Last updated: {lastRefresh.toLocaleTimeString()}
        </span>
      </div>


      {/* Filters */}
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
          <div>
            <label style={{ fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem', display: 'block', color: '#d1d5db' }}>
              Category
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value as any)}
              style={{
                padding: '0.5rem 0.75rem',
                borderRadius: '0.375rem',
                border: '1px solid #374151',
                background: '#1f2937',
                color: '#ffffff',
                fontSize: '0.875rem'
              }}
            >
              <option value="all">All Categories ({categoryStats.total})</option>
              <option value="polymarket">Polymarket ({categoryStats.polymarket})</option>
              <option value="stock">Stock ({categoryStats.stock})</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem', display: 'block', color: '#d1d5db' }}>
              Type
            </label>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value as any)}
              style={{
                padding: '0.5rem 0.75rem',
                borderRadius: '0.375rem',
                border: '1px solid #374151',
                background: '#1f2937',
                color: '#ffffff',
                fontSize: '0.875rem'
              }}
            >
              <option value="all">All Types ({typeStats.total})</option>
              <option value="buy">Buy ({typeStats.buy})</option>
              <option value="sell">Sell ({typeStats.sell})</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem', display: 'block', color: '#d1d5db' }}>
              Status
            </label>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value as any)}
              style={{
                padding: '0.5rem 0.75rem',
                borderRadius: '0.375rem',
                border: '1px solid #374151',
                background: '#1f2937',
                color: '#ffffff',
                fontSize: '0.875rem'
              }}
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
          <div key={trade.id} style={{
            borderLeft: `4px solid ${getTypeColor(trade.type)}`,
            background: '#1f2937',
            border: '1px solid #374151',
            borderRadius: '0.5rem',
            padding: '1.5rem',
            marginBottom: '1rem',
            transition: 'all 0.2s ease',
            cursor: 'pointer'
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
                <div style={{ fontSize: '0.9rem', color: '#94a3b8' }}>
                  {trade.amount} shares @ ${trade.price.toFixed(2)} = ${trade.totalValue.toFixed(2)}
                </div>
                <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>
                  {formatDate(trade.timestamp)} at {formatTime(trade.timestamp)} • {trade.model}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{
                  fontSize: '1.2rem',
                  fontWeight: 'bold',
                  color: trade.profit >= 0 ? '#10b981' : '#ef4444'
                }}>
                  {trade.profit >= 0 ? '+' : ''}${trade.profit.toFixed(2)}
                </div>
                {trade.fees > 0 && (
                  <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
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
          padding: '3rem',
          color: '#6b7280',
          background: '#1f2937',
          borderRadius: '0.5rem',
          border: '1px solid #374151'
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📊</div>
          <p style={{ fontSize: '1.125rem', margin: 0 }}>No trades found for the selected filters.</p>
        </div>
      )}
    </div>
  );
};

export default TradingHistoryPage;
