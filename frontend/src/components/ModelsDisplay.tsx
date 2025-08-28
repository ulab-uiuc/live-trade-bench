import React, { useState, useMemo } from 'react';
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

  // 生成模拟利润历史数据
  const generateProfitHistory = (model: Model) => {
    const days = 30;
    const history = [];
    let currentProfit = 0;
    const dailyVariance = Math.abs(model.profit) / days;

    for (let i = 0; i < days; i++) {
      const change = (Math.random() - 0.5) * dailyVariance * 2;
      currentProfit += change;
      history.push({
        day: i + 1,
        profit: currentProfit,
        date: new Date(Date.now() - (days - i) * 24 * 60 * 60 * 1000).toLocaleDateString()
      });
    }

    // 确保最后一天的利润接近实际利润
    history[days - 1].profit = model.profit;

    return history;
  };

  // 生成模拟资产分配数据
  const generateAssetAllocation = (model: Model) => {
    if (model.category === 'stock') {
      return [
        { name: 'AAPL', allocation: 0.25, color: '#3b82f6' },
        { name: 'MSFT', allocation: 0.20, color: '#10b981' },
        { name: 'NVDA', allocation: 0.15, color: '#f59e0b' },
        { name: 'GOOGL', allocation: 0.10, color: '#ef4444' },
        { name: 'TSLA', allocation: 0.10, color: '#8b5cf6' },
        { name: 'CASH', allocation: 0.20, color: '#6b7280' }
      ];
    } else {
      return [
        { name: 'Election 2024', allocation: 0.35, color: '#3b82f6' },
        { name: 'Sports Betting', allocation: 0.25, color: '#10b981' },
        { name: 'Crypto Markets', allocation: 0.20, color: '#f59e0b' },
        { name: 'CASH', allocation: 0.20, color: '#6b7280' }
      ];
    }
  };

  // 简单的SVG折线图组件
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

        {/* 总计验证 */}
        <div className="allocation-total">
          <span>Total: {(allocations.reduce((sum, asset) => sum + asset.allocation, 0) * 100).toFixed(1)}%</span>
        </div>
      </div>
    );
  };

  return (
    <div className="models-container">
      {/* 简化的标题 */}
      <div className="models-header">
        <h2>Trading Models</h2>
        <button onClick={onRefresh} className="refresh-btn">🔄</button>
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
                <h3>{model.name}</h3>
                <div className="top-right-badges">
                  <div className={`category-tag ${model.category}`}>{model.category}</div>
                  <span
                    className="status-dot-small"
                    style={{ backgroundColor: getStatusColor(model.status) }}
                  />
                </div>
              </div>

              {/* 只显示回报率 */}
              <div className="card-return-only">
                <span className="return-label">Return</span>
                <span className={`return-value-large ${model.performance >= 0 ? 'positive' : 'negative'}`}>
                  {model.performance.toFixed(1)}%
                  </span>
              </div>

              {/* 资产分配横条 */}
              <div className="card-allocation">
                <div className="allocation-label">Asset Allocation</div>
                <div className="allocation-bar-mini">
                  {allocations.map((asset) => (
                    <div
                      key={asset.name}
                      className="allocation-segment-mini"
                      style={{
                        width: `${asset.allocation * 100}%`,
                        backgroundColor: asset.color
                      }}
                      title={`${asset.name}: ${(asset.allocation * 100).toFixed(1)}%`}
                    />
                  ))}
                </div>
                <div className="allocation-legend-mini">
                  {allocations.slice(0, 3).map((asset) => (
                    <div key={asset.name} className="legend-item-mini">
                      <div
                        className="legend-dot"
                        style={{ backgroundColor: asset.color }}
                      />
                      <span>{asset.name} {(asset.allocation * 100).toFixed(0)}%</span>
                    </div>
                  ))}
                  {allocations.length > 3 && (
                    <div className="legend-item-mini">
                      <span>+{allocations.length - 3} more</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

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

              <ProfitChart
                data={generateProfitHistory(selectedModel)}
                model={selectedModel}
              />

              <AssetAllocationBar model={selectedModel} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelsDisplay;
