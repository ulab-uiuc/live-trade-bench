import React, { useState, useEffect, useMemo } from 'react';
import './ModelsDisplay.css';

interface Model {
  id: string;
  name: string;
  category: 'polymarket' | 'stock';
  performance: number;
  accuracy: number;
  trades: number;
  profit: number;
  status: 'active' | 'inactive' | 'training';
}

interface ModelsDisplayProps {
  modelsData: Model[];
  stockModels: Model[];
  polymarketModels: Model[];
  onRefresh: () => void;
}

const ModelsDisplay: React.FC<ModelsDisplayProps> = ({
  modelsData,
  stockModels,
  polymarketModels,
  onRefresh
}) => {
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'polymarket' | 'stock'>('all');
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [tooltip, setTooltip] = useState<{show: boolean; content: string; x: number; y: number}>({
    show: false,
    content: '',
    x: 0,
    y: 0
  });

  // 检查是否需要显示分类标签
  const showCategoryTabs = useMemo(() => {
    return stockModels.length > 0 && polymarketModels.length > 0;
  }, [stockModels.length, polymarketModels.length]);

  // 简化的过滤逻辑
  const filteredModels = useMemo(() => {
    // 如果不显示分类标签，直接返回所有数据
    if (!showCategoryTabs) {
      return modelsData;
    }

    switch (selectedCategory) {
      case 'stock': return stockModels;
      case 'polymarket': return polymarketModels;
      default: return modelsData;
    }
  }, [selectedCategory, stockModels, polymarketModels, modelsData, showCategoryTabs]);

  // 简化的状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return '#10b981';
      case 'inactive': return '#ef4444';
      case 'training': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  // 点击模型卡片处理
  const handleModelClick = (model: Model) => {
    setSelectedModel(model);
    setShowModal(true);
  };

  // 关闭模态框
  const closeModal = () => {
    setShowModal(false);
    setSelectedModel(null);
  };

  // 处理悬停提示
  const handleMouseEnter = (asset: any, event: React.MouseEvent) => {
    const rect = event.currentTarget.getBoundingClientRect();
    setTooltip({
      show: true,
      content: `${asset.name}: ${(asset.allocation * 100).toFixed(1)}% | Price: ${asset.price} (${asset.change})`,
      x: rect.left + rect.width / 2,
      y: rect.top - 10
    });
  };

  const handleMouseLeave = () => {
    setTooltip({ show: false, content: '', x: 0, y: 0 });
  };

  // Fetch real profit history data from backend
  const [profitHistoryData, setProfitHistoryData] = useState<{[key: string]: any[]}>({});

  const fetchProfitHistory = async (model: Model) => {
    if (profitHistoryData[model.id]) {
      return profitHistoryData[model.id]; // Return cached data
    }

    try {
      const response = await fetch(`/api/models/${model.id}/chart-data`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const chartData = await response.json();

      // Convert the profit history to the expected format
      const history = chartData.profit_history.map((item: any, index: number) => ({
        day: index + 1,
        profit: item.profit || 0,
        date: new Date(item.timestamp || Date.now()).toLocaleDateString()
      }));

      // Cache the data
      setProfitHistoryData(prev => ({ ...prev, [model.id]: history }));
      return history;
    } catch (error) {
      console.error('Error fetching profit history:', error);
      // Fallback to a simple history with current profit
      return [{
        day: 1,
        profit: model.profit,
        date: new Date().toLocaleDateString()
      }];
    }
  };

  // 生成模拟资产分配数据（包含价格信息）
  const generateAssetAllocation = (model: Model) => {
    if (model.category === 'stock') {
      return [
        { name: 'AAPL', allocation: 0.25, color: '#3b82f6', price: '$175.84', change: '+2.3%' },
        { name: 'MSFT', allocation: 0.20, color: '#10b981', price: '$378.91', change: '+1.8%' },
        { name: 'NVDA', allocation: 0.15, color: '#f59e0b', price: '$887.52', change: '+4.2%' },
        { name: 'GOOGL', allocation: 0.10, color: '#ef4444', price: '$139.67', change: '-0.5%' },
        { name: 'TSLA', allocation: 0.10, color: '#8b5cf6', price: '$248.19', change: '+1.2%' },
        { name: 'CASH', allocation: 0.20, color: '#6b7280', price: '$1.00', change: '0.0%' }
      ];
    } else {
      return [
        { name: 'Election 2024', allocation: 0.35, color: '#3b82f6', price: '$0.65', change: '+5.2%' },
        { name: 'Sports Betting', allocation: 0.25, color: '#10b981', price: '$0.78', change: '-2.1%' },
        { name: 'Crypto Markets', allocation: 0.20, color: '#f59e0b', price: '$0.42', change: '+8.7%' },
        { name: 'CASH', allocation: 0.20, color: '#6b7280', price: '$1.00', change: '0.0%' }
      ];
    }
  };

  // 简单的SVG折线图组件
  const ProfitChartWithData = ({ model, fetchProfitHistory }: { model: Model, fetchProfitHistory: (model: Model) => Promise<any[]> }) => {
    const [chartData, setChartData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
      const loadData = async () => {
        setLoading(true);
        const data = await fetchProfitHistory(model);
        setChartData(data);
        setLoading(false);
      };
      loadData();
    }, [model.id, fetchProfitHistory]);

    if (loading) {
      return (
        <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9ca3af' }}>
          Loading chart data...
        </div>
      );
    }

    return <ProfitChart data={chartData} model={model} />;
  };

  const ProfitChart = ({ data, model }: { data: any[], model: Model }) => {
    const width = 400;
    const height = 200;
    const padding = 40;

    const maxProfit = Math.max(...data.map(d => d.profit));
    const minProfit = Math.min(...data.map(d => d.profit));
    const range = maxProfit - minProfit || 100;

    // 创建SVG路径
    const pathData = data.map((point, index) => {
      const x = padding + (index / (data.length - 1)) * (width - 2 * padding);
      const y = padding + ((maxProfit - point.profit) / range) * (height - 2 * padding);
      return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(' ');

    return (
      <div className="profit-chart">
        <h3>30-Day Profit History</h3>
        <svg width={width} height={height} style={{ border: '1px solid #374151', borderRadius: '0.5rem', background: '#1f2937' }}>
          {/* 网格线 */}
          <defs>
            <pattern id="grid" width="40" height="20" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 20" fill="none" stroke="#374151" strokeWidth="0.5"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />

          {/* 零线 */}
          {minProfit < 0 && maxProfit > 0 && (
            <line
              x1={padding}
              y1={padding + (maxProfit / range) * (height - 2 * padding)}
              x2={width - padding}
              y2={padding + (maxProfit / range) * (height - 2 * padding)}
              stroke="#6b7280"
              strokeWidth="1"
              strokeDasharray="5,5"
            />
          )}

          {/* 利润线 */}
          <path
            d={pathData}
            fill="none"
            stroke={model.profit >= 0 ? '#10b981' : '#ef4444'}
            strokeWidth="2"
          />

          {/* 数据点 */}
          {data.map((point, index) => {
            const x = padding + (index / (data.length - 1)) * (width - 2 * padding);
            const y = padding + ((maxProfit - point.profit) / range) * (height - 2 * padding);
            return (
              <circle
                key={index}
                cx={x}
                cy={y}
                r="2"
                fill={model.profit >= 0 ? '#10b981' : '#ef4444'}
              />
            );
          })}

          {/* Y轴标签 */}
          <text x="10" y={padding} fill="#9ca3af" fontSize="12">${maxProfit.toFixed(0)}</text>
          <text x="10" y={height - padding + 5} fill="#9ca3af" fontSize="12">${minProfit.toFixed(0)}</text>
        </svg>

        {/* 图表说明 */}
        <div className="chart-info">
          <div className="chart-stat">
            <span>Current Profit: </span>
            <span className={model.profit >= 0 ? 'positive' : 'negative'}>
              ${model.profit.toFixed(2)}
            </span>
          </div>
          <div className="chart-stat">
            <span>Performance: </span>
            <span className={model.performance >= 0 ? 'positive' : 'negative'}>
              {model.performance.toFixed(1)}%
            </span>
          </div>
        </div>
      </div>
    );
  };

  // 资产分配横条图组件
  const AssetAllocationBar = ({ model }: { model: Model }) => {
    const allocations = generateAssetAllocation(model);

    return (
      <div className="asset-allocation">
        <h3>Asset Allocation</h3>

        {/* 横条图 */}
        <div className="allocation-bar">
          {allocations.map((asset, index) => (
            <div
              key={asset.name}
              className="allocation-segment"
              style={{
                width: `${asset.allocation * 100}%`,
                backgroundColor: asset.color
              }}
              title={`${asset.name}: ${(asset.allocation * 100).toFixed(1)}%`}
            />
          ))}
        </div>

        {/* 图例 */}
        <div className="allocation-legend">
          {allocations.map((asset) => (
            <div key={asset.name} className="legend-item">
              <div
                className="legend-color"
                style={{ backgroundColor: asset.color }}
              />
              <span className="legend-name">{asset.name}</span>
              <span className="legend-percentage">
                {(asset.allocation * 100).toFixed(1)}%
              </span>
            </div>
          ))}
        </div>


      </div>
    );
  };

  return (
    <div className="models-container">
      {/* 简化的标题 */}
      <div className="models-header">
        <h2 style={{
          color: '#ffffff',
          display: 'block',
          visibility: 'visible',
          opacity: 1,
          position: 'relative',
          zIndex: 1000
        }}>Trading Models</h2>
        <button onClick={onRefresh} className="refresh-btn" style={{
          color: '#9ca3af',
          display: 'block',
          visibility: 'visible',
          opacity: 1
        }}>🔄</button>
      </div>

      {/* 只在有多种类型时显示过滤器 */}
      {showCategoryTabs && (
        <div className="category-tabs">
        <button
          onClick={() => setSelectedCategory('all')}
            className={selectedCategory === 'all' ? 'active' : ''}
        >
            All ({modelsData.length})
        </button>
        <button
            onClick={() => setSelectedCategory('stock')}
            className={selectedCategory === 'stock' ? 'active' : ''}
        >
            Stock ({stockModels.length})
        </button>
        <button
            onClick={() => setSelectedCategory('polymarket')}
            className={selectedCategory === 'polymarket' ? 'active' : ''}
        >
            Polymarket ({polymarketModels.length})
        </button>
        </div>
      )}

            {/* 方形模型卡片，显示资产分配 */}
      <div className="models-grid-square">
        {filteredModels.map(model => {
          const allocations = generateAssetAllocation(model);
          return (
            <div
              key={model.id}
              className="model-card-square"
              onClick={() => handleModelClick(model)}
            >
                                                        {/* 紧凑头部 */}
              <div className="card-header-compact">
                <h3 style={{
                  color: '#ffffff',
                  display: 'block',
                  visibility: 'visible',
                  opacity: 1,
                  position: 'relative',
                  zIndex: 1000
                }}>{model.name}</h3>
                <div className="top-right-badges">
                  <span
                    className="status-dot-small"
                    style={{ backgroundColor: getStatusColor(model.status) }}
                  />
                </div>
      </div>

              {/* 只显示回报率 */}
              <div className="card-return-only">
                <span className="return-label" style={{
                  color: '#9ca3af',
                  display: 'block',
                  visibility: 'visible',
                  opacity: 1,
                  position: 'relative',
                  zIndex: 1000
                }}>Return</span>
                <span className={`return-value-large ${model.performance >= 0 ? 'positive' : 'negative'}`} style={{
                  color: model.performance >= 0 ? '#10b981' : '#ef4444',
                  display: 'block',
                  visibility: 'visible',
                  opacity: 1,
                  position: 'relative',
                  zIndex: 1000
                }}>
                  {model.performance.toFixed(1)}%
                  </span>
              </div>

              {/* 资产分配横条 - 自定义悬停显示 */}
              <div className="card-allocation">
                <div className="allocation-label" style={{
                  color: '#9ca3af',
                  display: 'block',
                  visibility: 'visible',
                  opacity: 1,
                  position: 'relative',
                  zIndex: 1000
                }}>Asset Allocation</div>
                <div className="allocation-bar-mini">
                  {allocations.map((asset) => (
                    <div
                      key={asset.name}
                      className="allocation-segment-mini"
                      style={{
                        width: `${asset.allocation * 100}%`,
                        backgroundColor: asset.color
                      }}
                      onMouseEnter={(e) => handleMouseEnter(asset, e)}
                      onMouseLeave={handleMouseLeave}
                    />
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* 自定义悬停提示 */}
      {tooltip.show && (
        <div
          style={{
            position: 'fixed',
            top: tooltip.y,
            left: tooltip.x,
            transform: 'translateX(-50%)',
            background: 'rgba(0, 0, 0, 0.9)',
            color: 'white',
            padding: '8px 12px',
            borderRadius: '4px',
            fontSize: '12px',
            zIndex: 10000,
            pointerEvents: 'none',
            whiteSpace: 'nowrap',
            boxShadow: '0 4px 8px rgba(0, 0, 0, 0.3)',
            border: '1px solid #374151'
          }}
        >
          {tooltip.content}
        </div>
      )}

      {/* 模态框 */}
      {showModal && selectedModel && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{selectedModel.name}</h2>
              <button className="modal-close" onClick={closeModal}>×</button>
            </div>

            <div className="modal-body">
              <div className="model-details-modal">
                <div className="detail-row">
                  <span>Category:</span>
                  <span className="category-badge">{selectedModel.category}</span>
                </div>
                <div className="detail-row">
                  <span>Status:</span>
                  <span className={`status-badge ${selectedModel.status}`}>
                    {selectedModel.status}
                  </span>
            </div>
                <div className="detail-row">
                  <span>Total Trades:</span>
                  <span>{selectedModel.trades}</span>
                </div>
                <div className="detail-row">
                  <span>Accuracy:</span>
                  <span>{selectedModel.accuracy.toFixed(1)}%</span>
                </div>
              </div>

              <AssetAllocationBar model={selectedModel} />

              <AssetRatioChart model={selectedModel} />

              <ProfitChartWithData
                model={selectedModel}
                fetchProfitHistory={fetchProfitHistory}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Asset Ratio Chart Component
interface AssetRatioChartProps {
  model: Model;
}

const AssetRatioChart: React.FC<AssetRatioChartProps> = ({ model }) => {
  const [ratioHistory, setRatioHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRatioHistory = async () => {
      try {
        setLoading(true);
        // Generate mock historical ratio data for demonstration
        const mockData = generateMockRatioHistory(model);
        setRatioHistory(mockData);
      } catch (error) {
        console.error('Error fetching ratio history:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchRatioHistory();
  }, [model]);

  const generateMockRatioHistory = (model: Model) => {
    const days = 30;
    const data = [];
    const assets = model.category === 'stock' 
      ? ['AAPL', 'GOOGL', 'MSFT', 'CASH']
      : ['Market1', 'Market2', 'Market3', 'CASH'];

    for (let i = 0; i < days; i++) {
      const date = new Date();
      date.setDate(date.getDate() - (days - i));
      
      // Generate realistic allocation changes over time
      const baseAllocations = model.category === 'stock'
        ? [0.3, 0.25, 0.25, 0.2]  // Stock allocations
        : [0.4, 0.3, 0.2, 0.1];   // Polymarket allocations

      const entry: any = {
        date: date.toISOString().split('T')[0],
        timestamp: date.getTime()
      };

      assets.forEach((asset, index) => {
        // Add some variation to the base allocation
        const variation = (Math.sin(i * 0.2) * 0.1) + (Math.random() * 0.1 - 0.05);
        entry[asset] = Math.max(0.05, Math.min(0.6, baseAllocations[index] + variation));
      });

      // Normalize to ensure sum equals 1
      const total = assets.reduce((sum, asset) => sum + entry[asset], 0);
      assets.forEach(asset => {
        entry[asset] = entry[asset] / total;
      });

      data.push(entry);
    }

    return data;
  };

  const colors = ['#60a5fa', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

  if (loading) {
    return (
      <div style={{ 
        padding: '2rem', 
        textAlign: 'center',
        background: '#1f2937',
        borderRadius: '0.5rem',
        margin: '1rem 0'
      }}>
        <div style={{ fontSize: '1rem', color: '#9ca3af' }}>Loading asset ratio history...</div>
      </div>
    );
  }

  const assets = ratioHistory.length > 0 ? Object.keys(ratioHistory[0]).filter(key => key !== 'date' && key !== 'timestamp') : [];
  const maxRatio = Math.max(...ratioHistory.flatMap(entry => assets.map(asset => entry[asset])));
  const chartHeight = 300;
  const chartWidth = 600;
  const margin = { top: 20, right: 80, bottom: 40, left: 50 };

  return (
    <div style={{
      margin: '1rem 0'
    }}>
      <h3 style={{
        color: '#ffffff',
        fontSize: '1.125rem',
        fontWeight: '600',
        marginBottom: '1rem',
        textAlign: 'center'
      }}>
        Asset Allocation History (Past 30 Days)
      </h3>

      <div style={{ 
        display: 'flex', 
        justifyContent: 'center',
        overflowX: 'auto'
      }}>
        <svg width={chartWidth} height={chartHeight + margin.top + margin.bottom}>
          {/* Background grid with gradient */}
          <defs>
            <linearGradient id="chartBackground" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#334155" stopOpacity="0.1"/>
              <stop offset="100%" stopColor="#1e293b" stopOpacity="0.3"/>
            </linearGradient>
          </defs>
          
          {/* Subtle background */}
          <rect 
            x={margin.left} 
            y={margin.top} 
            width={chartWidth - margin.left - margin.right} 
            height={chartHeight}
            fill="url(#chartBackground)"
            rx="8"
          />
          
          {[0, 0.2, 0.4, 0.6, 0.8, 1.0].map((value, index) => {
            const y = margin.top + chartHeight - (value * chartHeight);
            return (
              <g key={index}>
                <line
                  x1={margin.left}
                  y1={y}
                  x2={chartWidth - margin.right}
                  y2={y}
                  stroke={value === 0 ? "#475569" : "#374151"}
                  strokeWidth={value === 0 ? "1.5" : "0.5"}
                  strokeOpacity={value === 0 ? "0.8" : "0.3"}
                  strokeDasharray={value === 0 ? "none" : "3,3"}
                />
                <text
                  x={margin.left - 15}
                  y={y + 4}
                  fill="#d1d5db"
                  fontSize="11"
                  fontWeight="500"
                  textAnchor="end"
                >
                  {(value * 100).toFixed(0)}%
                </text>
              </g>
            );
          })}

          {/* Stacked Areas */}
          {(() => {
            // Calculate cumulative data for stacking
            const stackedData = ratioHistory.map(entry => {
              let cumulative = 0;
              const stacked: any = { date: entry.date };
              assets.forEach(asset => {
                stacked[asset + '_start'] = cumulative;
                cumulative += entry[asset];
                stacked[asset + '_end'] = cumulative;
              });
              return stacked;
            });

            return assets.map((asset, assetIndex) => {
              const color = colors[assetIndex % colors.length];
              
              // Create path for stacked area
              const topPoints = stackedData.map((entry, index) => {
                const x = margin.left + (index / (stackedData.length - 1)) * (chartWidth - margin.left - margin.right);
                const y = margin.top + chartHeight - (entry[asset + '_end'] * chartHeight);
                return `${x},${y}`;
              }).join(' ');

              const bottomPoints = stackedData.map((entry, index) => {
                const x = margin.left + (index / (stackedData.length - 1)) * (chartWidth - margin.left - margin.right);
                const y = margin.top + chartHeight - (entry[asset + '_start'] * chartHeight);
                return `${x},${y}`;
              }).reverse().join(' ');

              const pathData = `M ${topPoints} L ${bottomPoints} Z`;

              return (
                <g key={asset}>
                  {/* Gradient definition for this asset */}
                  <defs>
                    <linearGradient id={`gradient-${asset}`} x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" stopColor={color} stopOpacity="0.8"/>
                      <stop offset="100%" stopColor={color} stopOpacity="0.3"/>
                    </linearGradient>
                  </defs>
                  
                  {/* Stacked area with gradient */}
                  <path
                    d={pathData}
                    fill={`url(#gradient-${asset})`}
                    stroke="none"
                    style={{ 
                      filter: 'drop-shadow(0 1px 3px rgba(0,0,0,0.1))',
                      transition: 'all 0.3s ease'
                    }}
                  />
                  
                  {/* Subtle top border line */}
                  {assetIndex < assets.length - 1 && (
                    <polyline
                      points={topPoints}
                      fill="none"
                      stroke={color}
                      strokeWidth="0.5"
                      strokeOpacity="0.3"
                      style={{ 
                        filter: 'blur(0.5px)',
                        mixBlendMode: 'multiply'
                      }}
                    />
                  )}
                </g>
              );
            });
          })()}

          {/* X-axis labels */}
          {ratioHistory.filter((_, index) => index % 5 === 0).map((entry, index) => {
            const x = margin.left + (index * 5 / (ratioHistory.length - 1)) * (chartWidth - margin.left - margin.right);
            return (
              <text
                key={index}
                x={x}
                y={chartHeight + margin.top + 20}
                fill="#9ca3af"
                fontSize="10"
                textAnchor="middle"
              >
                {new Date(entry.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              </text>
            );
          })}
        </svg>
      </div>

      {/* Legend */}
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        flexWrap: 'wrap',
        gap: '1rem',
        marginTop: '1rem'
      }}>
        {assets.map((asset, index) => (
          <div key={asset} style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <div style={{
              width: '12px',
              height: '12px',
              backgroundColor: colors[index % colors.length],
              borderRadius: '50%'
            }}></div>
            <span style={{
              color: '#d1d5db',
              fontSize: '0.875rem',
              fontWeight: '500'
            }}>
              {asset}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ModelsDisplay;

