import React, { useMemo } from 'react';
import ModelsDisplay from './ModelsDisplay';
import './Dashboard.css';
import { Model } from '../types';

interface BitMEXDashboardProps {
  modelsData: Model[];
  modelsLastRefresh: Date;
  isLoading: boolean;
}

const BitMEXDashboard: React.FC<BitMEXDashboardProps> = ({ modelsData, modelsLastRefresh, isLoading }) => {
  const bitmexModels = useMemo(() =>
    modelsData.filter(m => m.category === 'bitmex' || m.category === 'bitmex-benchmark'),
    [modelsData]
  );

  if (isLoading) {
    return <div className="loading-indicator">Loading...</div>;
  }

  return (
    <div className="theme-bitmex">
      <div style={{
        textAlign: 'center',
        padding: '2rem 0'
      }}>
        <h1 style={{
          color: '#10b981',
          fontSize: '3.5rem',
          fontWeight: '800',
          margin: '0 0 0.5rem 0',
          display: 'block',
          visibility: 'visible',
          opacity: 1,
          position: 'relative',
          zIndex: 1000
        }}>
          BitMEX Models
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
          AI-powered cryptocurrency perpetual contract trading
        </p>

        <div style={{
          maxWidth: '1000px',
          margin: '1.5rem auto 0',
          padding: '1rem 1.5rem',
          background: 'rgba(16, 185, 129, 0.1)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          borderRadius: '12px',
          color: 'rgba(255, 255, 255, 0.8)',
          fontSize: '0.95rem',
          lineHeight: '1.6',
          textAlign: 'left'
        }}>
          We display real-time performance metrics for each AI trading agent managing cryptocurrency perpetual contracts on BitMEX. Trading occurs 24/7 across 12-15 major crypto assets including Bitcoin (XBTUSD), Ethereum (ETHUSD), and other top cryptocurrencies. Agents consider funding rates, order book depth, and crypto-specific market dynamics. Click any model card to explore detailed portfolio analysis, allocation history, profit trends, and LLM decision-making insights.
        </div>
      </div>

      <ModelsDisplay
        modelsData={bitmexModels}
        stockModels={[]}
        polymarketModels={[]}
        onRefresh={undefined}
      />
    </div>
  );
};

export default BitMEXDashboard;
