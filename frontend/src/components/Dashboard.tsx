import React, { useState } from "react";
import "./Dashboard.css";

// ------- Types -------
export type ModelRow = {
  id: string | number;
  name: string;
  provider?: string; // e.g., OpenAI, Google, Anthropic
  score: number; // higher is better
  votes?: number;
  logoUrl?: string; // optional small logo
};

export type DashboardProps = {
  modelsData?: any[]; // raw input from your backend
  modelsLastRefresh?: Date | string;
  systemStatus?: any;
  systemLastRefresh?: Date | string;
};

// ------- Helpers -------
function relativeTime(dateLike?: Date | string) {
  if (!dateLike) return "";
  const date = typeof dateLike === "string" ? new Date(dateLike) : dateLike;
  const diffMs = Date.now() - date.getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min${mins === 1 ? "" : "s"} ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} hour${hrs === 1 ? "" : "s"} ago`;
  const days = Math.floor(hrs / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}

// Utility function for conditional class names (keeping for potential future use)
// function clsx(...xs: Array<string | false | null | undefined>) {
//   return xs.filter(Boolean).join(" ");
// }

function normalize(raw: any): ModelRow {
  // Map backend model data to UI format
  // Performance/profit is likely stored as a decimal (e.g., 0.05 = 5%)
  let score = 0;
  if (typeof raw?.performance === "number") {
    score = raw.performance;
  } else if (typeof raw?.currentProfit === "number") {
    // Convert profit to percentage
    score = raw.currentProfit * 100;
  } else if (typeof raw?.profit === "number") {
    score = raw.profit * 100;
  } else if (typeof raw?.score === "number") {
    score = raw.score;
  }

  // Count trades/allocations
  const trades = raw?.allocationHistory?.length ||
    raw?.trades ||
    raw?.votes ||
    raw?.popularity ||
    0;

  return {
    id: raw?.id ?? raw?.name ?? Math.random().toString(36).slice(2),
    name: raw?.name ?? raw?.model ?? "Unknown Model",
    provider: extractProvider(raw?.name),
    score: Number(score.toFixed(2)),
    votes: trades,
    logoUrl: raw?.logoUrl,
  } as ModelRow;
}

function extractProvider(name?: string): string {
  if (!name) return "Unknown";
  const n = name.toLowerCase();
  if (n.includes("gpt") || n.includes("openai")) return "OpenAI";
  if (n.includes("claude") || n.includes("anthropic")) return "Anthropic";
  if (n.includes("gemini") || n.includes("google")) return "Google";
  if (n.includes("llama") || n.includes("meta")) return "Meta";
  if (n.includes("qwen")) return "Qwen";
  if (n.includes("deepseek")) return "DeepSeek";
  if (n.includes("grok")) return "xAI";
  return "Other";
}

// ------- Provider Icon -------
const ProviderIcon: React.FC<{ name?: string; provider?: string }> = ({ name, provider }) => {
  const getProviderIcon = (provider?: string, name?: string) => {
    const p = provider?.toLowerCase() || "";
    const n = name?.toLowerCase() || "";

    if (p.includes("openai") || p.includes("gpt") || n.includes("gpt")) {
      return "./openai.png";
    }
    if (p.includes("anthropic") || p.includes("claude") || n.includes("claude")) {
      return `${process.env.PUBLIC_URL}/claude.png`;
    }
    if (p.includes("google") || p.includes("gemini") || n.includes("gemini")) {
      return "./google.png";
    }
    if (p.includes("meta") || p.includes("llama") || n.includes("llama")) {
      return "./meta.png";
    }
    if (p.includes("qwen") || n.includes("qwen") || p.includes("kimi") || n.includes("kimi")) {
      return "./kimi.png";
    }
    if (p.includes("deepseek") || n.includes("deepseek")) {
      return "./deepseek.png";
    }
    if (p.includes("xai") || p.includes("grok") || n.includes("grok")) {
      return "❌"; // Keep emoji for xAI as no PNG available
    }
    return "⚡"; // Default emoji
  };

  const getProviderClass = (provider?: string, name?: string) => {
    const p = provider?.toLowerCase() || "";
    const n = name?.toLowerCase() || "";
    if (p.includes("openai") || p.includes("gpt") || n.includes("gpt")) return "openai";
    if (p.includes("anthropic") || p.includes("claude") || n.includes("claude")) return "anthropic";
    if (p.includes("google") || p.includes("gemini") || n.includes("gemini")) return "google";
    if (p.includes("meta") || p.includes("llama") || n.includes("llama")) return "meta";
    if (p.includes("qwen") || n.includes("qwen") || p.includes("kimi") || n.includes("kimi")) return "kimi";
    if (p.includes("deepseek") || n.includes("deepseek")) return "deepseek";
    return "other";
  };

  const icon = getProviderIcon(provider, name);
  const cls = getProviderClass(provider, name);
  const isPng = icon.endsWith('.png');

  return (
    <div className={`model-avatar ${cls}`} title={provider || name}>
      {isPng ? (
        <img
          src={icon}
          alt={provider || name}
          style={{ width: '18px', height: '18px', objectFit: 'contain' }}
          onError={(e) => {
            console.log('Failed to load image:', icon, 'for provider:', provider, 'name:', name);
            // Fallback to emoji if image fails to load
            e.currentTarget.style.display = 'none';
            e.currentTarget.parentElement!.innerHTML = '<span style="line-height: 1; display: block;">⚡</span>';
          }}
        />
      ) : (
        <span style={{ lineHeight: 1, display: 'block' }}>{icon}</span>
      )}
    </div>
  );
};

// ------- Modern Leaderboard Card -------
const LeaderboardCard: React.FC<{
  title: string;
  updatedAt?: Date | string;
  items: ModelRow[];
  category: "stock" | "polymarket";
}> = ({ title, updatedAt, items, category }) => {
  const [showAll, setShowAll] = useState(false);

  // Sort by score desc, compute rank
  const sortedItemsWithRank = [...items]
    .sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
    .map((x, i) => ({ ...x, rank: i + 1 }));

  const rows = showAll ? sortedItemsWithRank : sortedItemsWithRank.slice(0, 10);

  const getScoreClass = (score: number) => {
    if (score > 0) return "positive";
    if (score < 0) return "negative";
    return "neutral";
  };

  const getRankDisplay = (rank: number) => {
    return rank.toString();
  };

  return (
    <div className={`leaderboard-card ${category}`}>
      {/* Header */}
      <div className="card-header">
        <div className="card-title-section">
          <h3 className="card-title">{title}</h3>
        </div>
        <div className="card-updated">{relativeTime(updatedAt)}</div>
      </div>

      {/* Desktop Table */}
      <div className="leaderboard-table">
        {/* Header */}
        <div className="table-header">
          <div>Rank</div>
          <div>Model</div>
          <div>Return</div>
          <div>#Trades</div>
        </div>

        {/* Rows */}
        {rows.map((row) => (
          <div key={row.id} className="table-row">
            {/* Rank */}
            <div className={`rank-cell ${row.rank <= 3 ? `top-3 rank-${row.rank}` : ''}`}>
              {getRankDisplay(row.rank)}
            </div>

            {/* Model */}
            <div className="model-cell">
              <ProviderIcon name={row.name} provider={row.provider} />
              <div className="model-name">{row.name}</div>
            </div>

            {/* Score/Performance */}
            <div className={`score-cell ${getScoreClass(row.score)}`}>
              {row.score > 0 ? '+' : ''}{row.score.toFixed(1)}%
            </div>

            {/* Votes/Trades */}
            <div className="votes-cell">
              {row.votes}
            </div>
          </div>
        ))}
      </div>


      {/* Footer */}
      {items.length > 10 && (
        <div className="card-footer">
          <button
            className="view-all-btn"
            onClick={() => setShowAll(!showAll)}
          >
            {showAll ? 'Show Less' : `View All Models (${items.length})`}
          </button>
        </div>
      )}
    </div>
  );
};

// ------- Main Dashboard Component -------

const TwoPanelLeaderboard: React.FC<DashboardProps> = ({ modelsData = [], modelsLastRefresh = new Date(), systemStatus, systemLastRefresh }) => {
  const stock = modelsData.filter((m) => (m?.category ?? "").toString().toLowerCase() === "stock").map(normalize);
  const poly = modelsData
    .filter((m) => (m?.category ?? "").toString().toLowerCase().includes("poly"))
    .map(normalize);

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1 className="dashboard-title">
          Live Trading Benchmark
        </h1>
        <p className="dashboard-subtitle">
          Real-time leaderboard for LLM-powered portfolio management
        </p>
      </div>

      <div className="leaderboard-grid">
        <LeaderboardCard
          key="stock-leaderboard"
          title="Stock Market"
          updatedAt={modelsLastRefresh}
          items={stock}
          category="stock"
        />
        <LeaderboardCard
          key="polymarket-leaderboard"
          title="Polymarket"
          updatedAt={modelsLastRefresh}
          items={poly}
          category="polymarket"
        />
      </div>
    </div>
  );
};

export default TwoPanelLeaderboard;
