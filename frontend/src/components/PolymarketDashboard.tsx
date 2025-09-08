import React, { useMemo } from 'react';
import ModelsDisplay from './ModelsDisplay';
import './Dashboard.css';
import { Model } from '../types';

interface PolymarketDashboardProps {
  modelsData: Model[];
  modelsLastRefresh: Date;
  isLoading: boolean;
}

const PolymarketDashboard: React.FC<PolymarketDashboardProps> = ({ modelsData, modelsLastRefresh, isLoading }) => {
  const polymarketModels = useMemo(() =>
    modelsData.filter(m => m.category === 'polymarket'),
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
          🎯 Polymarket Models
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
          AI-powered prediction market portfolio management
        </p>
      </div>

      {/* Polymarket */}
      <ModelsDisplay
        modelsData={polymarketModels}
        stockModels={[]}
        polymarketModels={polymarketModels}
        onRefresh={undefined}
      />


    </div>
  );
};

export default PolymarketDashboard;
