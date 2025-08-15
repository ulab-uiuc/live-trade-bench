import React, { useState, useEffect } from 'react';

interface SystemStatus {
  system_running: boolean;
  active_agents: number;
  total_agents: number;
  uptime_seconds: number;
  uptime_hours: number;
  cycle_interval_minutes: number;
  last_cycle_time?: string;
  next_cycle_time?: string;
}

const SystemMonitoring: React.FC = () => {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const fetchSystemStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/models/system-status');

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setSystemStatus(data);
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

  const formatUptime = (seconds: number): string => {
    // Handle invalid/NaN values
    if (!seconds || isNaN(seconds) || seconds < 0) {
      return 'Starting...';
    }

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (hours > 24) {
      const days = Math.floor(hours / 24);
      const remainingHours = hours % 24;
      return `${days}d ${remainingHours}h`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  };

  const formatTime = (isoString?: string): string => {
    if (!isoString) return 'N/A';
    // Convert to local timezone and format consistently
    return new Date(isoString).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false // Use 24-hour format for consistency
    });
  };

  if (loading && !systemStatus) {
    return (
      <div className="system-monitoring">
        <div className="monitoring-header">
          <h3>System Monitoring</h3>
          <div className="spinner small"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="system-monitoring">
      <div className="monitoring-header">
        <h3>System Monitoring</h3>
        <div className="refresh-indicator">
          {loading && <div className="spinner small"></div>}
          <span>Updated: {formatTime(lastRefresh.toISOString())}</span>
        </div>
      </div>

      {systemStatus && (
        <div className="monitoring-content">
          {/* System Status */}
          <div className="status-card">
            <div className="status-label">System Status</div>
            <div className={`status-value ${systemStatus.system_running ? 'running' : 'stopped'}`}>
              {systemStatus.system_running ? '🟢 Running' : '🔴 Stopped'}
            </div>
          </div>

          {/* Active Models */}
          <div className="status-card">
            <div className="status-label">Active Models</div>
            <div className="status-value">
              {systemStatus.active_agents} / {systemStatus.total_agents}
            </div>
          </div>

          {/* Uptime */}
          <div className="status-card">
            <div className="status-label">System Uptime</div>
            <div className="status-value">
              {formatUptime(systemStatus.uptime_seconds)}
            </div>
          </div>

          {/* Cycle Interval */}
          <div className="status-card">
            <div className="status-label">Cycle Interval</div>
            <div className="status-value">
              {systemStatus.cycle_interval_minutes} min
            </div>
          </div>

          {/* Last Cycle */}
          <div className="status-card">
            <div className="status-label">Last Cycle</div>
            <div className="status-value">
              {formatTime(systemStatus.last_cycle_time)}
            </div>
          </div>

          {/* Next Cycle */}
          <div className="status-card">
            <div className="status-label">Next Cycle</div>
            <div className="status-value">
              {formatTime(systemStatus.next_cycle_time)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemMonitoring;
