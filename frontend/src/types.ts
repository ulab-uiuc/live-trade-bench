// Centralized shared types to avoid duplication across components

export type Category = 'polymarket' | 'stock' | 'bitmex' | 'bitmex-benchmark';

export interface Position {
  symbol: string;
  quantity: number;
  average_price: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  // Polymarket specific fields
  question?: string;
  url?: string;
  category?: string;
}

export interface Portfolio {
  cash: number;
  total_value: number;
  positions: { [key: string]: Position };
  target_allocations: { [key: string]: number };
  current_allocations: { [key: string]: number };
}

export interface Model {
  id: string;
  name: string;
  category: string;
  status: string;
  performance: number;
  profit: number;
  trades: number;
  asset_allocation: { [key: string]: number };
  // Detailed data, fetched once and passed around
  portfolio: Portfolio;
  profitHistory: any;
  allocationHistory: any;
}

export interface NewsArticle {
  // ... existing code ...
}
