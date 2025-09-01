import React, { useEffect, useCallback } from 'react';

// 使用any类型避免接口冲突，但保持功能
const Dashboard: React.FC<any> = (props) => {
  console.log('🎯 Dashboard component is rendering!', props);

  // 安全地访问props
  const modelsData = props?.modelsData || [];
  const modelsLastRefresh = props?.modelsLastRefresh || new Date();
  const setModelsData = props?.setModelsData;
  const setModelsLastRefresh = props?.setModelsLastRefresh;

  // Fetch all models data from backend
  const fetchModelsData = useCallback(async () => {
    try {
      const response = await fetch('/api/models/');
      if (response.ok) {
        const allModels = await response.json();
        if (setModelsData) {
          setModelsData(allModels);
        }
        if (setModelsLastRefresh) {
          setModelsLastRefresh(new Date());
        }
      }
    } catch (error) {
      console.error('Error fetching models data:', error);
    }
  }, [setModelsData, setModelsLastRefresh]);

  // Fetch data on component mount
  useEffect(() => {
    fetchModelsData();
  }, [fetchModelsData]);

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
              Stock Models Leaderboard
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
            <div style={{ padding: '1rem 0' }}>
              {/* 现代化柱状图容器 */}
              <div style={{ 
                padding: '2rem 1rem'
              }}>
                {/* 网格和柱状图 */}
                <div style={{ position: 'relative', height: '280px', marginBottom: '1rem' }}>
                  {/* Y轴网格线 */}
                  {[0, 25, 50, 75, 100].map(value => (
                    <div key={value} style={{
                      position: 'absolute',
                      left: '40px',
                      right: '20px',
                      top: `${260 - (value * 2.2)}px`,
                      height: '1px',
                      background: value === 0 ? '#64748b' : 'rgba(148, 163, 184, 0.15)',
                      borderTop: value === 0 ? '2px solid #64748b' : '1px dashed rgba(148, 163, 184, 0.1)'
                    }}>
                      <span style={{
                        position: 'absolute',
                        left: '-35px',
                        top: '-8px',
                        fontSize: '0.75rem',
                        color: '#94a3b8',
                        fontWeight: '500'
                      }}>{value}%</span>
                    </div>
                  ))}
                  
                  {/* 柱状图 */}
                  <div style={{ 
                    position: 'absolute',
                    bottom: '0',
                    left: '50px',
                    right: '30px',
                    height: '100%',
                    display: 'flex', 
                    alignItems: 'end', 
                    justifyContent: 'space-around',
                    gap: '0.5rem'
                  }}>
                    {stockModels
                      .sort((a: any, b: any) => (b?.performance || 0) - (a?.performance || 0))
                      .slice(0, 5)
                      .map((model: any, index: number) => {
                        const performance = model?.performance || 0;
                        const height = Math.max(Math.abs(performance) * 2.2, 8);
                        const isPositive = performance >= 0;
                        
                        return (
                          <div key={model?.id || index} style={{ 
                            flex: 1, 
                            maxWidth: '70px',
                            display: 'flex', 
                            flexDirection: 'column', 
                            alignItems: 'center'
                          }}>
                            {/* 柱子 */}
                            <div style={{
                              width: '100%',
                              height: `${height}px`,
                              background: isPositive 
                                ? 'linear-gradient(180deg, #34d399 0%, #10b981 50%, #059669 100%)'
                                : 'linear-gradient(180deg, #f87171 0%, #ef4444 50%, #dc2626 100%)',
                              borderRadius: '8px 8px 4px 4px',
                              position: 'relative',
                              boxShadow: isPositive 
                                ? '0 6px 20px rgba(16, 185, 129, 0.4)'
                                : '0 6px 20px rgba(239, 68, 68, 0.4)',
                              transition: 'all 0.3s ease',
                              cursor: 'pointer'
                            }}>
                              {/* 光泽效果 */}
                              <div style={{
                                position: 'absolute',
                                top: '0',
                                left: '0',
                                right: '0',
                                height: '30%',
                                background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.25) 0%, transparent 100%)',
                                borderRadius: '8px 8px 0 0'
                              }}/>
                              
                              {/* 数值标签 */}
                              <div style={{
                                position: 'absolute',
                                top: '-40px',
                                left: '50%',
                                transform: 'translateX(-50%)',
                                background: isPositive 
                                  ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                                  : 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                                color: '#ffffff',
                                padding: '4px 10px',
                                borderRadius: '16px',
                                fontSize: '0.75rem',
                                fontWeight: '700',
                                whiteSpace: 'nowrap',
                                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.25)',
                                border: '1px solid rgba(255, 255, 255, 0.2)'
                              }}>
                                {isPositive ? '+' : ''}{performance.toFixed(1)}%
                              </div>
                            </div>
                            
                            {/* 模型名称 */}
                            <div style={{
                              marginTop: '0.75rem',
                              padding: '0rem 0.5rem'
                            }}>
                              <span style={{ 
                                color: '#ffffff', 
                                fontSize: '0.6rem', 
                                fontWeight: '600',
                                textAlign: 'center',
                                display: 'block',
                                maxWidth: '100%',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap'
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
            <div style={{ padding: '1rem 0' }}>
              {/* 现代化柱状图容器 */}
              <div style={{ 
                padding: '2rem 1rem'
              }}>
                {/* 网格和柱状图 */}
                <div style={{ position: 'relative', height: '280px', marginBottom: '1rem' }}>
                  {/* Y轴网格线 */}
                  {[0, 25, 50, 75, 100].map(value => (
                    <div key={value} style={{
                      position: 'absolute',
                      left: '40px',
                      right: '20px',
                      top: `${260 - (value * 2.2)}px`,
                      height: '1px',
                      background: value === 0 ? '#8b5cf6' : 'rgba(167, 139, 250, 0.15)',
                      borderTop: value === 0 ? '2px solid #8b5cf6' : '1px dashed rgba(167, 139, 250, 0.1)'
                    }}>
                      <span style={{
                        position: 'absolute',
                        left: '-35px',
                        top: '-8px',
                        fontSize: '0.75rem',
                        color: '#c4b5fd',
                        fontWeight: '500'
                      }}>{value}%</span>
                    </div>
                  ))}
                  
                  {/* 柱状图 */}
                  <div style={{ 
                    position: 'absolute',
                    bottom: '0',
                    left: '50px',
                    right: '30px',
                    height: '100%',
                    display: 'flex', 
                    alignItems: 'end', 
                    justifyContent: 'space-around',
                    gap: '0.5rem'
                  }}>
                    {polymarketModels
                      .sort((a: any, b: any) => (b?.performance || 0) - (a?.performance || 0))
                      .slice(0, 5)
                      .map((model: any, index: number) => {
                        const performance = model?.performance || 0;
                        const height = Math.max(Math.abs(performance) * 2.2, 8);
                        const isPositive = performance >= 0;
                        
                        return (
                          <div key={model?.id || index} style={{ 
                            flex: 1, 
                            maxWidth: '70px',
                            display: 'flex', 
                            flexDirection: 'column', 
                            alignItems: 'center'
                          }}>
                            {/* 柱子 */}
                            <div style={{
                              width: '100%',
                              height: `${height}px`,
                              background: isPositive 
                                ? 'linear-gradient(180deg, #c4b5fd 0%, #a78bfa 50%, #8b5cf6 100%)'
                                : 'linear-gradient(180deg, #f87171 0%, #ef4444 50%, #dc2626 100%)',
                              borderRadius: '8px 8px 4px 4px',
                              position: 'relative',
                              boxShadow: isPositive 
                                ? '0 6px 20px rgba(139, 92, 246, 0.5)'
                                : '0 6px 20px rgba(239, 68, 68, 0.4)',
                              transition: 'all 0.3s ease',
                              cursor: 'pointer'
                            }}>
                              {/* 光泽效果 */}
                              <div style={{
                                position: 'absolute',
                                top: '0',
                                left: '0',
                                right: '0',
                                height: '30%',
                                background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.3) 0%, transparent 100%)',
                                borderRadius: '8px 8px 0 0'
                              }}/>
                              
                              {/* 数值标签 */}
                              <div style={{
                                position: 'absolute',
                                top: '-40px',
                                left: '50%',
                                transform: 'translateX(-50%)',
                                background: isPositive 
                                  ? 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)'
                                  : 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                                color: '#ffffff',
                                padding: '4px 10px',
                                borderRadius: '16px',
                                fontSize: '0.75rem',
                                fontWeight: '700',
                                whiteSpace: 'nowrap',
                                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.25)',
                                border: '1px solid rgba(255, 255, 255, 0.2)'
                              }}>
                                {isPositive ? '+' : ''}{performance.toFixed(1)}%
                              </div>
                            </div>
                            
                            {/* 模型名称 */}
                            <div style={{
                              marginTop: '0.75rem',
                              padding: '0rem 0.5rem'
                            }}>
                              <span style={{ 
                                color: '#ffffff', 
                                fontSize: '0.6rem', 
                                fontWeight: '600',
                                textAlign: 'center',
                                display: 'block',
                                maxWidth: '100%',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap'
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
          )}
        </div>
      </div>

    </div>
  );
};

export default Dashboard;
