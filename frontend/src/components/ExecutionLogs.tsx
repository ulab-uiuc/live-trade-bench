import React, { useState, useEffect } from 'react';

interface ExecutionLog {
  timestamp: string;
  event_type: string;
  data: {
    [key: string]: any;
  };
}

interface ExecutionLogsResponse {
  logs: ExecutionLog[];
  total_logs: number;
  filter_applied: boolean;
  event_type?: string;
}

interface SystemMetrics {
  system_performance: {
    total_portfolio_value: number;
    total_initial_value: number;
    system_return_pct: number;
    uptime_seconds: number;
    uptime_hours: number;
  };
  execution_stats: {
    total_cycles: number;
    successful_cycles: number;
    failed_cycles: number;
    total_actions: number;
    successful_actions: number;
    failed_actions: number;
  };
  active_models_count: number;
  total_models_count: number;
  recent_logs_count: number;
  avg_cycle_duration: number;
  success_rate: {
    cycles: number;
    actions: number;
  };
}

const ExecutionLogs: React.FC = () => {
  const [logs, setLogs] = useState<ExecutionLog[]>([]);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedEventType, setSelectedEventType] = useState<string>('');
  const [limit, setLimit] = useState<number>(50);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
        ...(selectedEventType && { event_type: selectedEventType })
      });

      const response = await fetch(`http://localhost:5000/api/models/execution-logs?${params}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ExecutionLogsResponse = await response.json();
      setLogs(data.logs);
      setLastRefresh(new Date());
    } catch (error) {
      console.error('Error fetching execution logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMetrics = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/models/system-metrics');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: SystemMetrics = await response.json();
      setMetrics(data);
    } catch (error) {
      console.error('Error fetching system metrics:', error);
    }
  };

  useEffect(() => {
    fetchLogs();
    fetchMetrics();

    // Refresh every 30 seconds
    const interval = setInterval(() => {
      fetchLogs();
      fetchMetrics();
    }, 30000);

    return () => clearInterval(interval);
  }, [selectedEventType, limit]);

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
  };

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const getEventTypeColor = (eventType: string) => {
    switch (eventType) {
      case 'cycle_completed': return '#28a745';
      case 'cycle_failed': return '#dc3545';
      case 'model_activated': return '#007bff';
      case 'model_deactivated': return '#6c757d';
      default: return '#17a2b8';
    }
  };

  const getEventTypeIcon = (eventType: string) => {
    switch (eventType) {
      case 'cycle_completed': return '✅';
      case 'cycle_failed': return '❌';
      case 'model_activated': return '🟢';
      case 'model_deactivated': return '⚪';
      default: return '📝';
    }
  };

  return (
    <div className="execution-logs">
      <div className="logs-header">
        <h3>System Monitoring</h3>
        <div className="refresh-indicator">
          {loading && <div className="spinner small"></div>}
          <span>Last updated: {lastRefresh.toLocaleTimeString()}</span>
        </div>
      </div>

      {/* System Metrics Summary */}
      {metrics && (
        <div className="metrics-summary">
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-label">System Performance</div>
              <div className={`metric-value ${metrics.system_performance.system_return_pct >= 0 ? 'positive' : 'negative'}`}>
                {metrics.system_performance.system_return_pct >= 0 ? '+' : ''}{(metrics.system_performance.system_return_pct ?? 0).toFixed(2)}%
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Total Portfolio Value</div>
              <div className="metric-value">
                ${(metrics.system_performance.total_portfolio_value ?? 0).toFixed(2)}
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Uptime</div>
              <div className="metric-value">
                {formatUptime(metrics.system_performance.uptime_seconds ?? 0)}
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Active Models</div>
              <div className="metric-value">
                {metrics.active_models_count ?? 0} / {metrics.total_models_count ?? 0}
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Cycle Success Rate</div>
              <div className="metric-value">
                {(metrics.success_rate.cycles ?? 0).toFixed(1)}%
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Action Success Rate</div>
              <div className="metric-value">
                {metrics.success_rate.actions ? metrics.success_rate.actions.toFixed(1) : '0.0'}%
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Avg Cycle Duration</div>
              <div className="metric-value">
                {metrics.avg_cycle_duration ? metrics.avg_cycle_duration.toFixed(1) : '0.0'}s
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Total Actions</div>
              <div className="metric-value">
                {metrics.execution_stats.total_actions ?? 0}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Log Filters */}
      <div className="log-filters">
        <div className="filter-group">
          <label>Event Type:</label>
          <select
            value={selectedEventType}
            onChange={(e) => setSelectedEventType(e.target.value)}
            className="filter-select"
          >
            <option value="">All Events</option>
            <option value="cycle_completed">Cycle Completed</option>
            <option value="cycle_failed">Cycle Failed</option>
            <option value="model_activated">Model Activated</option>
            <option value="model_deactivated">Model Deactivated</option>
          </select>
        </div>
        <div className="filter-group">
          <label>Limit:</label>
          <select
            value={limit}
            onChange={(e) => setLimit(parseInt(e.target.value))}
            className="filter-select"
          >
            <option value={25}>25 entries</option>
            <option value={50}>50 entries</option>
            <option value={100}>100 entries</option>
            <option value={200}>200 entries</option>
          </select>
        </div>
        <button onClick={fetchLogs} className="refresh-button">
          Refresh
        </button>
      </div>

      {/* Execution Logs */}
      <div className="logs-container">
        <h4>Execution Logs ({logs.length} entries)</h4>
        {logs.length === 0 ? (
          <div className="no-logs">
            <span>No execution logs available</span>
          </div>
        ) : (
          <div className="logs-list">
            {logs.map((log, index) => (
              <div key={index} className="log-entry">
                <div className="log-header">
                  <span className="log-icon">
                    {getEventTypeIcon(log.event_type)}
                  </span>
                  <span
                    className="log-event-type"
                    style={{ color: getEventTypeColor(log.event_type) }}
                  >
                    {log.event_type.replace('_', ' ')}
                  </span>
                  <span className="log-timestamp">
                    {formatTimestamp(log.timestamp)}
                  </span>
                </div>
                <div className="log-data">
                  {Object.entries(log.data).map(([key, value]) => (
                    <div key={key} className="log-data-item">
                      <span className="data-key">{key}:</span>
                      <span className="data-value">
                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ExecutionLogs;
