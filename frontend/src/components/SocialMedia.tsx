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
  category: 'market' | 'stock' | 'tech' | 'polymarket';
  ticker?: string;
  url?: string;
  subreddit?: string;
  hashtags?: string[];
}

interface SocialMediaProps {
  socialData: SocialPost[];
  setSocialData: (posts: SocialPost[]) => void;
  lastRefresh: Date;
  setLastRefresh: (date: Date) => void;
}

const SocialMedia: React.FC<SocialMediaProps> = ({
  socialData,
  setSocialData,
  lastRefresh,
  setLastRefresh
}) => {
  const [loading, setLoading] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState<'all' | 'reddit' | 'twitter' | 'discord' | 'telegram'>('all');
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'market' | 'stock' | 'tech' | 'polymarket'>('all');

  const fetchSocialPosts = async () => {
    setLoading(true);
    try {
      // Fetch real social media data from Reddit - get 5 posts from each category
      const response = await fetch('/api/social/?category=all');
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
          comments: post.comments,
        },
        sentiment: post.sentiment,
        category: post.category,
        ticker: post.ticker,
        url: post.url,
        subreddit: post.subreddit,
      }));

      setSocialData(transformedPosts);
      setLastRefresh(new Date());
    } catch (error) {
      console.error('Error fetching social posts:', error);
      // Keep existing social data on error, don't clear it
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Only fetch if we don't have data or if it's been more than a day
    const shouldFetch = socialData.length === 0 ||
      (Date.now() - lastRefresh.getTime()) > 24 * 60 * 60 * 1000;

    if (shouldFetch) {
      fetchSocialPosts();
    }

    // Auto-refresh every day
    const interval = setInterval(fetchSocialPosts, 24 * 60 * 60 * 1000);

    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
      case 'tech': return '#17a2b8';
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

  const filteredPosts = socialData.filter(post => {
    const platformMatch = selectedPlatform === 'all' || post.platform === selectedPlatform;
    const categoryMatch = selectedCategory === 'all' || post.category === selectedCategory;
    return platformMatch && categoryMatch;
  });

  const platformStats = {
    reddit: socialData.filter(p => p.platform === 'reddit').length,
    twitter: socialData.filter(p => p.platform === 'twitter').length,
    discord: socialData.filter(p => p.platform === 'discord').length,
    telegram: socialData.filter(p => p.platform === 'telegram').length,
    total: socialData.length
  };

  const categoryStats = {
    market: socialData.filter(p => p.category === 'market').length,
    stock: socialData.filter(p => p.category === 'stock').length,
    tech: socialData.filter(p => p.category === 'tech').length,
    polymarket: socialData.filter(p => p.category === 'polymarket').length,
    total: socialData.length
  };

  const sortedPosts = filteredPosts.sort((a, b) => b.postedAt.getTime() - a.postedAt.getTime());

  const sentimentStats = {
    positive: socialData.filter(p => p.sentiment === 'positive').length,
    negative: socialData.filter(p => p.sentiment === 'negative').length,
    neutral: socialData.filter(p => p.sentiment === 'neutral').length,
    total: socialData.length
  };

  const totalEngagement = socialData.reduce((sum, post) => sum + getTotalEngagement(post.engagement), 0);
  const avgEngagement = socialData.length > 0 ? (totalEngagement / socialData.length) : 0;

  return (
    <div className="social-media-page">
      <div className="refresh-indicator">
        <h1>Social Media Sentiment</h1>
        {loading && <div className="spinner"></div>}
        <span style={{ marginLeft: 'auto', fontSize: '0.875rem', color: '#666' }}>
          Last updated: {lastRefresh.toLocaleTimeString()}
        </span>
      </div>

      {/* Summary Statistics */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '15px',
        marginBottom: '20px'
      }}>
        <div style={{
          background: '#f8f9fa',
          padding: '15px',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#007bff' }}>
            {socialData.length}
          </div>
          <div style={{ fontSize: '0.9rem', color: '#666' }}>Total Posts</div>
        </div>
        <div style={{
          background: '#e8f5e8',
          padding: '15px',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#28a745' }}>
            {sentimentStats.positive}
          </div>
          <div style={{ fontSize: '0.9rem', color: '#666' }}>Positive</div>
        </div>
        <div style={{
          background: '#ffe8e8',
          padding: '15px',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#dc3545' }}>
            {sentimentStats.negative}
          </div>
          <div style={{ fontSize: '0.9rem', color: '#666' }}>Negative</div>
        </div>
        <div style={{
          background: '#f0f0f0',
          padding: '15px',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#6c757d' }}>
            {sentimentStats.neutral}
          </div>
          <div style={{ fontSize: '0.9rem', color: '#666' }}>Neutral</div>
        </div>
        <div style={{
          background: '#fff3cd',
          padding: '15px',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#ffc107' }}>
            {avgEngagement.toFixed(1)}
          </div>
          <div style={{ fontSize: '0.9rem', color: '#666' }}>Avg Engagement</div>
        </div>
      </div>

      {/* Filters */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap', marginBottom: '15px' }}>
          <div>
            <label style={{ fontSize: '0.9rem', fontWeight: 'bold', marginBottom: '5px', display: 'block' }}>
              Platform
            </label>
            <select
              value={selectedPlatform}
              onChange={(e) => setSelectedPlatform(e.target.value as any)}
              style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
            >
              <option value="all">All Platforms ({platformStats.total})</option>
              <option value="reddit">Reddit ({platformStats.reddit})</option>
              <option value="twitter">Twitter ({platformStats.twitter})</option>
              <option value="discord">Discord ({platformStats.discord})</option>
              <option value="telegram">Telegram ({platformStats.telegram})</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: '0.9rem', fontWeight: 'bold', marginBottom: '5px', display: 'block' }}>
              Category
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value as any)}
              style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
            >
              <option value="all">All Categories ({categoryStats.total})</option>
              <option value="market">Market ({categoryStats.market})</option>
              <option value="stock">Stock ({categoryStats.stock})</option>
              <option value="tech">Tech ({categoryStats.tech})</option>
              <option value="polymarket">Polymarket ({categoryStats.polymarket})</option>
            </select>
          </div>
        </div>
      </div>

      {/* Posts List */}
      <div style={{ maxHeight: 'calc(100vh - 400px)', overflowY: 'auto' }}>
        {sortedPosts.map(post => (
          <div key={post.id} className="social-post" style={{
            border: `1px solid #e9ecef`,
            borderRadius: '8px',
            padding: '15px',
            marginBottom: '10px',
            background: 'white',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            borderLeft: `4px solid ${getPlatformColor(post.platform)}`
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

      {sortedPosts.length === 0 && !loading && (
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
