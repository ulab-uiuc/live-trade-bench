import React, { useState, useEffect } from 'react';

interface SocialPost {
  id: string;
  platform: 'reddit' | 'twitter' | 'discord' | 'telegram';
  author: string;
  content: string;
  title?: string;
  postedAt: Date;
  engagement: {
    upvotes?: number;
    downvotes?: number;
    likes?: number;
    retweets?: number;
    comments?: number;
    shares?: number;
  };
  sentiment: 'positive' | 'negative' | 'neutral';
  category: 'market' | 'stock' | 'crypto' | 'options' | 'polymarket';
  ticker?: string;
  url?: string;
  subreddit?: string;
  hashtags?: string[];
}

const SocialMedia: React.FC = () => {
  const [posts, setPosts] = useState<SocialPost[]>([]);
  const [loading, setLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [selectedPlatform, setSelectedPlatform] = useState<'all' | 'reddit' | 'twitter' | 'discord' | 'telegram'>('all');
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'market' | 'stock' | 'crypto' | 'options' | 'polymarket'>('all');

  const fetchSocialPosts = async () => {
    setLoading(true);
    try {
      // Fetch from backend API
      const response = await fetch('http://localhost:8000/api/social/');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      // Transform backend data to frontend format
      const transformedPosts: SocialPost[] = data.map((post: any) => ({
        id: post.id,
        platform: post.platform,
        author: post.author,
        content: post.content,
        title: post.title,
        postedAt: new Date(post.posted_at),
        engagement: {
          upvotes: post.upvotes,
          downvotes: post.downvotes,
          likes: post.likes,
          retweets: post.retweets,
          comments: post.comments,
          shares: post.shares
        },
        sentiment: post.sentiment,
        category: post.category,
        ticker: post.ticker,
        url: post.url,
        subreddit: post.subreddit,
        hashtags: post.hashtags
      }));
      
      setPosts(transformedPosts);
      setLastRefresh(new Date());
    } catch (error) {
      console.error('Error fetching social posts:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSocialPosts();

    // Auto-refresh every 30 minutes
    const interval = setInterval(fetchSocialPosts, 30 * 60 * 1000);

    return () => clearInterval(interval);
  }, []);

  const getPlatformColor = (platform: string) => {
    switch (platform) {
      case 'reddit': return '#ff4500';
      case 'twitter': return '#1da1f2';
      case 'discord': return '#7289da';
      case 'telegram': return '#0088cc';
      default: return '#6c757d';
    }
  };

  const getPlatformIcon = (platform: string) => {
    switch (platform) {
      case 'reddit': return '🔴';
      case 'twitter': return '🐦';
      case 'discord': return '💬';
      case 'telegram': return '📱';
      default: return '📄';
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return '#28a745';
      case 'negative': return '#dc3545';
      case 'neutral': return '#6c757d';
      default: return '#6c757d';
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'market': return '#007bff';
      case 'stock': return '#28a745';
      case 'crypto': return '#ffc107';
      case 'options': return '#fd7e14';
      case 'polymarket': return '#6f42c1';
      default: return '#6c757d';
    }
  };

  const formatTimeAgo = (date: Date) => {
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));

    if (diffInMinutes < 60) {
      return `${diffInMinutes}m ago`;
    } else if (diffInMinutes < 1440) {
      return `${Math.floor(diffInMinutes / 60)}h ago`;
    } else {
      return `${Math.floor(diffInMinutes / 1440)}d ago`;
    }
  };

  const getTotalEngagement = (engagement: any) => {
    return (engagement.upvotes || 0) + (engagement.likes || 0) + 
           (engagement.retweets || 0) + (engagement.comments || 0) + 
           (engagement.shares || 0) - (engagement.downvotes || 0);
  };

  const filteredPosts = posts.filter(post => {
    const platformMatch = selectedPlatform === 'all' || post.platform === selectedPlatform;
    const categoryMatch = selectedCategory === 'all' || post.category === selectedCategory;
    return platformMatch && categoryMatch;
  });

  const platformStats = {
    reddit: posts.filter(p => p.platform === 'reddit').length,
    twitter: posts.filter(p => p.platform === 'twitter').length,
    discord: posts.filter(p => p.platform === 'discord').length,
    telegram: posts.filter(p => p.platform === 'telegram').length,
    total: posts.length
  };

  const categoryStats = {
    market: posts.filter(p => p.category === 'market').length,
    stock: posts.filter(p => p.category === 'stock').length,
    crypto: posts.filter(p => p.category === 'crypto').length,
    options: posts.filter(p => p.category === 'options').length,
    polymarket: posts.filter(p => p.category === 'polymarket').length,
    total: posts.length
  };

  return (
    <div className="social-media-page">
      <div className="refresh-indicator">
        <h1>Market Social Media</h1>
        {loading && <div className="spinner"></div>}
        <span style={{ marginLeft: 'auto', fontSize: '0.875rem', color: '#666' }}>
          Last updated: {lastRefresh.toLocaleTimeString()}
        </span>
      </div>

      {/* Platform Filter */}
      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ marginBottom: '10px', fontSize: '1rem', color: '#333' }}>Platforms</h3>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button
            onClick={() => setSelectedPlatform('all')}
            style={{
              padding: '8px 16px',
              border: '1px solid #ddd',
              borderRadius: '20px',
              background: selectedPlatform === 'all' ? '#007bff' : 'white',
              color: selectedPlatform === 'all' ? 'white' : '#333',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            All ({platformStats.total})
          </button>
          <button
            onClick={() => setSelectedPlatform('reddit')}
            style={{
              padding: '8px 16px',
              border: '1px solid #ff4500',
              borderRadius: '20px',
              background: selectedPlatform === 'reddit' ? '#ff4500' : 'white',
              color: selectedPlatform === 'reddit' ? 'white' : '#ff4500',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            🔴 Reddit ({platformStats.reddit})
          </button>
          <button
            onClick={() => setSelectedPlatform('twitter')}
            style={{
              padding: '8px 16px',
              border: '1px solid #1da1f2',
              borderRadius: '20px',
              background: selectedPlatform === 'twitter' ? '#1da1f2' : 'white',
              color: selectedPlatform === 'twitter' ? 'white' : '#1da1f2',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            🐦 Twitter ({platformStats.twitter})
          </button>
          <button
            onClick={() => setSelectedPlatform('discord')}
            style={{
              padding: '8px 16px',
              border: '1px solid #7289da',
              borderRadius: '20px',
              background: selectedPlatform === 'discord' ? '#7289da' : 'white',
              color: selectedPlatform === 'discord' ? 'white' : '#7289da',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            💬 Discord ({platformStats.discord})
          </button>
          <button
            onClick={() => setSelectedPlatform('telegram')}
            style={{
              padding: '8px 16px',
              border: '1px solid #0088cc',
              borderRadius: '20px',
              background: selectedPlatform === 'telegram' ? '#0088cc' : 'white',
              color: selectedPlatform === 'telegram' ? 'white' : '#0088cc',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            📱 Telegram ({platformStats.telegram})
          </button>
        </div>
      </div>

      {/* Category Filter */}
      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ marginBottom: '10px', fontSize: '1rem', color: '#333' }}>Categories</h3>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button
            onClick={() => setSelectedCategory('all')}
            style={{
              padding: '8px 16px',
              border: '1px solid #ddd',
              borderRadius: '20px',
              background: selectedCategory === 'all' ? '#007bff' : 'white',
              color: selectedCategory === 'all' ? 'white' : '#333',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            All ({categoryStats.total})
          </button>
          <button
            onClick={() => setSelectedCategory('market')}
            style={{
              padding: '8px 16px',
              border: '1px solid #007bff',
              borderRadius: '20px',
              background: selectedCategory === 'market' ? '#007bff' : 'white',
              color: selectedCategory === 'market' ? 'white' : '#007bff',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            📊 Market ({categoryStats.market})
          </button>
          <button
            onClick={() => setSelectedCategory('stock')}
            style={{
              padding: '8px 16px',
              border: '1px solid #28a745',
              borderRadius: '20px',
              background: selectedCategory === 'stock' ? '#28a745' : 'white',
              color: selectedCategory === 'stock' ? 'white' : '#28a745',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            📈 Stock ({categoryStats.stock})
          </button>
          <button
            onClick={() => setSelectedCategory('crypto')}
            style={{
              padding: '8px 16px',
              border: '1px solid #ffc107',
              borderRadius: '20px',
              background: selectedCategory === 'crypto' ? '#ffc107' : 'white',
              color: selectedCategory === 'crypto' ? 'white' : '#ffc107',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            ₿ Crypto ({categoryStats.crypto})
          </button>
          <button
            onClick={() => setSelectedCategory('options')}
            style={{
              padding: '8px 16px',
              border: '1px solid #fd7e14',
              borderRadius: '20px',
              background: selectedCategory === 'options' ? '#fd7e14' : 'white',
              color: selectedCategory === 'options' ? 'white' : '#fd7e14',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            ⚡ Options ({categoryStats.options})
          </button>
          <button
            onClick={() => setSelectedCategory('polymarket')}
            style={{
              padding: '8px 16px',
              border: '1px solid #6f42c1',
              borderRadius: '20px',
              background: selectedCategory === 'polymarket' ? '#6f42c1' : 'white',
              color: selectedCategory === 'polymarket' ? 'white' : '#6f42c1',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            🎯 Polymarket ({categoryStats.polymarket})
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gap: '1rem' }}>
        {filteredPosts.map(post => (
          <div key={post.id} className="social-post" style={{
            border: `1px solid #e9ecef`,
            borderRadius: '8px',
            padding: '1rem',
            background: 'white',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '20px' }}>{getPlatformIcon(post.platform)}</span>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.1rem' }}>{post.title || post.content.substring(0, 100)}...</h3>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginTop: '4px' }}>
                    <span style={{ color: '#666', fontSize: '0.9rem' }}>by {post.author}</span>
                    {post.subreddit && (
                      <span style={{ 
                        background: '#f8f9fa', 
                        padding: '2px 6px', 
                        borderRadius: '4px',
                        fontSize: '0.8rem',
                        color: '#666'
                      }}>
                        r/{post.subreddit}
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span
                  style={{
                    backgroundColor: getCategoryColor(post.category),
                    color: 'white',
                    padding: '0.25rem 0.5rem',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    fontWeight: 'bold',
                    textTransform: 'uppercase'
                  }}
                >
                  {post.category}
                </span>
                <span
                  style={{
                    backgroundColor: getSentimentColor(post.sentiment),
                    color: 'white',
                    padding: '0.25rem 0.5rem',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    fontWeight: 'bold',
                    textTransform: 'uppercase'
                  }}
                >
                  {post.sentiment}
                </span>
              </div>
            </div>

            <p style={{ margin: '0.5rem 0', lineHeight: '1.5' }}>{post.content}</p>

            {post.ticker && (
              <div style={{ marginBottom: '0.5rem' }}>
                <span style={{ 
                  background: '#e3f2fd', 
                  padding: '2px 8px', 
                  borderRadius: '12px',
                  fontSize: '0.8rem',
                  color: '#1976d2',
                  fontWeight: 'bold'
                }}>
                  ${post.ticker}
                </span>
              </div>
            )}

            {post.hashtags && post.hashtags.length > 0 && (
              <div style={{ marginBottom: '0.5rem' }}>
                {post.hashtags.map((tag, index) => (
                  <span key={index} style={{ 
                    background: '#f0f0f0', 
                    padding: '2px 6px', 
                    borderRadius: '4px',
                    fontSize: '0.8rem',
                    color: '#666',
                    marginRight: '4px'
                  }}>
                    #{tag}
                  </span>
                ))}
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
              <div style={{ display: 'flex', gap: '16px', fontSize: '0.9rem', color: '#666' }}>
                {post.engagement.upvotes !== undefined && (
                  <span>👍 {post.engagement.upvotes}</span>
                )}
                {post.engagement.downvotes !== undefined && (
                  <span>👎 {post.engagement.downvotes}</span>
                )}
                {post.engagement.likes !== undefined && (
                  <span>❤️ {post.engagement.likes}</span>
                )}
                {post.engagement.retweets !== undefined && (
                  <span>🔄 {post.engagement.retweets}</span>
                )}
                {post.engagement.comments !== undefined && (
                  <span>💬 {post.engagement.comments}</span>
                )}
                {post.engagement.shares !== undefined && (
                  <span>📤 {post.engagement.shares}</span>
                )}
                <span style={{ fontWeight: 'bold', color: getPlatformColor(post.platform) }}>
                  Total: {getTotalEngagement(post.engagement)}
                </span>
              </div>
              <div style={{ fontSize: '0.9rem', color: '#666' }}>
                {formatTimeAgo(post.postedAt)}
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredPosts.length === 0 && !loading && (
        <div style={{ 
          textAlign: 'center', 
          padding: '40px', 
          color: '#666',
          background: '#f8f9fa',
          borderRadius: '8px'
        }}>
          <p>No social media posts found for the selected filters.</p>
        </div>
      )}
    </div>
  );
};

export default SocialMedia; 