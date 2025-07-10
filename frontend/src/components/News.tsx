import React, { useState, useEffect } from 'react';

interface NewsItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  publishedAt: Date;
  impact: 'high' | 'medium' | 'low';
  category: 'market' | 'economic' | 'company' | 'tech';
  url: string;
}

interface NewsProps {
  newsData: NewsItem[];
  setNewsData: (news: NewsItem[]) => void;
  lastRefresh: Date;
  setLastRefresh: (date: Date) => void;
}

const News: React.FC<NewsProps> = ({ newsData, setNewsData, lastRefresh, setLastRefresh }) => {
  const [loading, setLoading] = useState(false);

  const fetchNews = async () => {
    setLoading(true);
    try {
      // Fetch real news data instead of sample data
      const response = await fetch('http://localhost:8000/api/news/real?query=stock%20market&days=7');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();

      // Transform backend data to frontend format
      const transformedNews: NewsItem[] = data.map((article: any) => ({
        id: article.id,
        title: article.title,
        summary: article.summary,
        source: article.source,
        publishedAt: new Date(article.published_at),
        impact: article.impact,
        category: article.category,
        url: article.url
      }));

      setNewsData(transformedNews);
      setLastRefresh(new Date());
    } catch (error) {
      console.error('Error fetching news:', error);
      // Keep existing news data on error, don't clear it
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Only fetch if we don't have data or if it's been more than an hour
    const shouldFetch = newsData.length === 0 || 
      (Date.now() - lastRefresh.getTime()) > 60 * 60 * 1000;
    
    if (shouldFetch) {
      fetchNews();
    }

    // Auto-refresh every hour
    const interval = setInterval(fetchNews, 60 * 60 * 1000);

    return () => clearInterval(interval);
  }, []);

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return '#dc3545';
      case 'medium': return '#ffc107';
      case 'low': return '#28a745';
      default: return '#6c757d';
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'market': return '#007bff';
      case 'economic': return '#6f42c1';
      case 'company': return '#fd7e14';
      case 'tech': return '#20c997';
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

  return (
    <div className="news-page">
      <div className="refresh-indicator">
        <h1>Market News</h1>
        {loading && <div className="spinner"></div>}
        <span style={{ marginLeft: 'auto', fontSize: '0.875rem', color: '#666' }}>
          Last updated: {lastRefresh.toLocaleTimeString()}
        </span>
      </div>

      <div style={{ display: 'grid', gap: '1rem' }}>
        {newsData.map(item => (
          <div key={item.id} className="news-item">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
              <h3>{item.title}</h3>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <span
                  style={{
                    backgroundColor: getCategoryColor(item.category),
                    color: 'white',
                    padding: '0.25rem 0.5rem',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    fontWeight: 'bold',
                    textTransform: 'uppercase'
                  }}
                >
                  {item.category}
                </span>
                <span
                  style={{
                    backgroundColor: getImpactColor(item.impact),
                    color: 'white',
                    padding: '0.25rem 0.5rem',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    fontWeight: 'bold',
                    textTransform: 'uppercase'
                  }}
                >
                  {item.impact} impact
                </span>
              </div>
            </div>

            <p>{item.summary}</p>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
              <div className="date">
                <strong>{item.source}</strong> • {formatTimeAgo(item.publishedAt)}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default News;
