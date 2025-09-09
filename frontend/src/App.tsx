import React, { useState, useEffect, useCallback, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import StockDashboard from './components/StockDashboard';
import PolymarketDashboard from './components/PolymarketDashboard';
import News from './components/News';
import SocialMedia from './components/SocialMedia';
import Navigation from './components/Navigation';
import './App.css';
import type { Model } from './types';

// Global data interfaces
interface NewsItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  published_at: string;
  category: string;
  link: string;
  stock_symbol: string | null;
}

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

function App() {
  // Add a ref to track if the initial fetch has been triggered
  const initialFetchComplete = useRef(false);

  // Global platform data - all managed in background
  const [modelsData, setModelsData] = useState<Model[]>([]);
  const [newsData, setNewsData] = useState<{
    stock: NewsItem[];
    polymarket: NewsItem[];
  }>({
    stock: [],
    polymarket: []
  });
  const [socialData, setSocialData] = useState<{
    stock: SocialPost[];
    polymarket: SocialPost[];
  }>({
    stock: [],
    polymarket: []
  });
  const [systemStatus, setSystemStatus] = useState<any>(null);

  // Add a global loading state
  const [isLoading, setIsLoading] = useState(true);

  // Storing previous ranks for comparison
  const prevRanks = useRef<{ [key: string]: number }>({});

  // Last refresh timestamps for all data types
  const [modelsLastRefresh, setModelsLastRefresh] = useState<Date>(new Date());
  const [newsLastRefresh, setNewsLastRefresh] = useState<Date>(new Date());
  const [socialLastRefresh, setSocialLastRefresh] = useState<Date>(new Date());
  const [systemLastRefresh, setSystemLastRefresh] = useState<Date>(new Date());

  // Background data fetching functions
  const fetchNewsData = useCallback(async () => {
    try {
      console.log('🔄 Background fetching news data...');
      const [stockResponse, polymarketResponse] = await Promise.all([
        fetch('/api/news/stock?limit=25'),
        fetch('/api/news/polymarket?limit=25')
      ]);

      if (stockResponse.ok && polymarketResponse.ok) {
        const stockNews = await stockResponse.json();
        const polymarketNews = await polymarketResponse.json();

        setNewsData({
          stock: stockNews,
          polymarket: polymarketNews
        });
        setNewsLastRefresh(new Date());
        console.log(`✅ Background news updated: ${stockNews.length} stock, ${polymarketNews.length} polymarket`);
      }
    } catch (error) {
      console.error('❌ Background news fetch failed:', error);
    }
  }, []);

  const fetchSocialData = useCallback(async () => {
    try {
      console.log('🔄 Background fetching social data...');
      const [stockResponse, polymarketResponse] = await Promise.all([
        fetch('/api/social/stock?limit=15'),
        fetch('/api/social/polymarket?limit=15')
      ]);

      console.log("DEBUG: 1. Raw API Response (Social)", { stock: stockResponse, polymarket: polymarketResponse });

      const stockPosts = stockResponse.ok ? await stockResponse.json() : [];
      const polymarketPosts = polymarketResponse.ok ? await polymarketResponse.json() : [];

      console.log("DEBUG: 2. Parsed JSON Data (Social)", { stockPosts, polymarketPosts });

      // Transform data to match expected format
      const transformStockPosts = stockPosts.map((post: any, index: number) => ({
        id: post.id || `stock_${index}`,
        platform: post.platform || 'Reddit',
        username: `u/${post.author}`,
        displayName: `u/${post.author}`,
        content: post.content || post.title || 'Stock discussion',
        time: post.created_at,
        likes: post.upvotes || Math.floor(Math.random() * 300),
        retweets: post.num_comments || Math.floor(Math.random() * 100),
        replies: Math.floor(Math.random() * 50),
        sentiment: post.sentiment || 'neutral',
        avatar: '📈',
        url: post.url,
        author: post.author,
        created_at: post.created_at,
        stock_symbols: post.stock_symbols
      }));

      const transformPolymarketPosts = polymarketPosts.map((post: any, index: number) => ({
        id: post.id || `poly_${index}`,
        platform: post.platform || 'Reddit',
        username: `u/${post.author}`,
        displayName: `u/${post.author}`,
        content: post.content || post.title || 'Political/prediction discussion',
        time: post.created_at || '2 hours ago',
        likes: post.upvotes || Math.floor(Math.random() * 300),
        retweets: post.num_comments || Math.floor(Math.random() * 100),
        replies: Math.floor(Math.random() * 50),
        sentiment: post.sentiment || 'neutral',
        avatar: '🎯',
        url: post.url,
        author: post.author,
        created_at: post.created_at,
        stock_symbols: post.stock_symbols
      }));

      setSocialData({
        stock: transformStockPosts,
        polymarket: transformPolymarketPosts
      });
      setSocialLastRefresh(new Date());
      console.log(`✅ Background social updated: ${transformStockPosts.length} stock, ${transformPolymarketPosts.length} polymarket`);
    } catch (error) {
      console.error('❌ Background social fetch failed:', error);
    }
  }, []);

  const fetchModelsData = useCallback(async () => {
    try {
      console.log('🔄 Background fetching models data...');
      const response = await fetch('/api/models/');
      if (response.ok) {
        const currentModels: Model[] = await response.json();

        // --- RANKING LOGIC ---
        // 1. Sort models by performance to determine rank
        const sortedModels = [...currentModels].sort((a, b) => b.performance - a.performance);

        // 2. Create a map of model.id -> rank
        const newRanks: { [key: string]: number } = {};
        sortedModels.forEach((model, index) => {
          newRanks[model.id] = index + 1;
        });

        // 3. Calculate rank changes by comparing with previous ranks
        const newRankChanges: { [key: string]: number } = {};
        currentModels.forEach(model => {
          const oldRank = prevRanks.current[model.id];
          const newRank = newRanks[model.id];
          if (oldRank && newRank) {
            // Correct logic: A lower rank number is better.
            // e.g., moving from rank 2 to 1 is a change of +1.
            newRankChanges[model.id] = oldRank - newRank;
          } else {
            newRankChanges[model.id] = 0; // No change for new models
          }
        });

        // 4. Add rank and rank_change to each model object
        const modelsWithRanks = currentModels.map(model => ({
          ...model,
          rank: newRanks[model.id],
          rank_change: newRankChanges[model.id] || 0,
        }));

        // 5. Update state and store current ranks for the next fetch
        setModelsData(modelsWithRanks);
        setModelsLastRefresh(new Date());
        prevRanks.current = newRanks; // Store for next comparison

        console.log(`✅ Background models updated: ${currentModels.length} models with ranks`);
      }
    } catch (error) {
      console.error('❌ Background models fetch failed:', error);
    }
  }, []);

  const fetchSystemStatus = useCallback(async () => {
    try {
      console.log('🔄 Background fetching system status...');
      const response = await fetch('/api/system/status');
      if (response.ok) {
        const status = await response.json();
        setSystemStatus(status);
        setSystemLastRefresh(new Date());
        console.log('✅ Background system status updated');
      }
    } catch (error) {
      console.error('❌ Background system status fetch failed:', error);
    }
  }, []);

  // Parallel data fetching function
  const fetchAllDataInParallel = useCallback(async () => {
    console.log('🔄 Starting parallel data fetch...');
    const startTime = Date.now();

    try {
      // Execute all fetch functions in parallel
      await Promise.all([
        fetchModelsData(),
        fetchNewsData(),
        fetchSocialData(),
        fetchSystemStatus()
      ]);

      const elapsed = Date.now() - startTime;
      console.log(`✅ Parallel fetch completed in ${elapsed}ms`);
    } catch (error) {
      console.error('❌ Parallel fetch failed:', error);
    } finally {
      // Set loading to false after the first fetch completes
      if (initialFetchComplete.current) {
        setIsLoading(false);
      }
    }
  }, [fetchModelsData, fetchNewsData, fetchSocialData, fetchSystemStatus]);

  // Unified background data management
  useEffect(() => {
    // This effect should only run ONCE during the app's entire lifecycle
    if (initialFetchComplete.current) {
      console.log('↩️ Initial fetch already completed, skipping effect.');
      return;
    }
    initialFetchComplete.current = true;

    console.log('🚀 Starting unified background data management for the first time...');

    // Fetch all data immediately on app start in parallel
    fetchAllDataInParallel();

    // Smart parallel interval management
    // Group updates that can happen together to maximize parallel efficiency

    // High frequency: Models + System (every 1 minute for debugging)
    const highFreqInterval = setInterval(async () => {
      console.log('🔄 High frequency parallel update (1 min)...');
      await Promise.all([fetchModelsData(), fetchSystemStatus()]);
    }, 1 * 60 * 1000);

    // Medium frequency: News + Social (every 10 minutes, parallel)
    const lowFreqInterval = setInterval(async () => {
      console.log('🔄 Low frequency parallel update...');
      await Promise.all([fetchNewsData(), fetchSocialData()]);
    }, 10 * 60 * 1000);

    console.log('⏰ Smart parallel intervals set: High(1m), Medium(10m)');

    // Cleanup all intervals on unmount
    return () => {
      clearInterval(highFreqInterval);
      clearInterval(lowFreqInterval);
      console.log('🛑 All parallel intervals cleared');
    };
    // The dependency array is correct, but we've added a ref guard to prevent re-runs from HMR.
  }, [fetchAllDataInParallel, fetchModelsData, fetchNewsData, fetchSocialData, fetchSystemStatus]);

  return (
    <Router>
      <div className="App">
        <Navigation />
        <Routes>
          <Route path="/" element={
            <Dashboard
              modelsData={modelsData}
              modelsLastRefresh={modelsLastRefresh}
              systemStatus={systemStatus}
              systemLastRefresh={systemLastRefresh}
            />
          } />
          <Route path="/stocks" element={
            <StockDashboard
              modelsData={modelsData}
              modelsLastRefresh={modelsLastRefresh}
              isLoading={isLoading}
            />
          } />
          <Route path="/polymarket" element={
            <PolymarketDashboard
              modelsData={modelsData}
              modelsLastRefresh={modelsLastRefresh}
              isLoading={isLoading}
            />
          } />
          <Route path="/news" element={
            <News
              newsData={newsData}
              lastRefresh={newsLastRefresh}
              isLoading={isLoading}
            />
          } />
          <Route path="/social" element={
            <SocialMedia
              socialData={socialData}
              lastRefresh={socialLastRefresh}
              isLoading={isLoading}
            />
          } />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
