import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import News from './components/News';
import SocialMedia from './components/SocialMedia';
import TradingHistoryPage from './components/TradingHistoryPage';
import Navigation from './components/Navigation';
import './App.css';

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

interface Trade {
  id: string;
  timestamp: Date;
  symbol: string;
  type: 'buy' | 'sell';
  amount: number;
  price: number;
  profit: number;
  model: string;
  category: 'polymarket' | 'stock' | 'option';
  status: 'completed' | 'pending' | 'cancelled' | 'failed';
  fees: number;
  totalValue: number;
}

interface Model {
  id: string;
  name: string;
  category: 'polymarket' | 'stock' | 'option';
  performance: number;
  accuracy: number;
  trades: number;
  profit: number;
  status: 'active' | 'inactive' | 'training';
  market_type?: string;
  ticker?: string;
  strategy?: string;
}

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
  category: 'market' | 'stock' | 'tech' | 'options' | 'polymarket';
  ticker?: string;
  url?: string;
  subreddit?: string;
  hashtags?: string[];
}

function App() {
  const [newsData, setNewsData] = useState<NewsItem[]>([]);
  const [tradesData, setTradesData] = useState<Trade[]>([]);
  const [modelsData, setModelsData] = useState<Model[]>([]);
  const [socialData, setSocialData] = useState<SocialPost[]>([]);
  const [newsLastRefresh, setNewsLastRefresh] = useState<Date>(new Date());
  const [tradesLastRefresh, setTradesLastRefresh] = useState<Date>(new Date());
  const [modelsLastRefresh, setModelsLastRefresh] = useState<Date>(new Date());
  const [socialLastRefresh, setSocialLastRefresh] = useState<Date>(new Date());

  return (
    <Router>
      <div className="App">
        <Navigation />
        <Routes>
          <Route path="/" element={
            <Dashboard
              modelsData={modelsData}
              setModelsData={setModelsData}
              modelsLastRefresh={modelsLastRefresh}
              setModelsLastRefresh={setModelsLastRefresh}
            />
          } />
          <Route path="/news" element={
            <News
              newsData={newsData}
              setNewsData={setNewsData}
              lastRefresh={newsLastRefresh}
              setLastRefresh={setNewsLastRefresh}
            />
          } />
          <Route path="/social" element={
            <SocialMedia
              socialData={socialData}
              setSocialData={setSocialData}
              lastRefresh={socialLastRefresh}
              setLastRefresh={setSocialLastRefresh}
            />
          } />
          <Route path="/trading-history" element={
            <TradingHistoryPage
              tradesData={tradesData}
              setTradesData={setTradesData}
              lastRefresh={tradesLastRefresh}
              setLastRefresh={setTradesLastRefresh}
            />
          } />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
