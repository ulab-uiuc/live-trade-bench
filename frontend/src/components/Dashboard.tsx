import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./Dashboard.css";
import StockChart from './StockChart';

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
  historyData?: any[]; // chart history data
  modelsLastRefresh?: Date | string;
  stockNextRefresh?: Date | string;
  polymarketNextRefresh?: Date | string;
  systemStatus?: any;
  systemLastRefresh?: Date | string;
  views?: number; // 添加views属性
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

function formatNextUpdate(dateLike?: Date | string) {
  if (!dateLike) return "";
  const date = typeof dateLike === "string" ? new Date(dateLike) : dateLike;
  if (Number.isNaN(date.getTime())) return "";

  const options: Intl.DateTimeFormatOptions = {
    timeZone: "America/New_York",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  };
  const timeString = date.toLocaleTimeString([], options);

  const dateOptions: Intl.DateTimeFormatOptions = {
    timeZone: "America/New_York",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  };
  const nextDate = date.toLocaleDateString([], dateOptions);
  const nowDate = new Date().toLocaleDateString([], dateOptions);

  if (nextDate === nowDate) {
    return `Next update (ET): ${timeString}`;
  }

  return `Next update (ET): ${nextDate} ${timeString}`;
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
  const trades = raw?.trades ||
    raw?.allocationHistory?.length ||
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
  if (n.includes("llama")) return "Meta";
  if (n.includes("gemini")) return "Google";
  if (n.includes("kimi")) return "Moonshot";
  if (n.includes("qwen")) return "Qwen";
  if (n.includes("deepseek")) return "DeepSeek";
  if (n.includes("grok")) return "xAI";
  return "Other";
}

function getHomepageUrl(modelName?: string): string {
  if (!modelName) return "";

  // 直接映射20个固定模型的homepage链接
  const homepageMap: { [key: string]: string } = {
    // OpenAI models
    "GPT-5": "https://platform.openai.com/docs/models/gpt-5",
    "GPT-4.1": "https://openai.com/index/gpt-4-1/",
    "GPT-4o": "https://openai.com/index/gpt-4o/",
    "GPT-o3": "https://openai.com/index/introducing-o3-and-o4-mini/",
    // Anthropic models
    "Claude-Opus-4.1": "https://www.anthropic.com/news/claude-opus-4-1",
    "Claude-Opus-4": "https://www.anthropic.com/news/claude-4",
    "Claude-Sonnet-4": "https://www.anthropic.com/news/claude-4",
    "Claude-Sonnet-3.7": "https://www.anthropic.com/news/claude-3-7-sonnet",
    // Google models
    "Gemini-2.5-Flash": "http://aistudio.google.com/app/prompts/new_chat?model=gemini-2.5-flash",
    "Gemini-2.5-Pro": "http://aistudio.google.com/app/prompts/new_chat?model=gemini-2.5-pro",
    // xAI models
    "Grok-4": "https://docs.x.ai/docs/models/grok-4-0709",
    "Grok-3": "https://docs.x.ai/docs/models/grok-3",
    // Meta models
    "Llama4-Maverick": "https://huggingface.co/meta-llama/Llama-4-Maverick-17B-128E-Instruct",
    "Llama4-Scout": "https://huggingface.co/meta-llama/Llama-4-Scout-17B-16E-Instruct",
    "Llama3.3-70B-Instruct-Turbo": "https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct",
    // Qwen models
    "Qwen3-235B-A22B-Instruct": "https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507",
    "Qwen3-235B-A22B-Thinking": "https://huggingface.co/Qwen/Qwen3-235B-A22B-Thinking-2507",
    "Qwen2.5-72B-Instruct": "https://qwenlm.github.io/blog/qwen2.5/",
    // DeepSeek models
    "DeepSeek-R1": "https://api-docs.deepseek.com/news/news250120",
    "DeepSeek-V3.1": "https://huggingface.co/deepseek-ai/DeepSeek-V3.1",
    // Moonshot models
    "Kimi-K2-Instruct": "https://huggingface.co/moonshotai/Kimi-K2-Instruct-0905",
    "QQQ (Invesco QQQ Trust)": "https://finance.yahoo.com/quote/QQQ/",
    "VOO (Vanguard S&P 500 ETF)": "https://finance.yahoo.com/quote/VOO/",
  };

  return homepageMap[modelName] || "";
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
    if (p.includes("kimi") || n.includes("kimi")) {
      return "./kimi.png";
    }
    if (p.includes("qwen") || n.includes("qwen")) {
      return "./qwen.png";
    }
    if (p.includes("deepseek") || n.includes("deepseek")) {
      return "./deepseek.png";
    }
    if (p.includes("xai") || p.includes("grok") || n.includes("grok")) {
      return "./xai.png";
    }
    return "./benchmark.png"; // Default emoji
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
    if (p.includes("xai") || p.includes("grok") || n.includes("grok")) return "xai";
    return "other";
  };

  const icon = getProviderIcon(provider, name);
  const isBenchmarkIcon = typeof icon === 'string' && icon.includes('benchmark');
  const cls = isBenchmarkIcon ? 'benchmark' : getProviderClass(provider, name);
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
  nextUpdate?: Date | string;
  items: ModelRow[];
  category: "stock" | "polymarket" | "bitmex";
}> = ({ title, updatedAt, nextUpdate, items, category }) => {
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
        <div className="card-updated">
          {nextUpdate ? formatNextUpdate(nextUpdate) : relativeTime(updatedAt)}
        </div>
      </div>

      {/* Desktop Table */}
      <div className="leaderboard-table">
        {/* Header */}
        <div className="table-header">
          <div>
            <span className="rank-header-full">Rank</span>
            <span className="rank-header-short">🏆</span>
          </div>
          <div>Model</div>
          <div>Return</div>
          <div>
            <span className="trades-header-full">#Trades</span>
            <span className="trades-header-short">#</span>
          </div>
        </div>

        {/* Rows */}
        {rows.map((row) => {
          const homepageUrl = getHomepageUrl(row.name);
          const isBenchmark =
            (typeof row.id === "string" && row.id.includes("benchmark")) ||
            /\bQQQ\b|\bVOO\b/i.test(row.name);

          return (
            <div
              key={row.id}
              className={`table-row ${isBenchmark ? "benchmark" : ""}`}
              onClick={homepageUrl ? () => window.open(homepageUrl, '_blank') : undefined}
              style={{ cursor: homepageUrl ? 'pointer' : 'default' }}
            >
              {/* Rank */}
              <div className={`rank-cell ${row.rank <= 3 ? `top-3 rank-${row.rank}` : ''}`}>
                {getRankDisplay(row.rank)}
              </div>

              {/* Model */}
              <div className="model-cell">
                <ProviderIcon name={row.name} provider={row.provider} />
                <div className="model-name-group">
                  <div className={`model-name ${isBenchmark ? "benchmark-name" : ""}`}>
                    {row.name}
                  </div>
                </div>
              </div>

              {/* Score/Performance */}
              <div className={`score-cell ${getScoreClass(row.score)}`}>
                {row.score > 0 ? '+' : ''}{row.score.toFixed(1)}%
              </div>

              {/* Votes/Trades */}
              <div className="votes-cell">
                {row.votes === 0 ? '-' : row.votes}
              </div>
            </div>
          );
        })}
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



// ... (existing imports)

// ------- Main Dashboard Component -------

const TwoPanelLeaderboard: React.FC<DashboardProps> = ({ modelsData = [], historyData = [], modelsLastRefresh = new Date(), stockNextRefresh, polymarketNextRefresh, systemStatus, systemLastRefresh, views = 0 }) => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'chart' | 'rankings'>('chart');
  const [timeRange, setTimeRange] = useState<'1M' | 'ALL'>('1M');
  const [category, setCategory] = useState<'stock' | 'polymarket' | 'bitmex'>('stock');

  // 格式化数字显示
  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1).replace('.0', '') + 'M';
    } else {
      return num.toLocaleString();
    }
  };

  const stock = modelsData
    .filter((m) => {
      const category = (m?.category ?? "").toString().toLowerCase();
      return category === "stock" || category === "benchmark";
    })
    .map(normalize);
  const poly = modelsData
    .filter((m) => (m?.category ?? "").toString().toLowerCase().includes("poly"))
    .map(normalize);
  const bitmex = modelsData
    .filter((m) => {
      const category = (m?.category ?? "").toString().toLowerCase();
      return category === "bitmex" || category === "bitmex-benchmark";
    })
    .map(normalize);

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div className="title-container">
          <h1 className="dashboard-title">
            Live Trading Benchmark
          </h1>
          <div className="views-badge-small">
            Views: {formatNumber(views)}
          </div>
        </div>
        <p className="dashboard-subtitle">
          Real-time leaderboard for LLM-powered portfolio management. Know more at {" "}
          <button
            className="about-link"
            onClick={() => navigate('/about')}
          >
            About
          </button>.
        </p>

        {/* Description Section */}
        <div style={{
          maxWidth: '1000px',
          margin: '2rem auto 0',
          padding: '1rem 1.5rem',
          background: 'rgba(156, 158, 248, 0.1)',
          border: '1px solid rgba(156, 158, 248, 0.3)',
          borderRadius: '12px',
          color: 'rgba(255, 255, 255, 0.8)',
          fontSize: '0.95rem',
          lineHeight: '1.6',
          textAlign: 'left'
        }}>
          We evaluate AI trading agents across multiple asset classes in real-time. Each agent manages a diversified portfolio, making allocation decisions based on three types of information: (1) market price data; (2) real-time news data and (3) historical allocation data. For detailed information, please click the{" "}
          <button
            className="about-link"
            onClick={() => navigate('/stocks')}
            style={{
              background: 'none',
              border: 'none',
              color: '#9c9ef8',
              textDecoration: 'underline',
              fontSize: 'inherit',
              fontFamily: 'inherit',
              cursor: 'pointer',
              padding: 0,
              transition: 'color 0.2s ease'
            }}
            onMouseEnter={(e) => e.currentTarget.style.color = '#818cf8'}
            onMouseLeave={(e) => e.currentTarget.style.color = '#9c9ef8'}
          >
            Stock
          </button>
          {", "}
          <button
            className="about-link"
            onClick={() => navigate('/polymarket')}
            style={{
              background: 'none',
              border: 'none',
              color: '#9c9ef8',
              textDecoration: 'underline',
              fontSize: 'inherit',
              fontFamily: 'inherit',
              cursor: 'pointer',
              padding: 0,
              transition: 'color 0.2s ease'
            }}
            onMouseEnter={(e) => e.currentTarget.style.color = '#818cf8'}
            onMouseLeave={(e) => e.currentTarget.style.color = '#9c9ef8'}
          >
            Polymarket
          </button>
          {", or "}
          <button
            className="about-link"
            onClick={() => navigate('/bitmex')}
            style={{
              background: 'none',
              border: 'none',
              color: '#9c9ef8',
              textDecoration: 'underline',
              fontSize: 'inherit',
              fontFamily: 'inherit',
              cursor: 'pointer',
              padding: 0,
              transition: 'color 0.2s ease'
            }}
            onMouseEnter={(e) => e.currentTarget.style.color = '#818cf8'}
            onMouseLeave={(e) => e.currentTarget.style.color = '#9c9ef8'}
          >
            BitMEX
          </button>{" "}
          for more information.
        </div>

        {/* Tab Switcher - Aligned with chart controls */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginTop: '2rem',
          marginBottom: '1rem',
          paddingLeft: '10px',
          paddingRight: '10px',
          borderBottom: '1px solid #374151',
          paddingBottom: '10px'
        }}>
          {/* Category selector - only show when chart is active */}
          <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-start' }}>
            {activeTab === 'chart' && (
              <div className="toggle-group">
                <button
                  className={`toggle-btn ${category === 'stock' ? 'active' : ''}`}
                  onClick={() => setCategory('stock')}
                >
                  Stock
                </button>
                <button
                  className={`toggle-btn ${category === 'polymarket' ? 'active' : ''}`}
                  onClick={() => setCategory('polymarket')}
                >
                  Polymarket
                </button>
                <button
                  className={`toggle-btn ${category === 'bitmex' ? 'active' : ''}`}
                  onClick={() => setCategory('bitmex')}
                >
                  BitMEX
                </button>
              </div>
            )}
          </div>

          {/* Chart/Rankings selector - center */}
          <div className="toggle-group">
            <button
              className={`toggle-btn ${activeTab === 'chart' ? 'active' : ''}`}
              onClick={() => setActiveTab('chart')}
            >
              Chart
            </button>
            <button
              className={`toggle-btn ${activeTab === 'rankings' ? 'active' : ''}`}
              onClick={() => setActiveTab('rankings')}
            >
              Rankings
            </button>
          </div>

          {/* Time range selector - only show when chart is active */}
          <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end' }}>
            {activeTab === 'chart' && (
              <div className="toggle-group">
                <button
                  className={`toggle-btn ${timeRange === '1M' ? 'active' : ''}`}
                  onClick={() => setTimeRange('1M')}
                >
                  30 Days
                </button>
                <button
                  className={`toggle-btn ${timeRange === 'ALL' ? 'active' : ''}`}
                  onClick={() => setTimeRange('ALL')}
                >
                  ALL
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Chart Section */}
      <div style={{ marginTop: '0', display: activeTab === 'chart' ? 'block' : 'none' }}>
        <StockChart
          modelsData={modelsData}
          historyData={historyData}
          timeRange={timeRange}
          category={category}
        />
      </div>

      {/* Rankings Section */}
      <div className="leaderboard-grid" style={{ display: activeTab === 'rankings' ? 'grid' : 'none' }}>
        <LeaderboardCard
          key="stock-leaderboard"
          title="Stock"
          updatedAt={modelsLastRefresh}
          nextUpdate={stockNextRefresh}
          items={stock}
          category="stock"
        />
        <LeaderboardCard
          key="polymarket-leaderboard"
          title="Polymarket"
          updatedAt={modelsLastRefresh}
          nextUpdate={polymarketNextRefresh}
          items={poly}
          category="polymarket"
        />
        <LeaderboardCard
          key="bitmex-leaderboard"
          title="BitMEX"
          updatedAt={modelsLastRefresh}
          nextUpdate={undefined}
          items={bitmex}
          category="bitmex"
        />
      </div>
    </div>
  );
};

export default TwoPanelLeaderboard;
