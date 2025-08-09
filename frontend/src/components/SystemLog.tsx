import React, { useState, useEffect } from 'react';

interface SystemAction {
  id: string;
  agentId: string;
  agentName: string;
  agentType: 'trading_agent';
  action: 'BUY' | 'SELL' | 'HOLD';
  description: string;
  status: 'pending' | 'executed' | 'evaluated';
  timestamp: Date;
  targets?: string[]; // affected tickers
  metadata?: {
    ticker: string;
    action_type: string;
    quantity: number;
    price: number;
    reasoning: string;
    portfolio_before: {
      cash: number;
      holdings: Record<string, number>;
    };
    portfolio_after: {
      cash: number;
      holdings: Record<string, number>;
    };
    total_cost: number;
  };
}

interface SystemLogProps {
  lastRefresh: Date;
}

const SystemLog: React.FC<SystemLogProps> = ({ lastRefresh }) => {
  const [actions, setActions] = useState<SystemAction[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedAgentType, setSelectedAgentType] = useState<'all' | 'trading_agent'>('all');
  const [selectedStatus, setSelectedStatus] = useState<'all' | 'pending' | 'executed' | 'evaluated'>('all');

  const fetchSystemLog = async () => {
    setLoading(true);
    try {
      // Fetch from backend API
      const response = await fetch('http://localhost:8000/api/system-log/');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();

      // Transform backend data to frontend format
      const transformedActions: SystemAction[] = data.map((action: any) => ({
        id: action.id,
        agentId: action.agent_id,
        agentName: action.agent_name,
        agentType: action.agent_type,
        action: action.action,
        description: action.description,
        status: action.status,
        timestamp: new Date(action.timestamp),
        duration: action.duration,
        dataProcessed: action.data_processed,
        targets: action.targets,
        metadata: action.metadata
      }));

      setActions(transformedActions);
    } catch (error) {
      console.error('Error fetching system log:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSystemLog();

    // Auto-refresh every 15 seconds for real-time updates
    const interval = setInterval(fetchSystemLog, 15 * 1000);

    return () => clearInterval(interval);
  }, [lastRefresh]);

  const getAgentTypeColor = (agentType: string) => {
    switch (agentType) {
      case 'trading_agent': return '#28a745';
      default: return '#6c757d';
    }
  };

  const getAgentTypeIcon = (agentType: string) => {
    switch (agentType) {
      case 'trading_agent': return '🤖';
      default: return '⚙️';
    }
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'BUY': return '📈';
      case 'SELL': return '📉';
      case 'HOLD': return '⏸️';
      default: return '📝';
    }
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case 'BUY': return '#28a745';
      case 'SELL': return '#dc3545';
      case 'HOLD': return '#ffc107';
      default: return '#6c757d';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return '#ffc107';
      case 'executed': return '#17a2b8';
      case 'evaluated': return '#28a745';
      default: return '#6c757d';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return '⏳';
      case 'executed': return '✅';
      case 'evaluated': return '📊';
      default: return '📝';
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

  const formatDuration = (duration?: number) => {
    if (!duration) return '';
    if (duration < 1000) return `${duration}ms`;
    return `${(duration / 1000).toFixed(1)}s`;
  };

  const filteredActions = actions.filter(action => {
    const agentTypeMatch = selectedAgentType === 'all' || action.agentType === selectedAgentType;
    const statusMatch = selectedStatus === 'all' || action.status === selectedStatus;
    return agentTypeMatch && statusMatch;
  });

  const recentActions = filteredActions
    .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
    .slice(0, 20); // Show only the 20 most recent actions

  const agentTypeStats = {
    trading_agent: actions.filter(a => a.agentType === 'trading_agent').length,
    total: actions.length
  };

  const statusStats = {
    pending: actions.filter(a => a.status === 'pending').length,
    executed: actions.filter(a => a.status === 'executed').length,
    evaluated: actions.filter(a => a.status === 'evaluated').length,
    total: actions.length
  };

  const actionStats = {
    buy: actions.filter(a => a.action === 'BUY').length,
    sell: actions.filter(a => a.action === 'SELL').length,
    hold: actions.filter(a => a.action === 'HOLD').length,
    total: actions.length
  };

  return (
    <div className="system-log">
      <div className="refresh-indicator">
        <h2>System Log</h2>
        {loading && <div className="spinner"></div>}
        <span style={{ marginLeft: 'auto', fontSize: '0.875rem', color: '#666' }}>
          Last updated: {lastRefresh.toLocaleTimeString()}
        </span>
      </div>

      {/* Status Filter */}
      <div style={{ marginBottom: '15px' }}>
        <h3 style={{ marginBottom: '8px', fontSize: '0.9rem', color: '#333' }}>Trading Action Status</h3>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <button
            onClick={() => setSelectedStatus('all')}
            style={{
              padding: '6px 12px',
              border: '1px solid #ddd',
              borderRadius: '16px',
              background: selectedStatus === 'all' ? '#007bff' : 'white',
              color: selectedStatus === 'all' ? 'white' : '#333',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            All ({statusStats.total})
          </button>
          <button
            onClick={() => setSelectedStatus('pending')}
            style={{
              padding: '6px 12px',
              border: '1px solid #ffc107',
              borderRadius: '16px',
              background: selectedStatus === 'pending' ? '#ffc107' : 'white',
              color: selectedStatus === 'pending' ? 'white' : '#ffc107',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            ⏳ Pending ({statusStats.pending})
          </button>
          <button
            onClick={() => setSelectedStatus('executed')}
            style={{
              padding: '6px 12px',
              border: '1px solid #17a2b8',
              borderRadius: '16px',
              background: selectedStatus === 'executed' ? '#17a2b8' : 'white',
              color: selectedStatus === 'executed' ? 'white' : '#17a2b8',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            ✅ Executed ({statusStats.executed})
          </button>
          <button
            onClick={() => setSelectedStatus('evaluated')}
            style={{
              padding: '6px 12px',
              border: '1px solid #28a745',
              borderRadius: '16px',
              background: selectedStatus === 'evaluated' ? '#28a745' : 'white',
              color: selectedStatus === 'evaluated' ? 'white' : '#28a745',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            📊 Evaluated ({statusStats.evaluated})
          </button>
        </div>
      </div>

      {/* Action Summary */}
      <div style={{ marginBottom: '15px' }}>
        <h3 style={{ marginBottom: '8px', fontSize: '0.9rem', color: '#333' }}>Action Summary</h3>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <span style={{
            padding: '4px 8px',
            background: '#e8f5e8',
            color: '#28a745',
            borderRadius: '12px',
            fontSize: '11px',
            fontWeight: 'bold'
          }}>
            📈 {actionStats.buy} BUY
          </span>
          <span style={{
            padding: '4px 8px',
            background: '#ffeaea',
            color: '#dc3545',
            borderRadius: '12px',
            fontSize: '11px',
            fontWeight: 'bold'
          }}>
            📉 {actionStats.sell} SELL
          </span>
          <span style={{
            padding: '4px 8px',
            background: '#fff3cd',
            color: '#ffc107',
            borderRadius: '12px',
            fontSize: '11px',
            fontWeight: 'bold'
          }}>
            ⏸️ {actionStats.hold} HOLD
          </span>
        </div>
      </div>

      <div style={{ maxHeight: 'calc(100vh - 350px)', overflowY: 'auto' }}>
        {recentActions.map(action => (
          <div key={action.id} className="log-item" style={{
            border: `1px solid #e9ecef`,
            borderRadius: '8px',
            padding: '12px',
            marginBottom: '8px',
            background: 'white',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            borderLeft: `4px solid ${getStatusColor(action.status)}`
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '16px' }}>{getAgentTypeIcon(action.agentType)}</span>
                <span style={{ fontSize: '16px' }}>{getActionIcon(action.action)}</span>
                <span style={{ fontSize: '16px' }}>{getStatusIcon(action.status)}</span>
                <div>
                  <div style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>
                    {action.agentName}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#666' }}>
                    {action.action} {action.targets ? action.targets[0] : ''}
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                <span
                  style={{
                    backgroundColor: getActionColor(action.action),
                    color: 'white',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontSize: '0.7rem',
                    fontWeight: 'bold',
                    textTransform: 'uppercase'
                  }}
                >
                  {action.action}
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
                <span style={{ fontSize: '0.8rem', color: '#666' }}>
                  {formatTimeAgo(action.timestamp)}
                </span>
              </div>
            </div>

            <div style={{ fontSize: '0.85rem', color: '#333', marginBottom: '6px' }}>
              {action.description}
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', color: '#666' }}>
              <div style={{ display: 'flex', gap: '12px' }}>
                {action.metadata && (
                  <>
                    <span>💰 ${action.metadata.price.toFixed(2)}</span>
                    <span>📊 {action.metadata.quantity} shares</span>
                    {action.metadata.total_cost > 0 && (
                      <span>💵 ${action.metadata.total_cost.toFixed(2)} total</span>
                    )}
                  </>
                )}
                {action.targets && action.targets.length > 0 && (
                  <span>🎯 {action.targets.join(', ')}</span>
                )}
              </div>
              <div>
                Model: {action.agentId}
              </div>
            </div>

            {action.metadata?.reasoning && (
              <div style={{
                fontSize: '0.8rem',
                color: '#555',
                background: '#f8f9fa',
                padding: '6px 8px',
                borderRadius: '4px',
                marginTop: '8px',
                borderLeft: '3px solid #007bff'
              }}>
                <strong>Reasoning:</strong> {action.metadata.reasoning}
              </div>
            )}

            {action.metadata && (action.metadata.portfolio_before || action.metadata.portfolio_after) && (
              <div style={{
                fontSize: '0.75rem',
                color: '#666',
                background: '#f8f9fa',
                padding: '4px 8px',
                borderRadius: '4px',
                marginTop: '6px'
              }}>
                <details>
                  <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>Portfolio Changes</summary>
                  <div style={{ margin: '4px 0', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                    {action.metadata.portfolio_before && (
                      <div>
                        <div style={{ fontWeight: 'bold', marginBottom: '2px' }}>Before:</div>
                        <div>Cash: ${action.metadata.portfolio_before.cash.toFixed(2)}</div>
                        <div>Holdings: {Object.keys(action.metadata.portfolio_before.holdings).length > 0
                          ? Object.entries(action.metadata.portfolio_before.holdings)
                            .map(([ticker, qty]) => `${ticker}: ${qty}`)
                            .join(', ')
                          : 'None'}</div>
                      </div>
                    )}
                    {action.metadata.portfolio_after && (
                      <div>
                        <div style={{ fontWeight: 'bold', marginBottom: '2px' }}>After:</div>
                        <div>Cash: ${action.metadata.portfolio_after.cash.toFixed(2)}</div>
                        <div>Holdings: {Object.keys(action.metadata.portfolio_after.holdings).length > 0
                          ? Object.entries(action.metadata.portfolio_after.holdings)
                            .map(([ticker, qty]) => `${ticker}: ${qty}`)
                            .join(', ')
                          : 'None'}</div>
                      </div>
                    )}
                  </div>
                </details>
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
          <p style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '8px' }}>No Trading Actions Yet</p>
          <p style={{ fontSize: '14px' }}>Trading models haven't generated any BUY/SELL/HOLD decisions yet.</p>
          <p style={{ fontSize: '12px', color: '#999', marginTop: '12px' }}>
            Actions will appear here when models analyze market data and make trading decisions.
          </p>
        </div>
      )}
    </div>
  );
};

export default SystemLog;
