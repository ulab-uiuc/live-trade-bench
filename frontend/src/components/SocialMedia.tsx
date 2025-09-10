import React, { useState, useMemo } from 'react';
import './SocialMedia.css';
import { getAssetColor } from '../utils/colors';


interface SocialMediaProps {
  socialData: {
    stock: any[];
    polymarket: any[];
  };
  lastRefresh: Date;
  isLoading: boolean;
}

const SocialMedia: React.FC<SocialMediaProps> = ({ socialData, lastRefresh, isLoading }) => {
  const [activeCategory, setActiveCategory] = useState<'stock' | 'polymarket'>('stock');

  const posts = useMemo(() => {
    const rawPosts = activeCategory === 'stock' ? socialData.stock : socialData.polymarket;
    return rawPosts.map((post: any, index: number) => ({
      ...post,
      id: post.id || `${activeCategory}-${index}`,
      sentiment: post.sentiment || 'neutral'
    }));
  }, [activeCategory, socialData]);

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment.toLowerCase()) {
      case 'bullish':
      case 'positive': return '#10b981';
      case 'bearish':
      case 'negative': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getTagColor = (tag: string | null) => {
    if (!tag) return '#6b7280';
    return getAssetColor(tag, activeCategory);
  };

  const formatTimeAgo = (timeString: string) => {
    try {
      const time = new Date(timeString);
      if (isNaN(time.getTime())) {
        return 'Unknown time';
      }

      const diff = new Date().getTime() - time.getTime();
      const hours = Math.floor(diff / (1000 * 60 * 60));

      if (hours < 1) return 'Just now';
      if (hours < 24) return `${hours}h ago`;
      return `${Math.floor(hours / 24)}d ago`;
    } catch (error) {
      return 'Unknown time';
    }
  };

  if (isLoading && posts.length === 0) {
    return (
      <div className="loading-indicator">
        <span>Loading social media feeds...</span>
      </div>
    );
  }

  return (
    <div className="social-media-container">
      <div className="social-media-header">
        <h1>Social Media</h1>
        <div className="social-media-controls">
          <div className="social-media-category-tabs">
            {(['stock', 'polymarket'] as const).map((market) => (
              <button
                key={market}
                onClick={() => setActiveCategory(market)}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '0.375rem',
                  border: 'none',
                  background: activeCategory === market ? '#6366f1' : 'transparent',
                  color: activeCategory === market ? '#ffffff' : '#d1d5db',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  fontSize: '0.875rem',
                  fontWeight: activeCategory === market ? 'bold' : 'normal'
                }}
              >
                {market === 'stock' ? 'Stock Market' : 'Polymarket'}
              </button>
            ))}
          </div>

          <div style={{
            fontSize: '0.875rem',
            color: '#9ca3af'
          }}>
            {posts.length} posts • Last updated: {lastRefresh.toLocaleTimeString()}
          </div>
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
        gap: '1.5rem'
      }}>
        {posts.map((post) => (
          <div
            key={post.id}
            style={{
              background: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '0.5rem',
              padding: '1.5rem',
              transition: 'all 0.2s ease',
              cursor: 'pointer'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = '#3b82f6';
              e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = '#374151';
              e.currentTarget.style.transform = 'translateY(0)';
            }}
            onClick={() => {
              if (post.url) {
                window.open(post.url, '_blank', 'noopener,noreferrer');
              }
            }}
          >
            {/* Post header */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              marginBottom: '1rem'
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                flexWrap: 'wrap'
              }}>
                {/* Stock Symbol Tags */}
                {post.stock_symbols && post.stock_symbols.length > 0 && (
                  post.stock_symbols.map((symbol: string, index: number) => (
                    <span key={index} style={{
                      background: '#3b82f6',
                      color: '#ffffff',
                      padding: '0.25rem 0.5rem',
                      borderRadius: '0.25rem',
                      fontSize: '0.75rem',
                      fontWeight: 'bold'
                    }}>
                      {symbol}
                    </span>
                  ))
                )}
                
                {/* Tag for Stock or Polymarket Question */}
                {post.tag && (
                  <span style={{
                    background: getTagColor(post.tag),
                    color: '#ffffff',
                    padding: '0.25rem 0.5rem',
                    borderRadius: '0.25rem',
                    fontSize: '0.75rem',
                    fontWeight: 'bold'
                  }}>
                    {post.tag}
                  </span>
                )}
                
                {/* Polymarket Question Tag */}
                {post.question && (
                  <span style={{
                    background: getTagColor(post.question),
                    color: '#ffffff',
                    padding: '0.25rem 0.5rem',
                    borderRadius: '0.25rem',
                    fontSize: '0.75rem',
                    fontWeight: 'bold',
                    maxWidth: '200px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    {post.question}
                  </span>
                )}
                
                <span style={{
                  background: getSentimentColor(post.sentiment),
                  color: '#ffffff',
                  padding: '0.25rem 0.5rem',
                  borderRadius: '0.25rem',
                  fontSize: '0.75rem',
                  fontWeight: 'bold',
                  textTransform: 'uppercase'
                }}>
                  {post.sentiment}
                </span>
              </div>

              <span style={{
                fontSize: '0.75rem',
                color: '#9ca3af'
              }}>
                {formatTimeAgo(post.time || post.created_at || '')}
              </span>
            </div>

            {/* Post content */}
            <p style={{
              fontSize: '0.875rem',
              color: '#d1d5db',
              lineHeight: '1.5',
              marginBottom: '1rem',
              maxHeight: '120px',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: '-webkit-box',
              WebkitLineClamp: 4,
              WebkitBoxOrient: 'vertical'
            }}>
              {post.content.length > 200 ? `${post.content.substring(0, 200)}...` : post.content}
            </p>

            {/* Post footer */}
            <div style={{
              display: 'flex',
              justifyContent: 'flex-start',
              alignItems: 'center',
              fontSize: '0.75rem',
              color: '#9ca3af'
            }}>
              <div style={{
                display: 'flex',
                gap: '1rem',
                alignItems: 'center'
              }}>
                <span>❤️ {post.likes || post.upvotes || 0}</span>
                <span>🔄 {post.retweets || 0}</span>
                <span>💬 {post.replies || 0}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SocialMedia;
