import React, { useState, useMemo } from 'react';
import './SocialMedia.css';

interface SocialPost {
  id: string;
  platform: string;
  username: string;
  displayName: string;
  content: string;
  time: string;
  likes: number;
  retweets: number;
  replies: number;
  sentiment: string;
  avatar: string;
}

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

  const posts = useMemo(() =>
    activeCategory === 'stock' ? socialData.stock : socialData.polymarket,
    [activeCategory, socialData]
  );

  const getPlatformColor = (platform: string) => {
    switch (platform.toLowerCase()) {
      case 'twitter': return '#1da1f2';
      case 'linkedin': return '#0077b5';
      case 'reddit': return '#ff4500';
      case 'discord': return '#7289da';
      case 'telegram': return '#0088cc';
      default: return '#6366f1';
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment.toLowerCase()) {
      case 'bullish':
      case 'positive': return '#10b981';
      case 'bearish':
      case 'negative': return '#ef4444';
      default: return '#6b7280';
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
        <h1>📱 Social Media Sentiment</h1>
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
              transition: 'all 0.2s ease'
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
                gap: '0.75rem'
              }}>
                <div style={{
                  fontSize: '1.5rem'
                }}>
                  {post.avatar}
                </div>
                <div>
                  <div style={{
                    fontSize: '0.875rem',
                    fontWeight: 'bold',
                    color: '#ffffff'
                  }}>
                    {post.displayName}
                  </div>
                  <div style={{
                    fontSize: '0.75rem',
                    color: '#9ca3af'
                  }}>
                    {post.username}
                  </div>
                </div>
              </div>

              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <span style={{
                  background: getPlatformColor(post.platform),
                  color: '#ffffff',
                  padding: '0.25rem 0.5rem',
                  borderRadius: '0.25rem',
                  fontSize: '0.75rem',
                  fontWeight: 'bold'
                }}>
                  {post.platform}
                </span>
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
            </div>

            {/* Post content */}
            <p style={{
              fontSize: '0.875rem',
              color: '#d1d5db',
              lineHeight: '1.5',
              marginBottom: '1rem'
            }}>
              {post.content}
            </p>

            {/* Post footer */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontSize: '0.75rem',
              color: '#9ca3af'
            }}>
              <div style={{
                display: 'flex',
                gap: '1rem'
              }}>
                <span>❤️ {post.likes}</span>
                <span>🔄 {post.retweets}</span>
                <span>💬 {post.replies}</span>
              </div>
              <span>{post.time}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SocialMedia;
