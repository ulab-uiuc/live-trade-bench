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
    <div className="theme-polymarket">
      <div style={{
        textAlign: 'center',
        padding: '2rem 0'
      }}>
        <h1 style={{
          color: '#06b6d4',
          fontSize: '3.5rem',
          fontWeight: '800',
          margin: '0 0 0.5rem 0',
          display: 'block',
          visibility: 'visible',
          opacity: 1,
          position: 'relative',
          zIndex: 1000
        }}>
          Polymarket Models
        </h1>
        <p style={{
          color: 'rgba(255, 255, 255, 0.7)',
          fontSize: '1.2rem',
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
