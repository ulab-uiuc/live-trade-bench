import React, { useState, useEffect } from 'react';
import ModelsDisplay from './ModelsDisplay';
import SystemLog from './SystemLog';

interface Model {
  id: string;
  name: string;
  category: 'polymarket' | 'stock' | 'option';
  performance: number;
  accuracy: number;
  trades: number;
  profit: number;
  status: 'active' | 'inactive' | 'training';
  market_type?: string;
  ticker?: string;
  strategy?: string;
}

interface DashboardProps {
  modelsData: Model[];
  setModelsData: (models: Model[]) => void;
  modelsLastRefresh: Date;
  setModelsLastRefresh: (date: Date) => void;
}

const Dashboard: React.FC<DashboardProps> = ({
  modelsData,
  setModelsData,
  modelsLastRefresh,
  setModelsLastRefresh
}) => {
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
        <ModelsDisplay
          modelsData={modelsData}
          setModelsData={setModelsData}
          lastRefresh={modelsLastRefresh}
          setLastRefresh={setModelsLastRefresh}
        />
      </div>
      <div className="system-log-section">
        <SystemLog lastRefresh={lastRefresh} />
      </div>
    </div>
  );
};

export default Dashboard;
