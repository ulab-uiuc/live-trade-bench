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
            className={`nav-link ${location.pathname === '/bitmex' ? 'active' : ''}`}
            onClick={() => navigate('/bitmex')}
          >
            BitMEX
          </button>
          <button
            className={`nav-link ${location.pathname === '/forex' ? 'active' : ''}`}
            onClick={() => navigate('/forex')}
          >
            Forex
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
          <a
            href="https://arxiv.org/abs/2511.03628"
            target="_blank"
            rel="noopener noreferrer"
            className="nav-link report-link"
          >
            Report
          </a>
        </div>

        {/* Right Side Links */}
        <div className="nav-right-links desktop-nav">
          <a
            href="https://github.com/ulab-uiuc/live-trade-bench"
            target="_blank"
            rel="noopener noreferrer"
            className="icon-link github-link"
            title="View on GitHub"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
          </a>
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
            className={`mobile-nav-link ${location.pathname === '/bitmex' ? 'active' : ''}`}
            onClick={() => navigateAndCloseMobile('/bitmex')}
          >
            BitMEX
          </button>
          <button
            className={`mobile-nav-link ${location.pathname === '/forex' ? 'active' : ''}`}
            onClick={() => navigateAndCloseMobile('/forex')}
          >
            Forex
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

          {/* Mobile External Links */}
          <div className="mobile-external-links">
            <a
              href="https://arxiv.org/abs/2511.03628"
              target="_blank"
              rel="noopener noreferrer"
              className="mobile-external-link"
            >
              Report
            </a>
            <a
              href="https://github.com/ulab-uiuc/live-trade-bench"
              target="_blank"
              rel="noopener noreferrer"
              className="mobile-external-link"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              <span>GitHub</span>
            </a>
          </div>
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
