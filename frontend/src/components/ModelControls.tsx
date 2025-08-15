import React, { useState, useEffect } from 'react';

interface SystemStatus {
  system_running: boolean;
  cycle_interval_minutes: number;
  total_agents: number;
  active_agents: number;
  tickers: string[];
  initial_cash: number;
  total_actions: number;
  last_cycle_time?: string;
  next_cycle_time?: string;
  execution_stats: {
    total_cycles: number;
    successful_cycles: number;
    failed_cycles: number;
    total_stock_actions?: number;
    total_polymarket_actions?: number;
    successful_stock_actions?: number;
    successful_polymarket_actions?: number;
    failed_stock_actions?: number;
    failed_polymarket_actions?: number;
    // Backward compatibility
    total_actions?: number;
    successful_actions?: number;
    failed_actions?: number;
  };
  active_models: { [key: string]: boolean };
  last_action?: any;
}

interface ModelControlsProps {
  models: Array<{
    id: string;
    name: string;
    status: string;
    is_activated?: boolean;
  }>;
  onModelUpdate?: () => void;
}

const ModelControls: React.FC<ModelControlsProps> = ({ models, onModelUpdate }) => {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [newInterval, setNewInterval] = useState<number>(30);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const fetchSystemStatus = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/models/system-status');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setSystemStatus(data);
      setNewInterval(data.cycle_interval_minutes);
      setLastRefresh(new Date());
    } catch (error) {
      console.error('Error fetching system status:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSystemStatus();
    // Refresh every 30 seconds
    const interval = setInterval(fetchSystemStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const toggleModel = async (modelId: string, currentlyActive: boolean) => {
    setActionLoading(modelId);
    try {
      const action = currentlyActive ? 'deactivate' : 'activate';
      const response = await fetch(`/api/models/${modelId}/${action}`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      await fetchSystemStatus(); // Refresh status
      onModelUpdate?.(); // Notify parent to refresh model data
    } catch (error) {
      console.error(`Error toggling model ${modelId}:`, error);
    } finally {
      setActionLoading(null);
    }
  };

  const triggerCycle = async () => {
    setActionLoading('cycle');
    try {
      const response = await fetch('/api/models/trigger-cycle', {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      await fetchSystemStatus(); // Refresh status
      onModelUpdate?.(); // Notify parent to refresh model data
    } catch (error) {
      console.error('Error triggering cycle:', error);
    } finally {
      setActionLoading(null);
    }
  };

  const setCycleInterval = async () => {
    setActionLoading('interval');
    try {
      const response = await fetch(`/api/models/cycle-interval?minutes=${newInterval}`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      await fetchSystemStatus(); // Refresh status
    } catch (error) {
      console.error('Error setting cycle interval:', error);
    } finally {
      setActionLoading(null);
    }
  };

  const formatTime = (isoString?: string) => {
    if (!isoString) return 'N/A';
    return new Date(isoString).toLocaleTimeString();
  };


  if (loading && !systemStatus) {
    return (
      <div className="model-controls-loading">
        <div className="spinner"></div>
        <span>Loading system status...</span>
      </div>
    );
  }

  return (
    <div className="model-controls">
      <div className="controls-header">
        <h3>Trading System Controls</h3>
        <div className="refresh-indicator">
          {loading && <div className="spinner small"></div>}
          <span>Last updated: {lastRefresh.toLocaleTimeString()}</span>
        </div>
      </div>

      {systemStatus && (
        <>
          {/* System Status Overview */}
          <div className="system-overview">
            <div className="overview-card">
              <div className="card-label">System Status</div>
              <div className={`card-value ${systemStatus.system_running ? 'running' : 'stopped'}`}>
                {systemStatus.system_running ? '🟢 Running' : '🔴 Stopped'}
              </div>
            </div>
            <div className="overview-card">
              <div className="card-label">Active Models</div>
              <div className="card-value">
                {systemStatus.active_agents} / {systemStatus.total_agents}
              </div>
            </div>
            <div className="overview-card">
              <div className="card-label">Cycle Interval</div>
              <div className="card-value">
                {systemStatus.cycle_interval_minutes} min
              </div>
            </div>
            <div className="overview-card">
              <div className="card-label">Total Actions</div>
              <div className="card-value">
                {systemStatus.total_actions}
              </div>
            </div>
          </div>

          {/* Timing Information */}
          <div className="timing-info">
            <div className="timing-item">
              <span className="timing-label">Last Cycle:</span>
              <span className="timing-value">{formatTime(systemStatus.last_cycle_time)}</span>
            </div>
            <div className="timing-item">
              <span className="timing-label">Next Cycle:</span>
              <span className="timing-value">{formatTime(systemStatus.next_cycle_time)}</span>
            </div>
          </div>

          {/* Execution Statistics */}
          <div className="execution-stats">
            <h4>Execution Statistics</h4>
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-label">Total Cycles</span>
                <span className="stat-value">{systemStatus.execution_stats.total_cycles}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Successful Cycles</span>
                <span className="stat-value positive">{systemStatus.execution_stats.successful_cycles}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Failed Cycles</span>
                <span className="stat-value negative">{systemStatus.execution_stats.failed_cycles}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Successful Stock</span>
                <span className="stat-value positive">{systemStatus.execution_stats.successful_stock_actions || 0}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Successful Polymarket</span>
                <span className="stat-value positive">{systemStatus.execution_stats.successful_polymarket_actions || 0}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Failed Stock</span>
                <span className="stat-value negative">{systemStatus.execution_stats.failed_stock_actions || 0}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Failed Polymarket</span>
                <span className="stat-value negative">{systemStatus.execution_stats.failed_polymarket_actions || 0}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Success Rate</span>
                <span className="stat-value">
                  {systemStatus.execution_stats.total_cycles > 0
                    ? ((systemStatus.execution_stats.successful_cycles / systemStatus.execution_stats.total_cycles) * 100).toFixed(1)
                    : 0}%
                </span>
              </div>
            </div>
          </div>

          {/* System Controls */}
          <div className="system-controls">
            <h4>System Controls</h4>

            {/* Manual Cycle Trigger */}
            <div className="control-group">
              <label>Manual Trading Cycle</label>
              <button
                onClick={triggerCycle}
                disabled={actionLoading === 'cycle'}
                className="control-button primary"
              >
                {actionLoading === 'cycle' ? 'Running...' : 'Trigger Cycle Now'}
              </button>
            </div>

            {/* Cycle Interval Control */}
            <div className="control-group">
              <label>Cycle Interval (minutes)</label>
              <div className="interval-control">
                <input
                  type="number"
                  min="1"
                  max="1440"
                  value={newInterval}
                  onChange={(e) => setNewInterval(parseInt(e.target.value))}
                  className="interval-input"
                />
                <button
                  onClick={setCycleInterval}
                  disabled={actionLoading === 'interval' || newInterval === systemStatus.cycle_interval_minutes}
                  className="control-button secondary"
                >
                  {actionLoading === 'interval' ? 'Setting...' : 'Update'}
                </button>
              </div>
            </div>
          </div>

          {/* Model Activation Controls */}
          <div className="model-activation">
            <h4>Model Activation</h4>
            <div className="models-list">
              {models.map(model => {
                const isActive = systemStatus.active_models[model.id] ?? true;
                return (
                  <div key={model.id} className="model-control-item">
                    <div className="model-info">
                      <span className="model-name">{model.name}</span>
                      <span className={`model-status ${isActive ? 'active' : 'inactive'}`}>
                        {isActive ? '🟢 Active' : '⚪ Inactive'}
                      </span>
                    </div>
                    <button
                      onClick={() => toggleModel(model.id, isActive)}
                      disabled={actionLoading === model.id}
                      className={`toggle-button ${isActive ? 'deactivate' : 'activate'}`}
                    >
                      {actionLoading === model.id ? 'Loading...' : (isActive ? 'Deactivate' : 'Activate')}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Trading Universe */}
          <div className="trading-universe">
            <h4>Trading Universe</h4>
            <div className="tickers-list">
              {systemStatus.tickers.map(ticker => (
                <span key={ticker} className="ticker-badge">{ticker}</span>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ModelControls;
