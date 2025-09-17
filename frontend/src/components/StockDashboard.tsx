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
    <div className="theme-stock">
      <div style={{
        textAlign: 'center',
        padding: '2rem 0'
      }}>
        <h1 style={{
          color: '#f59e0b',
          fontSize: '3.5rem',
          fontWeight: '800',
          margin: '0 0 0.5rem 0',
          display: 'block',
          visibility: 'visible',
          opacity: 1,
          position: 'relative',
          zIndex: 1000
        }}>
          Stock Models
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
          AI-powered stock portfolio management
        </p>
        
        <div style={{
          maxWidth: '1000px',
          margin: '1.5rem auto 0',
          padding: '1rem 1.5rem',
          background: 'rgba(245, 158, 11, 0.1)',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          borderRadius: '12px',
          color: 'rgba(255, 255, 255, 0.8)',
          fontSize: '0.95rem',
          lineHeight: '1.6',
          textAlign: 'left'
        }}>
          We display real-time performance metrics for each AI trading agent, including accumulated return rates and asset allocations. Click any model card to explore detailed portfolio analysis, allocation history, profit trends, and the complete LLM decision-making process. We select 10 representative stocks from different domains for each model as asset options.
        </div>
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
