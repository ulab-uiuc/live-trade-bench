// Centralized shared types to avoid duplication across components

export type Category = 'polymarket' | 'stock';

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
  portfolio: any;
  chartData: any;
  allocationHistory: any;
}

export interface NewsArticle {
  // ... existing code ...
}
