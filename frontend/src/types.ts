// Centralized shared types to avoid duplication across components

export type Category = 'polymarket' | 'stock';

export interface Model {
  id: string;
  name: string;
  category: Category;
  performance: number;
  accuracy: number;
  trades: number;
  profit: number;
  status: 'active' | 'inactive' | 'training';
  // Optional fields seen in some components
  market_type?: string;
  ticker?: string;
  strategy?: string;
}

export interface Trade {
  id: string;
  timestamp: Date;
  symbol: string;
  type: 'buy' | 'sell';
  amount: number;
  price: number;
  profit: number;
  model: string;
  category: Category;
  status: 'completed' | 'pending' | 'cancelled' | 'failed';
  fees: number;
  totalValue: number;
}
