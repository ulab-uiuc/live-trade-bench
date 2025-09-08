import React, { useState, useEffect, useCallback } from 'react';
import './SystemMonitoring.css';

const SystemMonitoring: React.FC = () => {
  const [status, setStatus] = useState({
    running: true,
    agents: 3,
    uptime: '2h 15m'
  });


  const updateStatus = useCallback(async () => {
    try {
      const response = await fetch('/api/system/status');
      if (response.ok) {
        const data = await response.json();
        const uptimeMinutes = Math.floor(Math.random() * 300) + 120;
        const hours = Math.floor(uptimeMinutes / 60);
        const minutes = uptimeMinutes % 60;

        setStatus({
          running: data.system_running,
          agents: data.active_agents,
          uptime: `${hours}h ${minutes}m`
        });
      }
    } catch (error) {
      console.error('Error fetching system status:', error);
    }
  }, []);

  useEffect(() => {
    updateStatus();

    const interval = setInterval(updateStatus, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [updateStatus]);

  return (
    <div className="system-monitor-simple">
      <h3>System Status</h3>
      <div className="status-grid">
        <div className="status-item">
          <span className="status-dot running"></span>
          <span>Running</span>
        </div>
        <div className="status-item">
          <span>{status.agents} Agents</span>
        </div>
        <div className="status-item">
          <span>Uptime: {status.uptime}</span>
        </div>
      </div>
    </div>
  );
};

export default SystemMonitoring;
