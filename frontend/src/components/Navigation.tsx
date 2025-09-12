import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const Navigation: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

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
          <div className="live-badge">
            <div className="live-indicator"></div>
            LIVE
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
