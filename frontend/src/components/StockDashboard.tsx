import React, { useMemo } from 'react';
import ModelsDisplay from './ModelsDisplay';
import './Dashboard.css';
import { Model } from '../types';

interface StockDashboardProps {
  modelsData: Model[];
  modelsLastRefresh: Date;
  isLoading: boolean;
}

const StockDashboard: React.FC<StockDashboardProps> = ({ modelsData, modelsLastRefresh, isLoading }) => {
  const stockModels = useMemo(() =>
    modelsData.filter(m => m.category === 'stock'),
    [modelsData]
  );

  if (isLoading) {
    return <div className="loading-indicator">Loading...</div>;
  }

  return (
    <div className="dashboard-ultra-simple">
      <div style={{
        textAlign: 'center',
        padding: '2rem 0'
      }}>
        <h1 style={{
          color: '#ffffff',
          fontSize: '2.5rem',
          margin: '0 0 0.5rem 0',
          fontWeight: '700',
          display: 'block',
          visibility: 'visible',
          opacity: 1,
          position: 'relative',
          zIndex: 1000
        }}>
          📈 Stock Models
        </h1>
        <p style={{
          color: '#ffffff',
          fontSize: '1rem',
          margin: 0,
          fontWeight: '500',
          display: 'block',
          visibility: 'visible',
          opacity: 1,
          position: 'relative',
          zIndex: 1000
        }}>
          AI-powered stock portfolio management
        </p>
      </div>

      {/*  -  */}
      <ModelsDisplay
        modelsData={stockModels}
        stockModels={stockModels}
        polymarketModels={[]}
        onRefresh={undefined}
      />


    </div>
  );
};

export default StockDashboard;
