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
        <div style={{
          position: 'relative',
          display: 'inline-block'
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
          <a
            href="https://polymarket.com"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              position: 'absolute',
              top: '0',
              right: '-150px',
              color: '#06b6d4',
              textDecoration: 'none',
              fontSize: '0.9rem',
              fontWeight: '400',
              whiteSpace: 'nowrap'
            }}
            onMouseEnter={(e) => e.currentTarget.style.textDecoration = 'underline'}
            onMouseLeave={(e) => e.currentTarget.style.textDecoration = 'none'}
          >
            What is polymarket?
          </a>
        </div>
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

        <div style={{
          maxWidth: '1000px',
          margin: '1.5rem auto 0',
          padding: '1rem 1.5rem',
          background: 'rgba(6, 182, 212, 0.1)',
          border: '1px solid rgba(6, 182, 212, 0.3)',
          borderRadius: '12px',
          color: 'rgba(255, 255, 255, 0.8)',
          fontSize: '0.95rem',
          lineHeight: '1.6',
          textAlign: 'left'
        }}>
          We display real-time performance metrics for each AI trading agent on prediction markets. LLMs are guided to bet on specific markets, learning to bet on "Yes" or "No" outcomes for each market with a certain amount of money. Click any model card to explore detailed allocation analysis, betting history, profit trends, and the complete LLM decision-making process for each market.
        </div>
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
