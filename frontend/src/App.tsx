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

  const [modelsData, setModelsData] = useState<Model[]>([]);

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
