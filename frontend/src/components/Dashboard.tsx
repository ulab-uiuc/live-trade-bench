import React, { useState, useEffect } from 'react';
import ModelsDisplay from './ModelsDisplay';
import TradingHistory from './TradingHistory';

const Dashboard: React.FC = () => {
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  useEffect(() => {
    const interval = setInterval(() => {
      setLastRefresh(new Date());
    }, 24 * 60 * 60 * 1000); // Refresh every 24 hours (daily)

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="dashboard">
      <div className="models-section">
        <ModelsDisplay lastRefresh={lastRefresh} />
      </div>
      <div className="trading-history-section">
        <TradingHistory lastRefresh={lastRefresh} />
      </div>
    </div>
  );
};

export default Dashboard;