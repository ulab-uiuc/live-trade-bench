import React, { useState, useEffect } from 'react';

interface SystemAction {
  id: string;
  agentId: string;
  agentName: string;
  agentType: 'data_collector' | 'trading_agent' | 'monitoring_agent' | 'risk_manager' | 'sentiment_analyzer' | 'market_analyzer';
  action: string;
  description: string;
  status: 'success' | 'warning' | 'error' | 'info';
  timestamp: Date;
  duration?: number; // in milliseconds
  dataProcessed?: number; // number of records processed
  targets?: string[]; // affected symbols, markets, etc.
  metadata?: Record<string, any>; // additional context
}

interface SystemLogProps {
  lastRefresh: Date;
}

const SystemLog: React.FC<SystemLogProps> = ({ lastRefresh }) => {
  const [actions, setActions] = useState<SystemAction[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedAgentType, setSelectedAgentType] = useState<'all' | 'data_collector' | 'trading_agent' | 'monitoring_agent' | 'risk_manager' | 'sentiment_analyzer' | 'market_analyzer'>('all');
  const [selectedStatus, setSelectedStatus] = useState<'all' | 'success' | 'warning' | 'error' | 'info'>('all');

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
      case 'data_collector': return '#17a2b8';
      case 'trading_agent': return '#28a745';
      case 'monitoring_agent': return '#ffc107';
      case 'risk_manager': return '#dc3545';
      case 'sentiment_analyzer': return '#6f42c1';
      case 'market_analyzer': return '#fd7e14';
      default: return '#6c757d';
    }
  };

  const getAgentTypeIcon = (agentType: string) => {
    switch (agentType) {
      case 'data_collector': return '📊';
      case 'trading_agent': return '🤖';
      case 'monitoring_agent': return '👁️';
      case 'risk_manager': return '🛡️';
      case 'sentiment_analyzer': return '💭';
      case 'market_analyzer': return '📈';
      default: return '⚙️';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return '#28a745';
      case 'warning': return '#ffc107';
      case 'error': return '#dc3545';
      case 'info': return '#17a2b8';
      default: return '#6c757d';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return '✅';
      case 'warning': return '⚠️';
      case 'error': return '❌';
      case 'info': return 'ℹ️';
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
    data_collector: actions.filter(a => a.agentType === 'data_collector').length,
    trading_agent: actions.filter(a => a.agentType === 'trading_agent').length,
    monitoring_agent: actions.filter(a => a.agentType === 'monitoring_agent').length,
    risk_manager: actions.filter(a => a.agentType === 'risk_manager').length,
    sentiment_analyzer: actions.filter(a => a.agentType === 'sentiment_analyzer').length,
    market_analyzer: actions.filter(a => a.agentType === 'market_analyzer').length,
    total: actions.length
  };

  const statusStats = {
    success: actions.filter(a => a.status === 'success').length,
    warning: actions.filter(a => a.status === 'warning').length,
    error: actions.filter(a => a.status === 'error').length,
    info: actions.filter(a => a.status === 'info').length,
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

      {/* Agent Type Filter */}
      <div style={{ marginBottom: '15px' }}>
        <h3 style={{ marginBottom: '8px', fontSize: '0.9rem', color: '#333' }}>Agent Types</h3>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <button
            onClick={() => setSelectedAgentType('all')}
            style={{
              padding: '6px 12px',
              border: '1px solid #ddd',
              borderRadius: '16px',
              background: selectedAgentType === 'all' ? '#007bff' : 'white',
              color: selectedAgentType === 'all' ? 'white' : '#333',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            All ({agentTypeStats.total})
          </button>
          <button
            onClick={() => setSelectedAgentType('data_collector')}
            style={{
              padding: '6px 12px',
              border: '1px solid #17a2b8',
              borderRadius: '16px',
              background: selectedAgentType === 'data_collector' ? '#17a2b8' : 'white',
              color: selectedAgentType === 'data_collector' ? 'white' : '#17a2b8',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            📊 Data ({agentTypeStats.data_collector})
          </button>
          <button
            onClick={() => setSelectedAgentType('trading_agent')}
            style={{
              padding: '6px 12px',
              border: '1px solid #28a745',
              borderRadius: '16px',
              background: selectedAgentType === 'trading_agent' ? '#28a745' : 'white',
              color: selectedAgentType === 'trading_agent' ? 'white' : '#28a745',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            🤖 Trading ({agentTypeStats.trading_agent})
          </button>
          <button
            onClick={() => setSelectedAgentType('monitoring_agent')}
            style={{
              padding: '6px 12px',
              border: '1px solid #ffc107',
              borderRadius: '16px',
              background: selectedAgentType === 'monitoring_agent' ? '#ffc107' : 'white',
              color: selectedAgentType === 'monitoring_agent' ? 'white' : '#ffc107',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            👁️ Monitor ({agentTypeStats.monitoring_agent})
          </button>
          <button
            onClick={() => setSelectedAgentType('risk_manager')}
            style={{
              padding: '6px 12px',
              border: '1px solid #dc3545',
              borderRadius: '16px',
              background: selectedAgentType === 'risk_manager' ? '#dc3545' : 'white',
              color: selectedAgentType === 'risk_manager' ? 'white' : '#dc3545',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            🛡️ Risk ({agentTypeStats.risk_manager})
          </button>
          <button
            onClick={() => setSelectedAgentType('sentiment_analyzer')}
            style={{
              padding: '6px 12px',
              border: '1px solid #6f42c1',
              borderRadius: '16px',
              background: selectedAgentType === 'sentiment_analyzer' ? '#6f42c1' : 'white',
              color: selectedAgentType === 'sentiment_analyzer' ? 'white' : '#6f42c1',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            💭 Sentiment ({agentTypeStats.sentiment_analyzer})
          </button>
          <button
            onClick={() => setSelectedAgentType('market_analyzer')}
            style={{
              padding: '6px 12px',
              border: '1px solid #fd7e14',
              borderRadius: '16px',
              background: selectedAgentType === 'market_analyzer' ? '#fd7e14' : 'white',
              color: selectedAgentType === 'market_analyzer' ? 'white' : '#fd7e14',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            📈 Market ({agentTypeStats.market_analyzer})
          </button>
        </div>
      </div>

      {/* Status Filter */}
      <div style={{ marginBottom: '15px' }}>
        <h3 style={{ marginBottom: '8px', fontSize: '0.9rem', color: '#333' }}>Status</h3>
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
            onClick={() => setSelectedStatus('success')}
            style={{
              padding: '6px 12px',
              border: '1px solid #28a745',
              borderRadius: '16px',
              background: selectedStatus === 'success' ? '#28a745' : 'white',
              color: selectedStatus === 'success' ? 'white' : '#28a745',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            ✅ Success ({statusStats.success})
          </button>
          <button
            onClick={() => setSelectedStatus('warning')}
            style={{
              padding: '6px 12px',
              border: '1px solid #ffc107',
              borderRadius: '16px',
              background: selectedStatus === 'warning' ? '#ffc107' : 'white',
              color: selectedStatus === 'warning' ? 'white' : '#ffc107',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            ⚠️ Warning ({statusStats.warning})
          </button>
          <button
            onClick={() => setSelectedStatus('error')}
            style={{
              padding: '6px 12px',
              border: '1px solid #dc3545',
              borderRadius: '16px',
              background: selectedStatus === 'error' ? '#dc3545' : 'white',
              color: selectedStatus === 'error' ? 'white' : '#dc3545',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            ❌ Error ({statusStats.error})
          </button>
          <button
            onClick={() => setSelectedStatus('info')}
            style={{
              padding: '6px 12px',
              border: '1px solid #17a2b8',
              borderRadius: '16px',
              background: selectedStatus === 'info' ? '#17a2b8' : 'white',
              color: selectedStatus === 'info' ? 'white' : '#17a2b8',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            ℹ️ Info ({statusStats.info})
          </button>
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
                <span style={{ fontSize: '16px' }}>{getStatusIcon(action.status)}</span>
                <div>
                  <div style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>
                    {action.agentName}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#666' }}>
                    {action.action}
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                <span
                  style={{
                    backgroundColor: getAgentTypeColor(action.agentType),
                    color: 'white',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontSize: '0.7rem',
                    fontWeight: 'bold',
                    textTransform: 'uppercase'
                  }}
                >
                  {action.agentType.replace('_', ' ')}
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
                {action.duration && (
                  <span>⏱️ {formatDuration(action.duration)}</span>
                )}
                {action.dataProcessed && (
                  <span>📊 {action.dataProcessed.toLocaleString()} records</span>
                )}
                {action.targets && action.targets.length > 0 && (
                  <span>🎯 {action.targets.join(', ')}</span>
                )}
              </div>
              <div>
                ID: {action.agentId}
              </div>
            </div>

            {action.metadata && Object.keys(action.metadata).length > 0 && (
              <div style={{ 
                fontSize: '0.75rem', 
                color: '#666', 
                background: '#f8f9fa',
                padding: '4px 8px',
                borderRadius: '4px',
                marginTop: '6px'
              }}>
                <details>
                  <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>Details</summary>
                  <pre style={{ margin: '4px 0 0 0', fontSize: '0.7rem', whiteSpace: 'pre-wrap' }}>
                    {JSON.stringify(action.metadata, null, 2)}
                  </pre>
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
          <p>No system actions found for the selected filters.</p>
        </div>
      )}
    </div>
  );
};

export default SystemLog; 