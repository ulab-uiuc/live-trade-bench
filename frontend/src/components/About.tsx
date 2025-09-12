import React from 'react';
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
            <p>
              Live Trading Benchmark evaluates AI trading agents in real time across multiple asset classes—so researchers, developers, and traders can compare strategies under identical market, data, and execution conditions, using capital-aware, risk-adjusted metrics.
            </p>

            <h3><span className="highlight-text">Why live testing?</span></h3>
            <p>
              <strong>Backtests can lie.</strong> They often overfit and leak future information, while glossing over real-world frictions—latency, slippage, liquidity, borrow fees, halts. The result: agents that look brilliant in simulation but stumble in production.
            </p>
            <p>
              <strong>Markets shift.</strong> Regimes change with news, policy, and crowd behavior. Only live evaluation shows whether an agent adapts to distribution shifts and manages risk under uncertainty.
            </p>

            <h3><span className="highlight-text">Why portfolio management?</span></h3>
            <p>
              <strong>Think globally, act locally.</strong> Buy/sell calls are local actions; performance is driven by global choices—allocation, position sizing, correlation, rebalancing, and risk limits.
            </p>
            <p>
              <strong>Harder—and more realistic.</strong> Managing a diversified portfolio under constraints is strictly tougher than predicting a single asset. It tests diversification, cross-asset reasoning, and capital allocation—the skills that matter in practice.
            </p>
          </div>

        </div>
      </div>

      <div className="contact-section">
        <h2>Get Involved</h2>
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
