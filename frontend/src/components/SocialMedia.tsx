import React, { useState } from 'react';

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
    stock: SocialPost[];
    polymarket: SocialPost[];
  };
  lastRefresh: Date;
}

const SocialMedia: React.FC<SocialMediaProps> = ({ socialData, lastRefresh }) => {
  console.log('📱 Social Media component rendering with background data!');

  const [selectedMarket, setSelectedMarket] = useState<'all' | 'stock' | 'polymarket'>('all');

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

  const filteredPosts = selectedMarket === 'all'
    ? [...socialData.stock, ...socialData.polymarket]
    : socialData[selectedMarket];

  console.log(`📊 Displaying ${filteredPosts.length} social posts (${selectedMarket})`);

  // Show loading state if no data yet
  if (filteredPosts.length === 0) {
    return (
      <div
        style={{
          padding: '2rem',
          background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%)',
          color: '#ffffff',
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📱</div>
          <p style={{ fontSize: '1.125rem' }}>Loading social media in background...</p>
          <p style={{ fontSize: '0.875rem', opacity: 0.7 }}>
            Last updated: {lastRefresh.toLocaleTimeString()}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      padding: '2rem',
      background: '#1f2937',
      color: '#ffffff',
      minHeight: '100vh',
      fontFamily: 'Arial, sans-serif',
      fontSize: '16px',
      position: 'relative',
      zIndex: 1000,
      overflow: 'visible',
      display: 'block'
    }}>
      <div style={{
        marginBottom: '2rem',
        borderBottom: '1px solid #374151',
        paddingBottom: '1rem'
      }}>
        <h1 style={{
          fontSize: '2rem',
          fontWeight: 'bold',
          marginBottom: '1rem',
          background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text'
        }}>
          📱 Social Media Sentiment
        </h1>
        
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem'
        }}>
          <div style={{
            display: 'flex',
            gap: '0.5rem',
            background: '#374151',
            borderRadius: '0.5rem',
            padding: '0.25rem'
          }}>
            {(['all', 'stock', 'polymarket'] as const).map((market) => (
              <button
                key={market}
                onClick={() => setSelectedMarket(market)}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '0.375rem',
                  border: 'none',
                  background: selectedMarket === market ? '#6366f1' : 'transparent',
                  color: selectedMarket === market ? '#ffffff' : '#d1d5db',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  fontSize: '0.875rem',
                  fontWeight: selectedMarket === market ? 'bold' : 'normal'
                }}
              >
                {market === 'all' ? 'All Markets' : 
                 market === 'stock' ? 'Stock Market' : 'Polymarket'}
              </button>
            ))}
          </div>
          
          <div style={{
            fontSize: '0.875rem',
            color: '#9ca3af'
          }}>
            {filteredPosts.length} posts • Last updated: {lastRefresh.toLocaleTimeString()}
          </div>
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
        gap: '1.5rem'
      }}>
        {filteredPosts.map((post) => (
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