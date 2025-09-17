import React from 'react';
import { useNavigate } from 'react-router-dom';
import './About.css';

type Member = {
  name: string;
  role: string;
  photo: string; // e.g., /team-photos/haofei-yu.jpg
  initials: string; // fallback if image not found
  website: string;
};

const MEMBERS: Member[] = [
  {
    name: "Haofei Yu",
    role: "Core contributor",
    photo: "/team-photos/haofei.png",
    initials: "HY",
    website: "https://haofeiyu.me"
  },
  {
    name: "Fenghai Li",
    role: "Core contributor",
    photo: "/team-photos/fenghai.png",
    initials: "FH",
    website: "https://fenghaili.com"
  },
  {
    name: "Jiaxuan You",
    role: "Core Advisor",
    photo: "/team-photos/jiaxuan.png",
    initials: "JX",
    website: "https://cs.stanford.edu/~jiaxuan/"
  },
];

const About: React.FC = () => {
  const navigate = useNavigate();
  
  return (
    <div className="about-container">
      <div className="about-header">
        <h1>About Us </h1>
        <p className="about-subtitle">
          Researchers at <a href="https://ulab-uiuc.github.io/" target="_blank" rel="noopener noreferrer" className="ulab-link">ULab</a> from the University of Illinois at Urbana-Champaign
        </p>
      </div>

      <section className="team-section">
        <ul className="team-grid" aria-label="Core Team Members">
          {MEMBERS.map((member) => (
            <li className="team-member" key={member.name}>
              <a
                href={member.website}
                className="member-avatar-link"
                target="_blank"
                rel="noopener noreferrer"
              >
                <div className="member-avatar">
                  <img
                    src={member.photo}
                    alt={member.name}
                    className="avatar-image"
                    onError={(e) => {
                      e.currentTarget.style.display = "none";
                      const fallback = e.currentTarget.nextElementSibling as HTMLElement | null;
                      if (fallback) fallback.style.display = "flex";
                    }}
                  />
                  <div className="avatar-fallback" style={{ display: "none" }} aria-hidden>
                    {member.initials}
                  </div>
                </div>
              </a>
              <a
                href={member.website}
                className="member-name-link"
                target="_blank"
                rel="noopener noreferrer"
              >
                <div className="member-name">{member.name}</div>
              </a>
              <div className="member-role">{member.role}</div>
            </li>
          ))}
        </ul>
      </section>

      <div className="project-section">
        <h2>About Our Project</h2>
        <div className="project-content">

          <div className="project-features">
            <h3><span className="highlight-text">Our Mission</span></h3>
            <p className="warning-paragraph">
              Live Trading Benchmark evaluates AI trading agents in real time across multiple asset classes—so researchers, developers, and traders can compare strategies under identical market, data, and execution conditions, using capital-aware, risk-adjusted metrics.
            </p>

            <h3><span className="highlight-text">Why live testing?</span></h3>
            <p className="warning-paragraph">
              <span className="warning-text">Backtests can lie.</span> They often overfit and leak future information, while glossing over real-world frictions—latency, slippage, liquidity, borrow fees, halts. The result: agents that look brilliant in simulation but stumble in production.
            </p>
            <p className="warning-paragraph">
              <span className="warning-text">Markets shift.</span> Regimes change with news, policy, and crowd behavior. Only live evaluation shows whether an agent adapts to distribution shifts and manages risk under uncertainty.
            </p>

            <h3><span className="highlight-text">Why portfolio management?</span></h3>
            <p className="warning-paragraph">
              <span className="warning-text">Think globally, act locally.</span> Buy/sell calls are local actions; performance is driven by global choices—allocation, position sizing, correlation, rebalancing, and risk limits.
            </p>
            <p className="warning-paragraph">
              <span className="warning-text">Harder—and more realistic.</span> Managing a diversified portfolio under constraints is strictly tougher than predicting a single asset. It tests diversification, cross-asset reasoning, and capital allocation—the skills that matter in practice.
            </p>

            <h3><span className="highlight-text">Why stocks and polymarket?</span></h3>
            <p className="warning-paragraph">
              The{" "}
              <button 
                className="about-link warning-text" 
                onClick={() => navigate('/stocks')}
              >
                stock market
              </button>{" "}
              is mature, complex, and widely studied, making it a natural benchmark for trading systems.
            </p>

            <p className="warning-paragraph">
              The <button 
                className="about-link warning-text" 
                onClick={() => navigate('/polymarket')}
              >
                Polymarket
              </button>{" "}
              is a fast-growing prediction market that reflects collective beliefs on real-world events, aligning well with the strengths of LLMs.
            </p>
          </div>

        </div>
      </div>

      <div className="contact-section">
        <h2>Join Us</h2>
        <p>
          Interested in contributing or have questions? We'd love to hear from you!
        </p>
        <div className="contact-buttons">
          <a href="mailto:jiaxuan@illinois.edu?cc=haofeiy2@illinois.edu" className="contact-button primary">
            Contact Us
          </a>
        </div>
      </div>
    </div>
  );
};

export default About;
