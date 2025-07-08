import React, { useState, useEffect } from 'react';

interface ModelAction {
  id: string;
  modelId: string;
  modelName: string;
  action: 'buy' | 'sell' | 'hold' | 'alert';
  symbol: string;
  price: number;
  quantity?: number;
  confidence: number;
  reason: string;
  timestamp: Date;
  category: 'polymarket' | 'stock' | 'option';
  status: 'pending' | 'executed' | 'cancelled' | 'failed';
}

interface ModelActionsProps {
  lastRefresh: Date;
}

const ModelActions: React.FC<ModelActionsProps> = ({ lastRefresh }) => {
  const [actions, setActions] = useState<ModelAction[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchModelActions = async () => {
    setLoading(true);
    try {
      // Fetch from backend API
      const response = await fetch('http://localhost:8000/api/model-actions/');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      // Transform backend data to frontend format
      const transformedActions: ModelAction[] = data.map((action: any) => ({
        id: action.id,
        modelId: action.model_id,
        modelName: action.model_name,
        action: action.action,
        symbol: action.symbol,
        price: action.price,
        quantity: action.quantity,
        confidence: action.confidence,
        reason: action.reason,
        timestamp: new Date(action.timestamp),
        category: action.category,
        status: action.status
      }));
      
      setActions(transformedActions);
    } catch (error) {
      console.error('Error fetching model actions:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModelActions();
    
    // Auto-refresh every 30 seconds for real-time updates
    const interval = setInterval(fetchModelActions, 30 * 1000);
    
    return () => clearInterval(interval);
  }, [lastRefresh]);

  const getActionColor = (action: string) => {
    switch (action) {
      case 'buy': return '#28a745';
      case 'sell': return '#dc3545';
      case 'hold': return '#6c757d';
      case 'alert': return '#ffc107';
      default: return '#6c757d';
    }
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'buy': return '📈';
      case 'sell': return '📉';
      case 'hold': return '⏸️';
      case 'alert': return '⚠️';
      default: return '📊';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'executed': return '#28a745';
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
      case 'option': return '#e67e22';
      default: return '#95a5a6';
    }
  };

  const formatTimeAgo = (date: Date) => {
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffInSeconds < 60) {
      return `${diffInSeconds}s ago`;
    } else if (diffInSeconds < 3600) {
      return `${Math.floor(diffInSeconds / 60)}m ago`;
    } else {
      return `${Math.floor(diffInSeconds / 3600)}h ago`;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return '#28a745';
    if (confidence >= 0.6) return '#ffc107';
    return '#dc3545';
  };

  const recentActions = actions
    .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
    .slice(0, 10); // Show only the 10 most recent actions

  const actionStats = {
    buy: actions.filter(a => a.action === 'buy').length,
    sell: actions.filter(a => a.action === 'sell').length,
    hold: actions.filter(a => a.action === 'hold').length,
    alert: actions.filter(a => a.action === 'alert').length,
    total: actions.length
  };

  return (
    <div className="model-actions">
      <div className="refresh-indicator">
        <h2>Model Actions</h2>
        {loading && <div className="spinner"></div>}
        <span style={{ marginLeft: 'auto', fontSize: '0.875rem', color: '#666' }}>
          Last updated: {lastRefresh.toLocaleTimeString()}
        </span>
      </div>

      {/* Action Statistics */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(2, 1fr)', 
        gap: '10px', 
        marginBottom: '20px' 
      }}>
        <div style={{ 
          background: '#e8f5e8', 
          padding: '10px', 
          borderRadius: '8px', 
          textAlign: 'center' 
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#28a745' }}>
            {actionStats.buy}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#666' }}>Buy Signals</div>
        </div>
        <div style={{ 
          background: '#ffe8e8', 
          padding: '10px', 
          borderRadius: '8px', 
          textAlign: 'center' 
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#dc3545' }}>
            {actionStats.sell}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#666' }}>Sell Signals</div>
        </div>
        <div style={{ 
          background: '#f8f9fa', 
          padding: '10px', 
          borderRadius: '8px', 
          textAlign: 'center' 
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#6c757d' }}>
            {actionStats.hold}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#666' }}>Hold Signals</div>
        </div>
        <div style={{ 
          background: '#fff3cd', 
          padding: '10px', 
          borderRadius: '8px', 
          textAlign: 'center' 
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#ffc107' }}>
            {actionStats.alert}
          </div>
          <div style={{ fontSize: '0.8rem', color: '#666' }}>Alerts</div>
        </div>
      </div>

      <div style={{ maxHeight: 'calc(100vh - 400px)', overflowY: 'auto' }}>
        {recentActions.map(action => (
          <div key={action.id} className="action-item" style={{
            border: `1px solid #e9ecef`,
            borderRadius: '8px',
            padding: '12px',
            marginBottom: '10px',
            background: 'white',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            borderLeft: `4px solid ${getActionColor(action.action)}`
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '18px' }}>{getActionIcon(action.action)}</span>
                <div>
                  <div style={{ fontWeight: 'bold', fontSize: '1rem' }}>
                    {action.symbol} - {action.action.toUpperCase()}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#666' }}>
                    {action.modelName}
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                <span
                  style={{
                    backgroundColor: getCategoryColor(action.category),
                    color: 'white',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontSize: '0.7rem',
                    fontWeight: 'bold',
                    textTransform: 'uppercase'
                  }}
                >
                  {action.category}
                </span>
                <span
                  style={{
                    backgroundColor: getStatusColor(action.status),
                    color: 'white',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontSize: '0.7rem',
                    fontWeight: 'bold',
                    textTransform: 'uppercase'
                  }}
                >
                  {action.status}
                </span>
              </div>
            </div>

            <div style={{ marginBottom: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.9rem' }}>
                  Price: <strong>${action.price.toFixed(2)}</strong>
                </span>
                {action.quantity && (
                  <span style={{ fontSize: '0.9rem' }}>
                    Qty: <strong>{action.quantity}</strong>
                  </span>
                )}
              </div>
            </div>

            <div style={{ marginBottom: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.8rem', color: '#666' }}>
                  Confidence: 
                  <span style={{ 
                    color: getConfidenceColor(action.confidence), 
                    fontWeight: 'bold',
                    marginLeft: '4px'
                  }}>
                    {(action.confidence * 100).toFixed(0)}%
                  </span>
                </span>
                <span style={{ fontSize: '0.8rem', color: '#666' }}>
                  {formatTimeAgo(action.timestamp)}
                </span>
              </div>
            </div>

            {action.reason && (
              <div style={{ 
                fontSize: '0.8rem', 
                color: '#666', 
                fontStyle: 'italic',
                background: '#f8f9fa',
                padding: '6px',
                borderRadius: '4px',
                marginTop: '6px'
              }}>
                "{action.reason}"
              </div>
            )}
          </div>
        ))}
      </div>

      {recentActions.length === 0 && !loading && (
        <div style={{ 
          textAlign: 'center', 
          padding: '40px', 
          color: '#666',
          background: '#f8f9fa',
          borderRadius: '8px'
        }}>
          <p>No recent model actions.</p>
        </div>
      )}
    </div>
  );
};

export default ModelActions; 