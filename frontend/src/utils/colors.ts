/**
 * Global color configuration for consistent asset colors across all components
 */

// Base color palette for different asset types
const STOCK_COLORS = [
  '#3b82f6', // Blue
  '#ef4444', // Red  
  '#10b981', // Green
  '#f59e0b', // Amber
  '#8b5cf6', // Purple
  '#06b6d4', // Cyan
  '#84cc16', // Lime
  '#f97316', // Orange
  '#ec4899', // Pink
  '#6366f1', // Indigo
  '#14b8a6', // Teal
  '#f43f5e', // Rose
  '#a855f7', // Violet
  '#22c55e', // Emerald
  '#eab308', // Yellow
  '#0ea5e9', // Sky
  '#dc2626', // Red-600
  '#16a34a', // Green-600
  '#ca8a04', // Yellow-600
  '#2563eb', // Blue-600
] as const;

const POLYMARKET_COLORS = [
  '#a78bfa', // Purple-300
  '#60a5fa', // Blue-300
  '#34d399', // Emerald-300
  '#fbbf24', // Amber-300
  '#f87171', // Red-300
  '#4ade80', // Green-300
  '#fb7185', // Rose-300
  '#38bdf8', // Sky-300
  '#c084fc', // Violet-300
  '#2dd4bf', // Teal-300
  '#facc15', // Yellow-300
  '#fb923c', // Orange-300
  '#e879f9', // Fuchsia-300
  '#67e8f9', // Cyan-300
  '#a3e635', // Lime-300
  '#94a3b8', // Slate-400
  '#f472b6', // Pink-300
  '#818cf8', // Indigo-300
  '#fdba74', // Orange-200
  '#bef264', // Lime-200
] as const;

// Special color for CASH (consistent across both systems)
const CASH_COLOR = '#6b7280'; // Gray-500

/**
 * Get color for a specific asset based on its ticker and category
 */
export function getAssetColor(ticker: string, category: 'stock' | 'polymarket'): string {
  // CASH always uses the same color
  if (ticker === 'CASH') {
    return CASH_COLOR;
  }

  // Generate a consistent hash for the ticker
  let hash = 0;
  for (let i = 0; i < ticker.length; i++) {
    hash = ticker.charCodeAt(i) + ((hash << 5) - hash);
  }
  hash = Math.abs(hash);

  // Select color palette based on category
  const colors = category === 'stock' ? STOCK_COLORS : POLYMARKET_COLORS;
  
  // Return consistent color based on hash
  return colors[hash % colors.length];
}

/**
 * Get all available colors for a category (useful for legends)
 */
export function getColorPalette(category: 'stock' | 'polymarket'): readonly string[] {
  return category === 'stock' ? STOCK_COLORS : POLYMARKET_COLORS;
}

/**
 * Get the special CASH color
 */
export function getCashColor(): string {
  return CASH_COLOR;
}

/**
 * Generate a color map for multiple assets
 */
export function generateColorMap(
  assets: string[], 
  category: 'stock' | 'polymarket'
): Record<string, string> {
  const colorMap: Record<string, string> = {};
  
  assets.forEach(asset => {
    colorMap[asset] = getAssetColor(asset, category);
  });
  
  return colorMap;
}
