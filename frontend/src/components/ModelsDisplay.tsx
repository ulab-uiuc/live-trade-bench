import React, { useState, useEffect, useMemo, useCallback, memo } from 'react';
import './ModelsDisplay.css';
import type { Model } from '../types';
import { getAssetColor, getCashColor } from '../utils/colors';
// Removed: import { AllocationHistoryItem, AssetAllocation, AssetMetadata } from '../types';

// Custom Tooltip State
type TooltipInfo = {
  content: string;
  x: number;
  y: number;
};

interface ModelsDisplayProps {
  modelsData: Model[];
  stockModels: Model[];
  polymarketModels: Model[];
  onRefresh?: () => void;
  // Removed assetMetadata prop
}

const ModelsDisplay: React.FC<ModelsDisplayProps> = ({
  modelsData,
  stockModels,
  polymarketModels,
  onRefresh,
  // assetMetadata // Removed from destructuring
}) => {
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'polymarket' | 'stock'>('all');
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [tooltip, setTooltip] = useState<TooltipInfo | null>(null);

  // Pre-warm the tooltip system to avoid first-hover delay
  useEffect(() => {
    // Initialize tooltip state immediately when modal opens
    if (showModal) {
      setTooltip(null);
    }
  }, [showModal]);


  const showCategoryTabs = useMemo(() => {
    return stockModels.length > 0 && polymarketModels.length > 0;
  }, [stockModels.length, polymarketModels.length]);


  const filteredModels = useMemo(() => {

    if (!showCategoryTabs) {
      return modelsData;
    }

    switch (selectedCategory) {
      case 'stock': return stockModels;
      case 'polymarket': return polymarketModels;
      default: return modelsData;
    }
  }, [selectedCategory, stockModels, polymarketModels, modelsData, showCategoryTabs]);


  const getStatusColor = (status: string) => ({
    active: '#10b981',
    inactive: '#ef4444',
    training: '#f59e0b'
  } as const)[status as 'active' | 'inactive' | 'training'] || '#6b7280';


  const handleModelClick = useCallback((model: Model) => {
    console.log('🔥 Modal opening for model:', model.name, 'category:', model.category);
    setSelectedModel(model);
    setShowModal(true);
  }, []);

  // Tooltip handlers - immediate DOM-based response
  const handleMouseMove = useCallback((e: React.MouseEvent, content: string) => {
    // Immediate state update without any async operations
    const newTooltip = { content, x: e.clientX + 15, y: e.clientY + 15 };
    setTooltip(newTooltip);
  }, []);

  const handleMouseLeave = useCallback(() => {
    setTooltip(null);
  }, []);


  const closeModal = useCallback(() => {
    setShowModal(false);
    setSelectedModel(null);
  }, []);

  // Simplified "dumb" chart components that receive all data via props

  // Profit Chart
  const ProfitChart = memo(({ data, profit, performance, onMouseMove, onMouseLeave }: {
    data: any[];
    profit: number;
    performance: number;
    onMouseMove: (e: React.MouseEvent, content: string) => void;
    onMouseLeave: () => void;
  }) => {
    const width = 400;
    const height = 200;
    const padding = 40;

    const chartData = useMemo(() => Array.isArray(data) ? data.slice(-30) : [], [data]);

    const { maxProfit, minProfit, range, pathData } = useMemo(() => {
      // Ensure data is an array before mapping
      const validData = chartData;
      const profits = validData.map(d => d.profit);

      const maxP = profits.length > 0 ? Math.max(...profits) : 0;
      const minP = profits.length > 0 ? Math.min(...profits) : 0;
      const r = maxP - minP || 100;

      let path;
      if (validData.length === 1) {
        // If only one point, draw a horizontal line across the chart
        const y = padding + ((maxP - validData[0].profit) / r) * (height - 2 * padding);
        path = `M ${padding},${y} L ${width - padding},${y}`;
      } else {
        path = validData.map((point, index) => {
          const x = padding + (index / (validData.length - 1)) * (width - 2 * padding);
          const y = padding + ((maxP - point.profit) / r) * (height - 2 * padding);
          return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
        }).join(' ');
      }

      return { maxProfit: maxP, minProfit: minP, range: r, pathData: path };
    }, [chartData]);

    if (chartData.length === 0) {
      return (
        <div className="profit-chart">
          <h3>Profit History</h3>
          <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9ca3af' }}>
            No profit history available.
          </div>
        </div>
      );
    }

    return (
      <div className="profit-chart">
        <h3>Profit History</h3>
        <svg width={width} height={height} className="chart-svg">
          {/*  */}
          <defs>
            <pattern id="grid" width="40" height="20" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 20" fill="none" stroke="#374151" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />

          {/*  */}
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

          {/*  */}
          <path
            d={pathData}
            fill="none"
            stroke={profit >= 0 ? '#10b981' : '#ef4444'}
            strokeWidth="2"
          />

          {/*  */}
          {chartData.map((point, index) => {
            const x = padding + (index / (chartData.length - 1)) * (width - 2 * padding);
            const y = padding + ((maxProfit - point.profit) / range) * (height - 2 * padding);
            return (
              <circle
                key={index}
                cx={x}
                cy={y}
                r="4"
                fill={profit >= 0 ? '#10b981' : '#ef4444'}
                style={{ cursor: 'pointer', transition: 'r 0.2s' }}
                onMouseMove={(e) => {
                  const date = new Date(point.date).toLocaleDateString();
                  onMouseMove(e, `Date: ${date} | Profit: $${point.profit.toFixed(2)}`);
                }}
                onMouseEnter={(e) => e.currentTarget.setAttribute('r', '6')}
                onMouseLeave={(e) => {
                  e.currentTarget.setAttribute('r', '4');
                  onMouseLeave();
                }}
              />
            );
          })}

          {/* Y */}
          <text x="10" y={padding} fill="#9ca3af" fontSize="12">${maxProfit.toFixed(0)}</text>
          <text x="10" y={height - padding + 5} fill="#9ca3af" fontSize="12">${minProfit.toFixed(0)}</text>
        </svg>

        {/*  */}
        <div className="chart-info">
          <div className="chart-stat">
            <span>Current Profit: </span>
            <span className={profit >= 0 ? 'positive' : 'negative'}>
              ${profit.toFixed(2)}
            </span>
          </div>
          <div className="chart-stat">
            <span>Performance: </span>
            <span className={performance >= 0 ? 'positive' : 'negative'}>
              {performance.toFixed(1)}%
            </span>
          </div>
        </div>
      </div>
    );
  });

  // Asset Allocation Bar (for modal)
  const AssetAllocationBar = memo(({
    portfolioData,
    category,
    onMouseMove,
    onMouseLeave
  }: {
    portfolioData: any;
    category: string;
    onMouseMove: (e: React.MouseEvent, content: string) => void;
    onMouseLeave: () => void;
  }) => {
    const allocations = useMemo(() => {
      if (!portfolioData) return [];

      const allocSource = portfolioData.current_allocations || {};

      const sortedAssetNames = Object.keys(allocSource)
        .sort((a, b) => {
          if (a === 'CASH') return 1;
          if (b === 'CASH') return -1;
          return a.localeCompare(b);
        });

      return sortedAssetNames.map((name, index) => {
        const allocation = allocSource[name] || 0;
        return {
          name,
          allocation,
          isCash: name === 'CASH',
          isPolymarket: category === 'polymarket',
          color: getAssetColor(name, index, category as 'stock' | 'polymarket'),
        };
      });
    }, [portfolioData, category]);

    // DEBUG: Log the category and colors
    if (allocations.find(a => a.name === 'AAPL')) {
      console.log('DEBUG (AssetAllocationBar) for AAPL:', {
        category,
        color: allocations.find(a => a.name === 'AAPL')?.color
      });
    }


    return (
      <div className="asset-allocation">
        <h3>Asset Allocation</h3>

        {/*  */}
        <div className="allocation-bar">
          {allocations.map((asset, index) => (
            <div
              key={asset.name}
              className="allocation-segment"
              style={{
                width: `${asset.allocation * 100}%`,
                backgroundColor: asset.color,
                minWidth: '10px' // Ensure minimum clickable area
              }}
              title={`${asset.name}: ${(asset.allocation * 100).toFixed(1)}%`}
              onMouseMove={(e) => onMouseMove(e, `${asset.name}: ${(asset.allocation * 100).toFixed(1)}%`)}
              onMouseLeave={onMouseLeave}
            />
          ))}
        </div>

        {/*  */}
        <div className="allocation-legend">
          {allocations.map((asset) => {
            // Check if this is a Polymarket position with additional info
            const position = portfolioData?.positions?.[asset.name];
            const isPolymarket = category === 'polymarket' && position?.question;

            // Debug logging
            if (category === 'polymarket') {
              console.log('Asset:', asset.name, 'Position:', position, 'IsPolymarket:', isPolymarket);
              console.log('PortfolioData:', portfolioData);
            }

            return (
              <div key={asset.name} className="legend-item">
                <div
                  className="legend-color"
                  style={{ backgroundColor: asset.color }}
                />
                <div className="legend-content">
                  {isPolymarket ? (
                    <div className="polymarket-item">
                      <div className="legend-name">
                        <a
                          href={position.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="polymarket-link"
                          title={position.question}
                        >
                          {position.question}
                        </a>
                      </div>
                      <div className="legend-category">
                        {position.category}
                      </div>
                    </div>
                  ) : (
                    (() => {
                      const stockLink = category === 'stock' && asset.name !== 'CASH' && position?.url
                        ? String(position.url)
                        : (category === 'stock' && asset.name !== 'CASH' ? `https://finance.yahoo.com/quote/${asset.name}` : undefined);
                      return stockLink ? (
                        <a
                          href={stockLink}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="polymarket-link"
                          title={asset.name}
                        >
                          {asset.name}
                        </a>
                      ) : (
                        <span className="legend-name">{asset.name}</span>
                      );
                    })()
                  )}
                  <span className="legend-percentage">
                    {(asset.allocation * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>


      </div>
    );
  });

  const miniAllocations = useMemo(() => {
    if (filteredModels.length === 0) return []; // Use filteredModels here

    // Aggregate allocations across all filtered models for the mini-chart
    if (selectedCategory === 'stock') {
      const aggregatedAllocations: Record<string, number> = {};
      filteredModels.forEach(model => { // Use filteredModels
        if (model.category === 'stock') {
          Object.entries(model.asset_allocation).forEach(([name, allocation]) => {
            if (allocation > 0) {
              aggregatedAllocations[name] = (aggregatedAllocations[name] || 0) + allocation;
            }
          });
        }
      });

      const assetNames = Object.keys(aggregatedAllocations);
      const sortedAssetNames = [...assetNames].sort((a, b) => {
        if (a === 'CASH') return 1;
        if (b === 'CASH') return -1;
        return a.localeCompare(b);
      });

      return sortedAssetNames.map((name, index) => {
        return {
          name,
          allocation: aggregatedAllocations[name] || 0,
          color: getAssetColor(name, index, 'stock'), // Explicitly pass 'stock' category
        };
      });
    } else if (selectedCategory === 'polymarket') {
      // For Polymarket, aggregate YES/NO outcomes for the same market
      const polymarketAggregatedAllocations: Record<string, { allocation: number; url: string; question: string }> = {};

      filteredModels.forEach(model => { // Use filteredModels
        if (model.category === 'polymarket') { // Ensure we only aggregate polymarket models here
          Object.entries(model.asset_allocation).forEach(([marketKey, allocation]) => {
            if (allocation > 0) {
              const parts = marketKey.split('_');
              const marketId = parts.slice(0, -1).join('_');
              // Safely access market_info from the model for question and url
              const marketInfo = model.portfolio.positions[marketKey]; // marketKey from model.asset_allocation can be a full key like 'marketId_YES'

              const existing = polymarketAggregatedAllocations[marketId] || { allocation: 0, url: '', question: '' };
              existing.allocation += allocation;
              existing.url = marketInfo?.url || '';
              existing.question = marketInfo?.question || '';
              polymarketAggregatedAllocations[marketId] = existing;
            }
          });
        }
      });

      const sortedMarketKeys = Object.keys(polymarketAggregatedAllocations)
        .sort((a, b) => {
          // For Polymarket mini-chart, still sort alphabetically by marketKey for consistent color assignment
          return a.localeCompare(b);
        });

      return sortedMarketKeys.map((marketKey, index) => {
        const { allocation, url, question } = polymarketAggregatedAllocations[marketKey];
        return {
          name: question || marketKey,
          allocation,
          isPolymarket: true,
          url,
          question,
          color: getAssetColor(marketKey, index, 'polymarket'), // Explicitly pass 'polymarket' category
        };
      });
    }
    return [];
  }, [filteredModels, selectedCategory]); // Corrected dependencies

  // Common function to handle mouse move for tooltips
  const onMouseMove = useCallback(
    (event: React.MouseEvent<HTMLDivElement>, content: string) => {
      setTooltip({ x: event.clientX + 10, y: event.clientY + 10, content });
    },
    []
  );

  const onMouseLeave = useCallback(() => {
    setTooltip(null);
  }, []);

  return (
    <div className="models-container">
      {/*  */}
      <div className="models-header">
        <h2>Trading Models</h2>
        {/* Refresh button is now conditional */}
        {onRefresh && <button onClick={onRefresh} className="refresh-btn">🔄</button>}
      </div>

      {/*  */}
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

      <div className="models-grid-square">
        {filteredModels.map(model => {
          // Use the real (mocked) asset allocation from the model prop
          const modelAllocationAssets = Object.entries(model.asset_allocation || {});

          const allocations = modelAllocationAssets.length > 0
            ? (() => {
              const arr = modelAllocationAssets
                .map(([name, allocation]) => ({
                  name,
                  allocation,
                  // The color for mini-allocation bar needs to be consistent,
                  // so we use the index from its own sorted list
                  color: getAssetColor(name,
                    [...Object.keys(model.asset_allocation || {})].sort((a, b) => {
                      if (a === 'CASH') return 1;
                      if (b === 'CASH') return -1;
                      return a.localeCompare(b);
                    }).indexOf(name),
                    model.category as 'stock' | 'polymarket')
                }))
                .sort((a, b) => {
                  if (a.name === 'CASH') return 1;
                  if (b.name === 'CASH') return -1;
                  return a.name.localeCompare(b.name);
                });
              const cashIndex = arr.findIndex(i => i.name === 'CASH');
              if (cashIndex > -1) {
                const [cashItem] = arr.splice(cashIndex, 1);
                arr.push(cashItem);
              }
              return arr;
            })()
            : []; // Default to empty if no allocation data

          return (
            <div
              key={model.id}
              className="model-card-square"
              onClick={() => handleModelClick(model)}
            >
              {/*  */}
              <div className="card-header-compact">
                <h3>{model.name}</h3>
                <div className="top-right-badges">
                  <span
                    className="status-dot-small"
                    style={{ backgroundColor: getStatusColor(model.status) }}
                  />
                </div>
              </div>

              <div className="card-return-only">
                <span className="return-label">Return</span>
                <span className={`return-value-large ${model.performance >= 0 ? 'positive' : 'negative'}`}>
                  {model.performance.toFixed(1)}%
                </span>
            </div>

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
                      onMouseMove={(e) => handleMouseMove(e, `${asset.name}: ${(asset.allocation * 100).toFixed(1)}%`)}
                      onMouseLeave={handleMouseLeave}
                    />
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Custom Tooltip Renderer */}
      {tooltip && (
        <div
          className="custom-tooltip"
          style={{
            left: `${tooltip.x}px`,
            top: `${tooltip.y}px`,
          }}
        >
          {tooltip.content}
                </div>
              )}

      {showModal && selectedModel && (
        console.log('🔥 Modal rendering for:', selectedModel.name),
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
              </div>

              <AssetAllocationBar
                portfolioData={selectedModel.portfolio}
                category={selectedModel.category}
                onMouseMove={handleMouseMove}
                onMouseLeave={handleMouseLeave}
              />
              {/* Debug category */}

              {/*  */}
              <div style={{
                height: '1px',
                background: 'linear-gradient(90deg, transparent 0%, #374151 50%, transparent 100%)',
                margin: '2rem 0',
                position: 'relative'
              }}>
            </div>

              <AssetRatioChart
                allocationHistory={selectedModel.allocationHistory}
                portfolio={selectedModel.portfolio}
                // assetMeta={(selectedModel as any).asset_meta || {}} // Removed this prop
                category={selectedModel.category}
                onMouseMove={handleMouseMove}
                onMouseLeave={handleMouseLeave}
              />

              <div style={{
                height: '1px',
                background: 'linear-gradient(90deg, transparent 0%, #374151 50%, transparent 100%)',
                margin: '2rem 0',
                position: 'relative'
              }}>
              </div>

              <ProfitChart
                data={selectedModel.chartData.profit_history}
                profit={selectedModel.profit}
                performance={selectedModel.performance}
                onMouseMove={handleMouseMove}
                onMouseLeave={handleMouseLeave}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Asset Ratio Chart Component (now a "dumb" component)
const AssetRatioChart: React.FC<{
  allocationHistory: any[];
  portfolio: any;
  // assetMeta: Record<string, { question?: string; url?: string; category?: string }>; // Removed this prop
  category: string;
  onMouseMove: (e: React.MouseEvent, content: string) => void;
  onMouseLeave: () => void;
}> = ({ allocationHistory, portfolio, category, onMouseMove, onMouseLeave }) => {

  // Create unique ID for this chart instance to avoid SVG gradient conflicts
  const chartId = useMemo(() => Math.random().toString(36).substr(2, 9), []);

  const chartData = useMemo(() => {
    if (!Array.isArray(allocationHistory) || allocationHistory.length === 0) return [] as any[];
    // Slice to the last 30 entries and normalize allocations into { [name]: weight }
    return allocationHistory.slice(-30).map((snapshot: any) => {
      const alloc = snapshot?.allocations;
      if (Array.isArray(alloc)) {
        const obj: Record<string, number> = {};
        alloc.forEach((a: any) => {
          if (a && a.name != null) obj[a.name] = a.weight ?? 0;
        });
        return obj;
      }
      return alloc || {};
    });
  }, [allocationHistory]);

  const allAssets = useMemo(() => {
      const assetSet = new Set<string>();
      chartData.forEach(allocations => {
          Object.keys(allocations).forEach(asset => assetSet.add(asset));
      });
      // Ensure CASH is last for stacking order if it exists
      const sortedAssets = Array.from(assetSet).sort((a, b) => {
        if (a === 'CASH') return 1;
        if (b === 'CASH') return -1;
        return a.localeCompare(b);
      });
      return sortedAssets;
  }, [chartData]);

  const stackedData = useMemo(() => {
    return chartData.map(allocations => {
        let cumulative = 0;
        const stacked: { [key: string]: number } = {};
        allAssets.forEach(asset => {
            const value = allocations[asset] || 0; // Default to 0 if asset not in this snapshot
            stacked[asset + '_start'] = cumulative;
            cumulative += value;
            stacked[asset + '_end'] = cumulative;
        });
        return stacked;
    });
  }, [chartData, allAssets]);

  // Build meta map for latest snapshot (name -> {url, category})
  const latestMeta = useMemo(() => {
    const latest = Array.isArray(allocationHistory) && allocationHistory.length > 0
      ? allocationHistory[allocationHistory.length - 1]
      : null;
    const map: Record<string, { url?: string; question?: string; category?: string }> = {};
    if (latest && Array.isArray(latest.allocations)) {
      latest.allocations.forEach((a: any) => {
        if (a && a.name) map[a.name] = { url: a.url, question: a.question, category: a.category };
      });
    }
    return map;
  }, [allocationHistory]);

  // Get colors based on the category passed as prop
  const getAssetColorForChart = useCallback(
    (assetName: string) => {
      const foundAssetIndex = allAssets.indexOf(assetName);
      if (foundAssetIndex !== -1) {
        return getAssetColor(assetName, foundAssetIndex, category as 'stock' | 'polymarket'); // Add type assertion here
      }
      return getCashColor();
    },
    [allAssets, category]
  );

  // This ensures the chart uses the same sorted and colored allocations
  const chartAllocations = useMemo(() => {
    return allAssets.map(item => ({ name: item, value: 1 })); // Simple value for legend
  }, [allAssets]);

  if (chartData.length === 0 || allAssets.length === 0) {
    return (
      <div style={{
        padding: '2rem',
        textAlign: 'center',
        background: '#1f2937',
        borderRadius: '0.5rem',
        margin: '1rem 0'
      }}>
        <div style={{ fontSize: '1rem', color: '#9ca3af' }}>No asset ratio history available.</div>
      </div>
    );
  }

  const chartHeight = 300;
  const chartWidth = 600;
  const margin = { top: 20, right: 80, bottom: 40, left: 50 };

  return (
    <div style={{ margin: '1rem 0' }}>
      <h3 style={{ color: '#ffffff', fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem', textAlign: 'center' }}>
        Asset Allocation History
      </h3>

      <div style={{ display: 'flex', justifyContent: 'center', overflowX: 'auto' }}>
        <svg width={chartWidth} height={chartHeight + margin.top + margin.bottom}>
          {/* Background and Y-Axis Grid */}
          <defs>
            <linearGradient id={`chartBackground-${chartId}`} x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#334155" stopOpacity="0.1" />
              <stop offset="100%" stopColor="#1e293b" stopOpacity="0.3" />
            </linearGradient>
          </defs>
          <rect x={margin.left} y={margin.top} width={chartWidth - margin.left - margin.right} height={chartHeight} fill={`url(#chartBackground-${chartId})`} rx="8" />
          {[0, 0.2, 0.4, 0.6, 0.8, 1.0].map((value, index) => {
            const y = margin.top + chartHeight - (value * chartHeight);
            return (
              <g key={index}>
                <line x1={margin.left} y1={y} x2={chartWidth - margin.right} y2={y} stroke={value === 0 ? "#475569" : "#374151"} strokeWidth={value === 0 ? "1.5" : "0.5"} strokeOpacity={value === 0 ? "0.8" : "0.3"} strokeDasharray={value === 0 ? "none" : "3,3"} />
                <text x={margin.left - 15} y={y + 4} fill="#d1d5db" fontSize="11" fontWeight="500" textAnchor="end">
                  {(value * 100).toFixed(0)}%
                </text>
              </g>
            );
          })}

          {/* Stacked Areas */}
          {allAssets.map((asset, assetIndex) => {
              const color = getAssetColorForChart(asset);

              let pathData;
              if (stackedData.length === 1) {
                const y_end = margin.top + chartHeight - (stackedData[0][asset + '_end'] * chartHeight);
                const y_start = margin.top + chartHeight - (stackedData[0][asset + '_start'] * chartHeight);
                const x_start = margin.left;
                const x_end = chartWidth - margin.right;
                pathData = `M ${x_start},${y_end} L ${x_end},${y_end} L ${x_end},${y_start} L ${x_start},${y_start} Z`;
              } else {
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

                  pathData = `M ${topPoints} L ${bottomPoints} Z`;
              }

              return (
                <g
                  key={asset}
                  onMouseMove={(e) => onMouseMove(e, `${asset}`)}
                  onMouseLeave={onMouseLeave}
                >
                  <path d={pathData} fill={color} strokeWidth="0" />
                </g>
              );
            })}

          {/* X-axis labels (using index) */}
          {chartData.map((_, index) => {
              // Show fewer labels if there are many data points
              if (chartData.length > 10 && index % Math.floor(chartData.length / 5) !== 0) {
                  return null;
              }
              const xRatio = chartData.length > 1 ? index / (chartData.length - 1) : 0.5;
              const x = margin.left + xRatio * (chartWidth - margin.left - margin.right);
              return (
                <text key={index} x={x} y={chartHeight + margin.top + 20} fill="#9ca3af" fontSize="10" textAnchor="middle">
                  {index + 1}
                </text>
              );
            })}
        </svg>
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', justifyContent: 'center', flexWrap: 'wrap', gap: '1rem', marginTop: '1rem' }}>
        {allAssets.map((asset, index) => {
          const meta = latestMeta[asset];
          const polymarketUrl = category === 'polymarket' ? meta?.url : undefined;
          const stockUrl = category === 'stock' && asset !== 'CASH' ? (meta?.url || `https://finance.yahoo.com/quote/${asset}`) : undefined;
          const linkUrl = polymarketUrl || stockUrl;
          const isLink = Boolean(linkUrl);

          return (
            <div key={asset} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{ width: '12px', height: '12px', backgroundColor: getAssetColorForChart(asset), borderRadius: '50%' }}></div>
              {isLink ? (
                <a
                  href={String(linkUrl)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="polymarket-link"
                  title={asset}
                >
                  {asset}
                </a>
              ) : (
                <span style={{ color: '#d1d5db', fontSize: '0.875rem', fontWeight: '500' }}>
                  {asset}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default memo(ModelsDisplay);
