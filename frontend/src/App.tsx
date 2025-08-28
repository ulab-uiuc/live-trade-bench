import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import StockDashboard from './components/StockDashboard';
import PolymarketDashboard from './components/PolymarketDashboard';
import News from './components/News';
import SocialMedia from './components/SocialMedia';
import TradingHistoryPage from './components/TradingHistoryPage';
import Navigation from './components/Navigation';
import './App.css';

interface Model {
  id: string;
  name: string;
  category: 'polymarket' | 'stock';
  performance: number;
  accuracy: number;
  trades: number;
  profit: number;
  status: 'active' | 'inactive' | 'training';
  market_type?: string;
  ticker?: string;
  strategy?: string;
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
  category: 'polymarket' | 'stock';
  status: 'completed' | 'pending' | 'cancelled' | 'failed';
  fees: number;
  totalValue: number;
}

function App() {
  const [tradesData, setTradesData] = useState<Trade[]>([]);
  
  // 添加测试数据
  const [modelsData, setModelsData] = useState<Model[]>([
    {
      id: '1',
      name: 'Growth Stock Model',
      category: 'stock',
      performance: 15.5,
      accuracy: 0.78,
      trades: 45,
      profit: 2500,
      status: 'active'
    },
    {
      id: '2',
      name: 'Value Stock Model',
      category: 'stock',
      performance: 8.2,
      accuracy: 0.82,
      trades: 32,
      profit: 1800,
      status: 'active'
    },
    {
      id: '3',
      name: 'Tech Stock Model',
      category: 'stock',
      performance: 22.1,
      accuracy: 0.75,
      trades: 28,
      profit: 3200,
      status: 'active'
    },
    {
      id: '4',
      name: 'Polymarket Predictor',
      category: 'polymarket',
      performance: 12.8,
      accuracy: 0.68,
      trades: 15,
      profit: 950,
      status: 'active'
    },
    {
      id: '5',
      name: 'Election Tracker',
      category: 'polymarket',
      performance: 18.3,
      accuracy: 0.72,
      trades: 22,
      profit: 1400,
      status: 'active'
    },
    {
      id: '6',
      name: 'Sports Predictor',
      category: 'polymarket',
      performance: -2.1,
      accuracy: 0.65,
      trades: 18,
      profit: -300,
      status: 'active'
    }
  ]);
  
  const [tradesLastRefresh, setTradesLastRefresh] = useState<Date>(new Date());
  const [modelsLastRefresh, setModelsLastRefresh] = useState<Date>(new Date());

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
          <Route path="/stocks" element={
            <StockDashboard
              modelsData={modelsData}
              setModelsData={setModelsData}
              modelsLastRefresh={modelsLastRefresh}
              setModelsLastRefresh={setModelsLastRefresh}
            />
          } />
          <Route path="/polymarket" element={
            <PolymarketDashboard
              modelsData={modelsData}
              setModelsData={setModelsData}
              modelsLastRefresh={modelsLastRefresh}
              setModelsLastRefresh={setModelsLastRefresh}
            />
          } />
          <Route path="/news" element={<News />} />
          <Route path="/social" element={<SocialMedia />} />
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
