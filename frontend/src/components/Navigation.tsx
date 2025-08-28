import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const Navigation: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <nav className="navigation">
      <div className="navigation-container">
        <div className="nav-logo">
          Live Trade Bench
        </div>
        <div className="nav-links">
          <button
            className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
            onClick={() => navigate('/')}
          >
            Overview
          </button>
          <button
            className={`nav-link ${location.pathname === '/stocks' ? 'active' : ''}`}
            onClick={() => navigate('/stocks')}
          >
            Stocks
          </button>
          <button
            className={`nav-link ${location.pathname === '/polymarket' ? 'active' : ''}`}
            onClick={() => navigate('/polymarket')}
          >
            Polymarket
          </button>
          <button
            className={`nav-link ${location.pathname === '/news' ? 'active' : ''}`}
            onClick={() => navigate('/news')}
          >
            News
          </button>
          <button
            className={`nav-link ${location.pathname === '/social' ? 'active' : ''}`}
            onClick={() => navigate('/social')}
          >
            Social Media
          </button>
          <button
            className={`nav-link ${location.pathname === '/trading-history' ? 'active' : ''}`}
            onClick={() => navigate('/trading-history')}
          >
            Trading History
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
