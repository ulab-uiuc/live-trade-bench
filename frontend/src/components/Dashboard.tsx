import React, { useEffect, useCallback } from 'react';

interface DashboardProps {
  modelsData: any[];
  modelsLastRefresh: Date;
  systemStatus: any;
  systemLastRefresh: Date;
}

const Dashboard: React.FC<DashboardProps> = ({
  modelsData,
  modelsLastRefresh,
  systemStatus,
  systemLastRefresh
}) => {
  console.log('📊 Dashboard rendering with background data!');

  // 分类模型数据
  const stockModels = modelsData.filter((model: any) => model?.category === 'stock');
  const polymarketModels = modelsData.filter((model: any) => model?.category === 'polymarket');

  return (
    <div style={{
      padding: '2rem',
      color: '#ffffff',
      fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
      fontSize: '16px',
      position: 'relative' // Needed for z-index context
    }}>
      {/* 主标题 */}
      <div style={{
        textAlign: 'center',
        marginBottom: '3rem',
        position: 'relative',
        zIndex: 1 // Ensure title is below navigation
      }}>
        <h1 style={{
          color: '#ffffff',
          fontSize: '3.5rem',
          marginBottom: '1rem',
          fontWeight: '800',
          background: 'linear-gradient(135deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          textShadow: '0 4px 8px rgba(0,0,0,0.3)',
          letterSpacing: '-0.025em'
        }}>
          Leaderboard
        </h1>
        <p style={{
          color: '#94a3b8',
          fontSize: '1.125rem',
          margin: 0,
          fontWeight: '500'
        }}>
          Real-time leaderboard on LLM-based stock and polymarket porfolio management
        </p>
      </div>

      {/* 统计信息卡片 - 无边框版本 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '1.5rem',
        marginBottom: '3rem',
        position: 'relative',
        zIndex: 1001,
        overflow: 'visible'
      }}>
        {/* Total Models */}
        <div style={{
          padding: '1.5rem',
          textAlign: 'center'
        }}>
          <div style={{
            width: '200px',
            height: '48px',
            background: 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1rem auto',
            fontSize: '0.875rem',
            fontWeight: '600',
            color: '#ffffff'
          }}>
            TOTAL MODELS
          </div>
          <p style={{ color: '#ffffff', margin: 0, fontSize: '2.5rem', fontWeight: '800' }}>{modelsData.length}</p>
        </div>

        {/* Stock Models */}
        <div style={{
          padding: '1.5rem',
          textAlign: 'center'
        }}>
          <div style={{
            width: '200px',
            height: '48px',
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1rem auto',
            fontSize: '0.875rem',
            fontWeight: '600',
            color: '#ffffff'
          }}>
            STOCK MODELS
          </div>
          <p style={{ color: '#10b981', margin: 0, fontSize: '2.5rem', fontWeight: '800' }}>{stockModels.length}</p>
        </div>

        {/* Polymarket Models */}
        <div style={{
          padding: '1.5rem',
          textAlign: 'center'
        }}>
          <div style={{
            width: '200px',
            height: '48px',
            background: 'linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%)',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1rem auto',
            fontSize: '0.875rem',
            fontWeight: '600',
            color: '#ffffff'
          }}>
            POLYMARKET MODELS
          </div>
          <p style={{ color: '#a78bfa', margin: 0, fontSize: '2.5rem', fontWeight: '800' }}>{polymarketModels.length}</p>
        </div>

        {/* Last Updated */}
        <div style={{
          padding: '1.5rem',
          textAlign: 'center'
        }}>
          <div style={{
            width: '200px',
            height: '48px',
            background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1.5rem auto',
            fontSize: '0.875rem',
            fontWeight: '600',
            color: '#ffffff'
          }}>
            LAST UPDATED
          </div>
                      <p style={{
              color: '#f59e0b',
              margin: '0 0 0.5rem 0',
              fontSize: '2.5rem',
              fontWeight: '800',
              fontFamily: 'monospace',
              letterSpacing: '-0.025em',
              lineHeight: '1'
            }}>
              {new Date(modelsLastRefresh).toLocaleString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
              })}
            </p>
            <p style={{
              color: '#94a3b8',
              margin: '0.25rem 0 0 0',
              fontSize: '0.75rem',
              fontWeight: '500',
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            }}>
              {new Date(modelsLastRefresh).toLocaleDateString('en-US', {
                month: 'short',
                day: '2-digit'
              })}
            </p>
        </div>
      </div>

      {/* 两个竖条形图区域 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '2rem',
        marginBottom: '2rem',
        // 强制覆盖
        position: 'relative',
        zIndex: 1001,
        overflow: 'visible'
      }}>
        {/* Stock Models 竖条形图 */}
        <div style={{
          // 强制覆盖
          position: 'relative',
          zIndex: 1001,
          overflow: 'visible'
        }}>
          <h2 style={{
            color: '#ffffff',
            fontSize: '1.75rem',
            marginBottom: '2rem',
            textAlign: 'center',
            fontWeight: '700',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem'
          }}>
            <span style={{
              background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>
              Stock Model Leaderboard
            </span>
          </h2>

          {stockModels.length === 0 ? (
            <div style={{
              textAlign: 'center',
              padding: '3rem 1rem',
              color: '#94a3b8'
            }}>
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📊</div>
              <p style={{ margin: 0, fontSize: '1.125rem', fontWeight: '500' }}>No stock models available</p>
            </div>
          ) : (
            (() => {
              const stockPerformances = stockModels.map((m: any) => m?.performance || 0);
              const maxStockPerf = Math.ceil(Math.max(...stockPerformances.map(Math.abs), 25) / 5) * 5;

              return (
                <div style={{ padding: '1rem 0' }}>
                  <div style={{ padding: '2rem 1rem' }}>
                    <div style={{ position: 'relative', height: '320px', marginBottom: '1rem' }}>
                      {/* Y轴网格线 - centered */}
                      {[maxStockPerf, maxStockPerf / 2, 0, -maxStockPerf / 2, -maxStockPerf].map(value => {
                        const topPercentage = 50 - (value / maxStockPerf) * 50;
                        return (
                          <div key={value} style={{
                            position: 'absolute',
                            left: '40px',
                            right: '20px',
                            top: `${topPercentage}%`,
                            height: '1px',
                            background: value === 0 ? '#64748b' : 'rgba(148, 163, 184, 0.15)',
                            borderTop: value === 0 ? '2px solid #64748b' : '1px dashed rgba(148, 163, 184, 0.1)',
                            transform: 'translateY(-50%)'
                          }}>
                            <span style={{
                              position: 'absolute',
                              left: '-40px',
                              top: '-8px',
                              fontSize: '0.75rem',
                              color: '#94a3b8',
                              fontWeight: '500'
                            }}>{value.toFixed(0)}%</span>
                          </div>
                        );
                      })}

                      {/* 柱状图 */}
                      <div style={{
                        position: 'absolute',
                        top: 0,
                        bottom: 0,
                        left: '50px',
                        right: '30px',
                        display: 'flex',
                        justifyContent: 'space-around',
                        gap: '0.3rem'
                      }}>
                        {stockModels
                          .sort((a: any, b: any) => (b?.performance || 0) - (a?.performance || 0))
                          .map((model: any, index: number) => {
                            const performance = model?.performance || 0;
                            const isPositive = performance >= 0;
                            const barHeight = Math.min((Math.abs(performance) / maxStockPerf) * 150, 150);

                            return (
                              <div key={model?.id || index} style={{
                                flex: 1,
                                maxWidth: '80px',
                                position: 'relative',
                                display: 'flex',
                                flexDirection: 'column',
                                justifyContent: 'flex-end'
                              }}>
                                {/* Performance Label */}
                                <div style={{
                                  position: 'absolute',
                                  left: '50%',
                                  transform: 'translateX(-50%)',
                                  ...(isPositive
                                    ? { bottom: `calc(50% + ${barHeight}px + 5px)` }
                                    : { top: `calc(50% + ${barHeight}px + 5px)` }),
                                  color: isPositive ? '#10b981' : '#ef4444',
                                  fontSize: '0.75rem',
                                  fontWeight: '700',
                                  whiteSpace: 'nowrap',
                                }}>
                                  {isPositive ? '+' : ''}{performance.toFixed(1)}%
                                </div>

                                {/* Bar */}
                                <div style={{
                                  position: 'absolute',
                                  left: '10%',
                                  right: '10%',
                                  ...(isPositive
                                    ? { bottom: '50%', height: `${barHeight}px` }
                                    : { top: '50%', height: `${barHeight}px` }),
                                  background: isPositive ? '#10b981' : '#ef4444',
                                  transition: 'all 0.3s ease',
                                  cursor: 'pointer'
                                }}>
                                </div>

                                {/* 模型名称和排名 */}
                                <div style={{
                                  height: '40px', // Reserve space at the bottom
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                }}>
                                  <span style={{
                                    color: '#ffffff',
                                    fontSize: '0.6rem',
                                    fontWeight: '600',
                                    textAlign: 'center',
                                    wordBreak: 'break-word',
                                  }}>
                                    {model?.name || 'Unknown'}
                                  </span>
                                </div>
                              </div>
                            );
                          })}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })()
          )}
        </div>

        {/* Polymarket Models 竖条形图 */}
        <div style={{
          // 强制覆盖
          position: 'relative',
          zIndex: 1001,
          overflow: 'visible'
        }}>
          <h2 style={{
            color: '#ffffff',
            fontSize: '1.75rem',
            marginBottom: '2rem',
            textAlign: 'center',
            fontWeight: '700',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem'
          }}>
            <span style={{
              background: 'linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>
              Polymarket Model Leaderboard
            </span>
          </h2>

          {polymarketModels.length === 0 ? (
            <div style={{
              textAlign: 'center',
              padding: '3rem 1rem',
              color: '#94a3b8'
            }}>
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🎯</div>
              <p style={{ margin: 0, fontSize: '1.125rem', fontWeight: '500' }}>No polymarket models available</p>
            </div>
          ) : (
            (() => {
              const polyPerformances = polymarketModels.map((m: any) => m?.performance || 0);
              const maxPolyPerf = Math.ceil(Math.max(...polyPerformances.map(Math.abs), 25) / 5) * 5;

              return (
                <div style={{ padding: '1rem 0' }}>
                  <div style={{ padding: '2rem 1rem' }}>
                    <div style={{ position: 'relative', height: '320px', marginBottom: '1rem' }}>
                      {/* Y轴网格线 - centered */}
                      {[maxPolyPerf, maxPolyPerf / 2, 0, -maxPolyPerf / 2, -maxPolyPerf].map(value => {
                        const topPercentage = 50 - (value / maxPolyPerf) * 50;
                        return (
                          <div key={value} style={{
                            position: 'absolute',
                            left: '40px',
                            right: '20px',
                            top: `${topPercentage}%`,
                            height: '1px',
                            background: value === 0 ? '#8b5cf6' : 'rgba(167, 139, 250, 0.15)',
                            borderTop: value === 0 ? '2px solid #8b5cf6' : '1px dashed rgba(167, 139, 250, 0.1)',
                            transform: 'translateY(-50%)'
                          }}>
                            <span style={{
                              position: 'absolute',
                              left: '-40px',
                              top: '-8px',
                              fontSize: '0.75rem',
                              color: '#c4b5fd',
                              fontWeight: '500'
                            }}>{value.toFixed(0)}%</span>
                          </div>
                        );
                      })}

                      {/* 柱状图 */}
                      <div style={{
                        position: 'absolute',
                        top: 0,
                        bottom: 0,
                        left: '50px',
                        right: '30px',
                        display: 'flex',
                        justifyContent: 'space-around',
                        gap: '0.3rem'
                      }}>
                        {polymarketModels
                          .sort((a: any, b: any) => (b?.performance || 0) - (a?.performance || 0))
                          .map((model: any, index: number) => {
                            const performance = model?.performance || 0;
                            const isPositive = performance >= 0;
                            const barHeight = Math.min((Math.abs(performance) / maxPolyPerf) * 150, 150);

                            return (
                              <div key={model?.id || index} style={{
                                flex: 1,
                                maxWidth: '80px',
                                position: 'relative',
                                display: 'flex',
                                flexDirection: 'column',
                                justifyContent: 'flex-end'
                              }}>
                                {/* Performance Label */}
                                <div style={{
                                  position: 'absolute',
                                  left: '50%',
                                  transform: 'translateX(-50%)',
                                  ...(isPositive
                                    ? { bottom: `calc(50% + ${barHeight}px + 5px)` }
                                    : { top: `calc(50% + ${barHeight}px + 5px)` }),
                                  color: isPositive ? '#a78bfa' : '#ef4444',
                                  fontSize: '0.75rem',
                                  fontWeight: '700',
                                  whiteSpace: 'nowrap',
                                }}>
                                  {isPositive ? '+' : ''}{performance.toFixed(1)}%
                                </div>

                                {/* Bar */}
                                <div style={{
                                  position: 'absolute',
                                  left: '10%',
                                  right: '10%',
                                  ...(isPositive
                                    ? { bottom: '50%', height: `${barHeight}px` }
                                    : { top: '50%', height: `${barHeight}px` }),
                                  background: isPositive ? '#a78bfa' : '#ef4444',
                                  transition: 'all 0.3s ease',
                                  cursor: 'pointer'
                                }}>
                                </div>

                                {/* 模型名称和排名 */}
                                <div style={{
                                  height: '40px', // Reserve space at the bottom
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                }}>
                                  <span style={{
                                    color: '#ffffff',
                                    fontSize: '0.6rem',
                                    fontWeight: '600',
                                    textAlign: 'center',
                                    wordBreak: 'break-word',
                                  }}>
                                    {model?.name || 'Unknown'}
                                  </span>
                                </div>
                              </div>
                            );
                          })}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })()
          )}
        </div>
      </div>

    </div>
  );
};

export default Dashboard;
