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
      // Fetch from model-actions API instead of system-log
      const response = await fetch('/api/model-actions/?limit=100');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();

      // Transform model-actions data to SystemAction format
      const transformedActions: SystemAction[] = data.map((action: any) => ({
        id: action.id,
        agentId: action.modelId,
        agentName: action.modelName,
        agentType: 'trading_agent' as const,
        action: action.action.toUpperCase() as 'BUY' | 'SELL' | 'HOLD',
        description: action.reason || `${action.action.toUpperCase()} ${action.quantity} ${action.symbol}`,
        status: action.status === 'executed' ? 'executed' : 'pending',
        timestamp: new Date(action.timestamp),
        targets: [action.symbol],
        metadata: {
          ticker: action.symbol,
          action_type: action.action,
          quantity: action.quantity,
          price: action.price,
          reasoning: action.reason || '',
          portfolio_before: { cash: 0, holdings: {} }, // Not available in model-actions
          portfolio_after: { cash: 0, holdings: {} },  // Not available in model-actions
          total_cost: action.price * action.quantity
        }
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
      <div className="system-log-header">
        <h2 className="system-log-title">📊 System Actions</h2>
        <div className="log-status">
          <span className="status-indicator active"></span>
          Live
        </div>
      </div>

      {/* Status Filter */}
      <div style={{ marginBottom: '1rem' }}>
        <div className="news-filters" style={{ justifyContent: 'flex-start' }}>
          <button
            onClick={() => setSelectedStatus('all')}
            className={`filter-button ${selectedStatus === 'all' ? 'active' : ''}`}
            style={{ fontSize: '0.75rem', padding: '0.375rem 0.75rem' }}
          >
            All ({statusStats.total})
          </button>
          <button
            onClick={() => setSelectedStatus('pending')}
            className={`filter-button ${selectedStatus === 'pending' ? 'active' : ''}`}
            style={{ fontSize: '0.75rem', padding: '0.375rem 0.75rem' }}
          >
            ⏳ Pending ({statusStats.pending})
          </button>
          <button
            onClick={() => setSelectedStatus('executed')}
            className={`filter-button ${selectedStatus === 'executed' ? 'active' : ''}`}
            style={{ fontSize: '0.75rem', padding: '0.375rem 0.75rem' }}
          >
            ✅ Executed ({statusStats.executed})
          </button>
          <button
            onClick={() => setSelectedStatus('evaluated')}
            className={`filter-button ${selectedStatus === 'evaluated' ? 'active' : ''}`}
            style={{ fontSize: '0.75rem', padding: '0.375rem 0.75rem' }}
          >
            📊 Evaluated ({statusStats.evaluated})
          </button>
        </div>
      </div>


      <div className="log-entries">
        {recentActions.map(action => (
          <div key={action.id} className="log-entry">
            <div className="log-entry-header">
              <div>
                <span className="log-time">{formatTimeAgo(action.timestamp)}</span>
                <span className={`log-type ${action.action.toLowerCase()}`} style={{ marginLeft: '0.5rem' }}>
                  {action.action}
                </span>
              </div>
            </div>

            <div className="log-content">
              <strong>{action.agentName}</strong>: {action.description}
            </div>

            {action.metadata && (
              <div className="log-content" style={{ marginTop: '0.5rem', fontSize: '0.75rem' }}>
                ${action.metadata.price.toFixed(2)} × {action.metadata.quantity} shares = ${action.metadata.total_cost.toFixed(2)}
              </div>
            )}

          </div>
        ))}
      </div>

      {recentActions.length === 0 && !loading && (
        <div className="empty-state">
          <div className="empty-state-icon">📊</div>
          <p className="empty-state-text">No trading actions yet</p>
        </div>
      )}
    </div>
  );
};

export default SystemLog;
