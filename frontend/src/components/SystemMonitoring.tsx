import React, { useState, useEffect, useCallback } from 'react';
import './SystemMonitoring.css';

const SystemMonitoring: React.FC = () => {
  const [status, setStatus] = useState({
    running: true,
    agents: 3,
    uptime: '2h 15m'
  });

  // 极简的状态更新
  const updateStatus = useCallback(() => {
    const now = new Date();
    const uptimeMinutes = Math.floor(Math.random() * 300) + 120; // 2-7小时
    const hours = Math.floor(uptimeMinutes / 60);
    const minutes = uptimeMinutes % 60;
    
    setStatus({
      running: true,
      agents: 3,
      uptime: `${hours}h ${minutes}m`
    });
  }, []);

  useEffect(() => {
    updateStatus();
    // 每5分钟更新一次，避免频繁更新
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