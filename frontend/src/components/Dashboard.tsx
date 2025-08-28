import React from 'react';

// 使用any类型避免接口冲突，但保持功能
const Dashboard: React.FC<any> = (props) => {
  console.log('🎯 Dashboard component is rendering!', props);

  // 安全地访问props
  const modelsData = props?.modelsData || [];
  const modelsLastRefresh = props?.modelsLastRefresh || new Date();

  // 分类模型数据
  const stockModels = modelsData.filter((model: any) => model?.category === 'stock');
  const polymarketModels = modelsData.filter((model: any) => model?.category === 'polymarket');

  return (
    <div style={{
      padding: '2rem',
      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%)',
      color: '#ffffff',
      minHeight: '100vh',
      fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
      fontSize: '16px',
      // 强制覆盖CSS问题
      position: 'relative',
      zIndex: 1000,
      overflow: 'visible',
      display: 'block'
    }}>
      {/* 主标题 */}
      <div style={{
        textAlign: 'center',
        marginBottom: '3rem',
        // 强制覆盖
        position: 'relative',
        zIndex: 1001,
        display: 'block'
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
          Overview Dashboard
        </h1>
        <p style={{
          color: '#94a3b8',
          fontSize: '1.125rem',
          margin: 0,
          fontWeight: '500'
        }}>
          Real-time portfolio performance and market insights
        </p>
      </div>

      {/* 统计信息卡片 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '1.5rem',
        marginBottom: '3rem',
        // 强制覆盖
        position: 'relative',
        zIndex: 1001,
        overflow: 'visible'
      }}>
        {/* Total Models */}
        <div style={{
          background: '#1f2937',
          border: '1px solid #374151',
          borderRadius: '0.5rem',
          padding: '1.5rem',
          textAlign: 'center',
          transition: 'all 0.2s ease',
          cursor: 'pointer'
        }}>
          <div style={{
            width: '48px',
            height: '48px',
            background: 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1rem auto',
            fontSize: '1.5rem'
          }}>
            📈
          </div>
          <p style={{ color: '#94a3b8', margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Total Models
          </p>
          <p style={{ color: '#ffffff', margin: 0, fontSize: '2.5rem', fontWeight: '800' }}>{modelsData.length}</p>
        </div>

        {/* Stock Models */}
        <div style={{
          background: '#1f2937',
          border: '1px solid #374151',
          borderRadius: '0.5rem',
          padding: '1.5rem',
          textAlign: 'center',
          transition: 'all 0.2s ease',
          cursor: 'pointer'
        }}>
          <div style={{
            width: '48px',
            height: '48px',
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1rem auto',
            fontSize: '1.5rem'
          }}>
            🚀
          </div>
          <p style={{ color: '#94a3b8', margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Stock Models
          </p>
          <p style={{ color: '#10b981', margin: 0, fontSize: '2.5rem', fontWeight: '800' }}>{stockModels.length}</p>
        </div>

        {/* Polymarket Models */}
        <div style={{
          background: '#1f2937',
          border: '1px solid #374151',
          borderRadius: '0.5rem',
          padding: '1.5rem',
          textAlign: 'center',
          transition: 'all 0.2s ease',
          cursor: 'pointer'
        }}>
          <div style={{
            width: '48px',
            height: '48px',
            background: 'linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%)',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1rem auto',
            fontSize: '1.5rem'
          }}>
            🎯
          </div>
          <p style={{ color: '#94a3b8', margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Polymarket Models
          </p>
          <p style={{ color: '#a78bfa', margin: 0, fontSize: '2.5rem', fontWeight: '800' }}>{polymarketModels.length}</p>
        </div>

        {/* Last Updated */}
        <div style={{
          background: '#1f2937',
          border: '1px solid #374151',
          borderRadius: '0.5rem',
          padding: '1.5rem',
          textAlign: 'center',
          transition: 'all 0.2s ease',
          cursor: 'pointer'
        }}>
          <div style={{
            width: '48px',
            height: '48px',
            background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1rem auto',
            fontSize: '1.5rem'
          }}>
            ⏰
          </div>
          <p style={{ color: '#94a3b8', margin: '0 0 0.5rem 0', fontSize: '0.875rem', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Last Updated
          </p>
          <p style={{ color: '#ffffff', margin: 0, fontSize: '1rem', fontWeight: '600' }}>{modelsLastRefresh.toLocaleString()}</p>
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
          background: '#1f2937',
          border: '1px solid #374151',
          borderRadius: '0.5rem',
          padding: '2rem',
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
              📈 Stock Models Performance
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
            <div style={{
              display: 'flex',
              alignItems: 'end',
              justifyContent: 'space-around',
              height: '250px',
              padding: '1rem 0'
            }}>
              {stockModels
                .sort((a: any, b: any) => (b?.performance || 0) - (a?.performance || 0))
                .slice(0, 5)
                .map((model: any, index: number) => {
                  const performance = model?.performance || 0;
                  const barHeight = Math.abs(performance) * 2;
                  const maxHeight = 180;
                  const height = Math.min(barHeight, maxHeight);

                  return (
                    <div key={model?.id || index} style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '0.75rem',
                      flex: 1,
                      maxWidth: '80px'
                    }}>
                      {/* 竖条 */}
                      <div style={{
                        width: '50px',
                        height: `${height}px`,
                        background: performance >= 0
                          ? 'linear-gradient(180deg, #10b981 0%, #059669 100%)'
                          : 'linear-gradient(180deg, #ef4444 0%, #dc2626 100%)',
                        borderRadius: '8px 8px 0 0',
                        position: 'relative',
                        display: 'flex',
                        alignItems: 'end',
                        justifyContent: 'center',
                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                        transition: 'all 0.2s ease'
                      }}>
                        {/* 数值标签 */}
                        <span style={{
                          position: 'absolute',
                          top: '-30px',
                          color: '#ffffff',
                          fontSize: '0.875rem',
                          fontWeight: '700',
                          background: performance >= 0
                            ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                            : 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                          padding: '4px 8px',
                          borderRadius: '6px',
                          whiteSpace: 'nowrap',
                          boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
                        }}>
                          {performance.toFixed(1)}%
                        </span>
                      </div>

                      {/* 模型名称 */}
                      <span style={{
                        color: '#ffffff',
                        fontSize: '0.875rem',
                        fontWeight: '600',
                        textAlign: 'center',
                        maxWidth: '100%',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        lineHeight: '1.2'
                      }}>
                        {model?.name || 'Unknown'}
                      </span>
                    </div>
                  );
                })}
            </div>
          )}
        </div>

        {/* Polymarket Models 竖条形图 */}
        <div style={{
          background: '#1f2937',
          border: '1px solid #374151',
          borderRadius: '0.5rem',
          padding: '2rem',
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
              📊 Polymarket Models Performance
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
            <div style={{
              display: 'flex',
              alignItems: 'end',
              justifyContent: 'space-around',
              height: '250px',
              padding: '1rem 0'
            }}>
              {polymarketModels
                .sort((a: any, b: any) => (b?.performance || 0) - (a?.performance || 0))
                .slice(0, 5)
                .map((model: any, index: number) => {
                  const performance = model?.performance || 0;
                  const barHeight = Math.abs(performance) * 2;
                  const maxHeight = 180;
                  const height = Math.min(barHeight, maxHeight);

                  return (
                    <div key={model?.id || index} style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '0.75rem',
                      flex: 1,
                      maxWidth: '80px'
                    }}>
                      {/* 竖条 */}
                      <div style={{
                        width: '50px',
                        height: `${height}px`,
                        background: performance >= 0
                          ? 'linear-gradient(180deg, #10b981 0%, #059669 100%)'
                          : 'linear-gradient(180deg, #ef4444 0%, #dc2626 100%)',
                        borderRadius: '8px 8px 0 0',
                        position: 'relative',
                        display: 'flex',
                        alignItems: 'end',
                        justifyContent: 'center',
                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                        transition: 'all 0.2s ease'
                      }}>
                        {/* 数值标签 */}
                        <span style={{
                          position: 'absolute',
                          top: '-30px',
                          color: '#ffffff',
                          fontSize: '0.875rem',
                          fontWeight: '700',
                          background: performance >= 0
                            ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                            : 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                          padding: '4px 8px',
                          borderRadius: '6px',
                          whiteSpace: 'nowrap',
                          boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
                        }}>
                          {performance.toFixed(1)}%
                        </span>
                      </div>

                      {/* 模型名称 */}
                      <span style={{
                        color: '#ffffff',
                        fontSize: '0.875rem',
                        fontWeight: '600',
                        textAlign: 'center',
                        maxWidth: '100%',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        lineHeight: '1.2'
                      }}>
                        {model?.name || 'Unknown'}
                      </span>
                    </div>
                  );
                })}
            </div>
          )}
        </div>
      </div>

    </div>
  );
};

export default Dashboard;
