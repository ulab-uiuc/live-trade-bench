import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const Navigation: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [views, setViews] = useState<number>(0);

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1).replace('.0', '') + 'M';
    } else {
      return num.toLocaleString();
    }
  };

  useEffect(() => {
    const fetchViews = async () => {
      try {
        const baseUrl = process.env.NODE_ENV === 'production' ? '' : 'http://localhost:5001';

        const response = await fetch(`${baseUrl}/api/views`);
        if (response.ok) {
          const data = await response.json();
          setViews(data.views);
        }

        await fetch(`${baseUrl}/api/views`, { method: 'POST' });

        const updatedResponse = await fetch(`${baseUrl}/api/views`);
        if (updatedResponse.ok) {
          const updatedData = await updatedResponse.json();
          setViews(updatedData.views);
        }
      } catch (error) {
        console.error('Failed to fetch views:', error);
      }
    };

    fetchViews();
  }, []);

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const navigateAndCloseMobile = (path: string) => {
    navigate(path);
    setIsMobileMenuOpen(false);
  };

  return (
    <nav className="navigation">
      <div className="navigation-container">
        {/* Logo Section */}
        <div className="nav-logo">
          <div className="views-badge">
            <div className="views-indicator"></div>
            Views: {formatNumber(views)}
          </div>
          <button
            className="brand-button"
            onClick={() => navigateAndCloseMobile('/')}
          >
            Trading Benchmark
          </button>
        </div>

        {/* Desktop Navigation Links */}
        <div className="nav-links desktop-nav">
          <button
            className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
            onClick={() => navigate('/')}
          >
            Leaderboard
          </button>
          <button
            className={`nav-link ${location.pathname === '/stocks' ? 'active' : ''}`}
            onClick={() => navigate('/stocks')}
          >
            Stock
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
            className={`nav-link ${location.pathname === '/about' ? 'active' : ''}`}
            onClick={() => navigate('/about')}
          >
            About
          </button>
        </div>

        {/* Mobile Hamburger Button */}
        <button
          className="mobile-menu-toggle"
          onClick={toggleMobileMenu}
          aria-label="Toggle mobile menu"
        >
          <div className={`hamburger ${isMobileMenuOpen ? 'open' : ''}`}>
            <span></span>
            <span></span>
            <span></span>
          </div>
        </button>
      </div>

      {/* Mobile Navigation Menu */}
      <div className={`mobile-nav ${isMobileMenuOpen ? 'open' : ''}`}>
        {/* Mobile Menu Header with Close Button */}
        <div className="mobile-nav-header">
          <button
            className="mobile-nav-close"
            onClick={() => setIsMobileMenuOpen(false)}
            aria-label="Close menu"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <div className="mobile-nav-links">
          <button
            className={`mobile-nav-link ${location.pathname === '/' ? 'active' : ''}`}
            onClick={() => navigateAndCloseMobile('/')}
          >
            Leaderboard
          </button>
          <button
            className={`mobile-nav-link ${location.pathname === '/stocks' ? 'active' : ''}`}
            onClick={() => navigateAndCloseMobile('/stocks')}
          >
            Stock
          </button>
          <button
            className={`mobile-nav-link ${location.pathname === '/polymarket' ? 'active' : ''}`}
            onClick={() => navigateAndCloseMobile('/polymarket')}
          >
            Polymarket
          </button>
          <button
            className={`mobile-nav-link ${location.pathname === '/news' ? 'active' : ''}`}
            onClick={() => navigateAndCloseMobile('/news')}
          >
            News
          </button>
          <button
            className={`mobile-nav-link ${location.pathname === '/social' ? 'active' : ''}`}
            onClick={() => navigateAndCloseMobile('/social')}
          >
            Social Media
          </button>

          <button
            className={`mobile-nav-link ${location.pathname === '/about' ? 'active' : ''}`}
            onClick={() => navigateAndCloseMobile('/about')}
          >
            About Us
          </button>
        </div>
      </div>

      {/* Mobile Menu Backdrop */}
      {isMobileMenuOpen && (
        <div
          className="mobile-menu-backdrop"
          onClick={() => setIsMobileMenuOpen(false)}
        ></div>
      )}
    </nav>
  );
};

export default Navigation;
