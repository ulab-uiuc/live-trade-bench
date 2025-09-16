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
  // Format Polymarket asset names from "Question_YES" to "Question buy YES"
  const formatAssetName = useCallback((name: string, category: string) => {
    if (category === 'polymarket' && name.includes('_')) {
      const lastUnderscoreIndex = name.lastIndexOf('_');
      const question = name.substring(0, lastUnderscoreIndex);
      const outcome = name.substring(lastUnderscoreIndex + 1);
      return `${question} Buy ${outcome}`;
    }
    return name;
  }, []);
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'polymarket' | 'stock'>('all');
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [tooltip, setTooltip] = useState<TooltipInfo | null>(null);
  const [sortOrder, setSortOrder] = useState<'default' | 'performance-asc' | 'performance-desc'>('performance-desc');

  // Pre-warm the tooltip system to avoid first-hover delay
  useEffect(() => {
    // Initialize tooltip state immediately when modal opens
    if (showModal) {
      setTooltip(null);
    }
  }, [showModal]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (showModal) {
      // Store original overflow value
      const originalOverflow = document.body.style.overflow;
      // Disable body scroll
      document.body.style.overflow = 'hidden';

      // Cleanup function to restore original overflow
      return () => {
        document.body.style.overflow = originalOverflow;
      };
    }
  }, [showModal]);


  const showCategoryTabs = useMemo(() => {
    return stockModels.length > 0 && polymarketModels.length > 0;
  }, [stockModels.length, polymarketModels.length]);


  const filteredModels = useMemo(() => {
    let models;

    if (!showCategoryTabs) {
      models = modelsData;
    } else {
      switch (selectedCategory) {
        case 'stock': models = stockModels; break;
        case 'polymarket': models = polymarketModels; break;
        default: models = modelsData; break;
      }
    }

    const sortedModels = [...models].sort((a, b) => {
      if (sortOrder === 'performance-asc') {
        return a.performance - b.performance;
      } else if (sortOrder === 'performance-desc') {
        return b.performance - a.performance;
      }
      // Default: alphabetical order by name
      return a.name.localeCompare(b.name);
    });

    return sortedModels;
  }, [selectedCategory, stockModels, polymarketModels, modelsData, showCategoryTabs, sortOrder]);


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

    const { maxPerformance, minPerformance, range, pathData } = useMemo(() => {
      // Ensure data is an array before mapping
      const validData = chartData;
      const performances = validData.map(d => (d.profit / d.totalValue) * 100 || 0);

      const maxP = performances.length > 0 ? Math.max(...performances) : 0;
      const minP = performances.length > 0 ? Math.min(...performances) : 0;
      const r = maxP - minP || 10;

      let path;
      if (validData.length === 1) {
        // If only one point, draw a horizontal line across the chart
        const performance = (validData[0].profit / validData[0].totalValue) * 100 || 0;
        const y = padding + ((maxP - performance) / r) * (height - 2 * padding);
        path = `M ${padding},${y} L ${width - padding},${y}`;
      } else {
        path = validData.map((point, index) => {
          const performance = (point.profit / point.totalValue) * 100 || 0;
          const x = padding + (index / (validData.length - 1)) * (width - 2 * padding);
          const y = padding + ((maxP - performance) / r) * (height - 2 * padding);
          return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
        }).join(' ');
      }

      return { maxPerformance: maxP, minPerformance: minP, range: r, pathData: path };
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
      <div className="profit-chart" onMouseLeave={handleMouseLeave}>
        <h3>Profit History</h3>
        <svg width={width} height={height} className="chart-svg" onMouseLeave={handleMouseLeave}>
          {/*  */}
          <defs>
            <pattern id="grid" width="40" height="20" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 20" fill="none" stroke="#374151" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />

          {/*  */}
          {minPerformance < 0 && maxPerformance > 0 && (
            <line
              x1={padding}
              y1={padding + (maxPerformance / range) * (height - 2 * padding)}
              x2={width - padding}
              y2={padding + (maxPerformance / range) * (height - 2 * padding)}
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
            const performance = (point.profit / point.totalValue) * 100 || 0;
            const x = padding + (index / (chartData.length - 1)) * (width - 2 * padding);
            const y = padding + ((maxPerformance - performance) / range) * (height - 2 * padding);
            return (
              <circle
                key={index}
                cx={x}
                cy={y}
                r="4"
                fill={performance >= 0 ? '#10b981' : '#ef4444'}
                style={{ cursor: 'pointer' }}
                onMouseMove={(e) => {
                  const date = new Date(point.timestamp).toLocaleString('zh-CN', {
                    year: 'numeric', month: '2-digit', day: '2-digit',
                    hour: '2-digit', minute: '2-digit', hour12: false
                  }).replace(/\//g, '-').replace(',', '');
                  handleMouseMove(e, `Date: ${date} | Performance: ${performance.toFixed(2)}%`);
                }}
                onMouseLeave={handleMouseLeave}
              />
            );
          })}

          {/* Y */}
          <text x="10" y={padding} fill="#9ca3af" fontSize="12">{maxPerformance.toFixed(1)}%</text>
          <text x="10" y={height - padding + 5} fill="#9ca3af" fontSize="12">{minPerformance.toFixed(1)}%</text>
        </svg>

        {/*  */}
        <div className="chart-info">
          <div className="chart-stat">
            <span>Current Profit: </span>
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
      <div className="asset-allocation" onMouseLeave={handleMouseLeave}>
        <h3>Asset Allocation</h3>

        {/*  */}
        <div className="allocation-bar" onMouseLeave={handleMouseLeave}>
          {allocations.map((asset, index) => (
            <div
              key={asset.name}
              className="allocation-segment"
              style={{
                flex: `${asset.allocation} 1 0`,
                backgroundColor: asset.color,
                minWidth: '10px' // Ensure minimum clickable area
              }}
              onMouseMove={(e) => handleMouseMove(e, `${formatAssetName(asset.name, category)}: ${(asset.allocation * 100).toFixed(1)}%`)}
              onMouseLeave={handleMouseLeave}
            />
          ))}
        </div>

        {/*  */}
        <div className="allocation-legend">
          {allocations.map((asset) => {
            // Check if this is a Polymarket position with additional info
            const position = portfolioData?.positions?.[asset.name];
            const isPolymarket = category === 'polymarket' && position?.question;
            const linkUrl = position?.url;

            return (
              <div key={asset.name} className="legend-item">
                <div
                  className="legend-color"
                  style={{ backgroundColor: asset.color }}
                />
                <div className="legend-content">
                  {linkUrl ? (
                    <a
                      href={linkUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={category === 'stock' ? 'stock-link' : 'polymarket-link'}
                      title={asset.name}
                    >
                      {formatAssetName(asset.name, category)}
                    </a>
                  ) : (
                    <span className="legend-name">{formatAssetName(asset.name, category)}</span>
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
        <div className="header-controls">
          <select
            value={sortOrder}
            onChange={(e) => setSortOrder(e.target.value as 'default' | 'performance-asc' | 'performance-desc')}
            className="sort-control"
          >
            <option value="default">Name A-Z</option>
            <option value="performance-desc">Return Rate ↓</option>
            <option value="performance-asc">Return Rate ↑</option>
          </select>
          {/* Refresh button is now conditional */}
          {onRefresh && <button onClick={onRefresh} className="refresh-btn">🔄</button>}
        </div>
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
                        flex: `${asset.allocation} 1 0`,
                        backgroundColor: asset.color
                      }}
                      onMouseMove={(e) => handleMouseMove(e, `${formatAssetName(asset.name, model.category)}: ${(asset.allocation * 100).toFixed(1)}%`)}
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
        <div className="modal-overlay" onClick={closeModal} onMouseLeave={handleMouseLeave}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} onMouseLeave={handleMouseLeave}>
            <div className="modal-header">
              <h2>{selectedModel.name}</h2>
              <button className="modal-close" onClick={closeModal} aria-label="Close modal">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
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
                formatAssetName={formatAssetName}
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
                data={selectedModel.profitHistory}
                profit={selectedModel.profit}
                performance={selectedModel.performance}
                onMouseMove={handleMouseMove}
                onMouseLeave={handleMouseLeave}
              />

              {/* LLM Input/Output Section in Modal */}
              {(() => {
                const lastAllocation = selectedModel.allocationHistory && selectedModel.allocationHistory.length > 0
                  ? selectedModel.allocationHistory[selectedModel.allocationHistory.length - 1]
                  : null;

                if (lastAllocation && (lastAllocation.llm_input || lastAllocation.llm_output)) {
                  return (
                    <>
                      <div style={{
                        height: '1px',
                        background: 'linear-gradient(90deg, transparent 0%, #374151 50%, transparent 100%)',
                        margin: '2rem 0',
                        position: 'relative'
                      }}>
                      </div>
                      <LLMInputOutputSection
                        llmInput={lastAllocation.llm_input}
                        llmOutput={lastAllocation.llm_output}
                      />
                    </>
                  );
                }
                return null;
              })()}
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
  formatAssetName: (name: string, category: string) => string;
  onMouseMove: (e: React.MouseEvent, content: string) => void;
  onMouseLeave: () => void;
}> = ({ allocationHistory, portfolio, category, formatAssetName, onMouseMove, onMouseLeave }) => {

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
          if (a && a.name != null) obj[a.name] = a.ratio ?? 0;
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

  // Build a comprehensive meta map from portfolio positions and allocation history
  const assetMetaMap = useMemo(() => {
    const map: Record<string, { url?: string; question?: string }> = {};

    // First, get URLs from current portfolio positions
    if (portfolio?.positions) {
      Object.entries(portfolio.positions).forEach(([assetName, position]: [string, any]) => {
        if (position?.url) {
          map[assetName] = { url: position.url, question: position.question };
        }
      });
    }

    // Then, get URLs from allocation history (if format supports it)
    if (Array.isArray(allocationHistory)) {
      allocationHistory.forEach(snapshot => {
        // Try new allocations_array format first
        if (snapshot && Array.isArray(snapshot.allocations_array)) {
          snapshot.allocations_array.forEach((a: any) => {
            // Add to map if it has a URL, overwriting older entries is fine
            if (a && a.name && a.url) {
              map[a.name] = { url: a.url, question: a.question };
            }
          });
        }
        // Fallback to old allocations format (object)
        else if (snapshot && snapshot.allocations && typeof snapshot.allocations === 'object') {
          // For old format, we can't get URLs from allocation history
          // URLs will only come from current portfolio positions
        }
      });
    }

    return map;
  }, [allocationHistory, portfolio]);

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
        background: '#0f1419',
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
        <svg
          width={chartWidth}
          height={chartHeight + margin.top + margin.bottom}
          style={{
            shapeRendering: 'crispEdges',
            vectorEffect: 'non-scaling-stroke'
          }}
        >
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
                <path
                  d={pathData}
                  fill={color}
                  stroke={color}
                  strokeWidth="0.5"
                  shapeRendering="crispEdges"
                  vectorEffect="non-scaling-stroke"
                />
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
          const meta = assetMetaMap[asset];
          const linkUrl = meta?.url;

          return (
            <div key={asset} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{ width: '12px', height: '12px', backgroundColor: getAssetColorForChart(asset), borderRadius: '50%' }}></div>
              {linkUrl ? (
                <a
                  href={linkUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={category === 'stock' ? 'stock-link' : 'polymarket-link'}
                  title={asset}
                >
                  {formatAssetName(asset, category)}
                </a>
              ) : (
                <span style={{ color: '#d1d5db', fontSize: '0.875rem', fontWeight: '500' }}>
                  {formatAssetName(asset, category)}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

// LLM Input/Output Section Component
const LLMInputOutputSection: React.FC<{
  llmInput?: any;
  llmOutput?: any;
}> = ({ llmInput, llmOutput }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [inputExpanded, setInputExpanded] = useState(false);
  const [outputExpanded, setOutputExpanded] = useState(false);

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };

  const toggleInputExpanded = () => {
    setInputExpanded(!inputExpanded);
  };

  const toggleOutputExpanded = () => {
    setOutputExpanded(!outputExpanded);
  };

  return (
    <div className="llm-section">
      <div className="llm-header" onClick={toggleExpanded}>
        <h3 className="llm-label">LLM Input & Output</h3>
        <div className={`llm-arrow ${isExpanded ? 'expanded' : ''}`}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="6,9 12,15 18,9"></polyline>
          </svg>
        </div>
      </div>

      {isExpanded && (
        <div className="llm-content">
          {llmInput && (
            <div className="llm-input-section">
              <h4>Input</h4>
              <div className="llm-text-content">
                <div className="llm-meta">
                  <span>Model: {llmInput.model || 'N/A'}</span>
                  <span>Time: {llmInput.timestamp ? new Date(llmInput.timestamp).toLocaleString() : 'N/A'}</span>
                </div>
                <div className="llm-prompt">
                  {llmInput.prompt ? (
                    <>
                      {inputExpanded ? llmInput.prompt : llmInput.prompt.substring(0, 200) + (llmInput.prompt.length > 200 ? '...' : '')}
                      {llmInput.prompt.length > 200 && (
                        <button
                          className="llm-expand-btn"
                          onClick={toggleInputExpanded}
                          title={inputExpanded ? 'Show Less' : 'Show More'}
                        >
                          <svg
                            width="12"
                            height="12"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            className={`llm-expand-arrow ${inputExpanded ? 'expanded' : ''}`}
                          >
                            <polyline points="6,9 12,15 18,9"></polyline>
                          </svg>
                        </button>
                      )}
                    </>
                  ) : 'No prompt available'}
                </div>
              </div>
            </div>
          )}

          {llmOutput && (
            <div className="llm-output-section">
              <h4>Output</h4>
              <div className="llm-text-content">
                <div className="llm-meta">
                  <span>Success: {llmOutput.success ? 'Yes' : 'No'}</span>
                  <span>Time: {llmOutput.timestamp ? new Date(llmOutput.timestamp).toLocaleString() : 'N/A'}</span>
                </div>
                <div className="llm-response">
                  {llmOutput.content ? (
                    <>
                      {outputExpanded ? llmOutput.content : llmOutput.content.substring(0, 300) + (llmOutput.content.length > 300 ? '...' : '')}
                      {llmOutput.content.length > 300 && (
                        <button
                          className="llm-expand-btn"
                          onClick={toggleOutputExpanded}
                          title={outputExpanded ? 'Show Less' : 'Show More'}
                        >
                          <svg
                            width="12"
                            height="12"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            className={`llm-expand-arrow ${outputExpanded ? 'expanded' : ''}`}
                          >
                            <polyline points="6,9 12,15 18,9"></polyline>
                          </svg>
                        </button>
                      )}
                    </>
                  ) : 'No response available'}
                </div>
                {llmOutput.error && (
                  <div className="llm-error">
                    Error: {llmOutput.error}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default memo(ModelsDisplay);
