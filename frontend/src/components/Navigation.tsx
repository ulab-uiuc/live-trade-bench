import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const Navigation: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <nav className="navigation">
      <button 
        className={location.pathname === '/' ? 'active' : ''}
        onClick={() => navigate('/')}
      >
        Dashboard
      </button>
      <button 
        className={location.pathname === '/news' ? 'active' : ''}
        onClick={() => navigate('/news')}
      >
        News
      </button>
    </nav>
  );
};

export default Navigation;