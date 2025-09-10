/**
 * Global color configuration for consistent asset colors across all components
 */

// --- Start of Manual Color Conversion Helpers ---

// Helper function to convert hex to RGB
const hexToRgb = (hex: string): { r: number; g: number; b: number } => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : { r: 0, g: 0, b: 0 };
};

// Helper function to convert RGB to HSL
const rgbToHsl = (r: number, g: number, b: number): { h: number; s: number; l: number } => {
  r /= 255;
  g /= 255;
  b /= 255;
  const max = Math.max(r, g, b),
    min = Math.min(r, g, b);
  let h = 0,
    s = 0,
    l = (max + min) / 2;
  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r:
        h = (g - b) / d + (g < b ? 6 : 0);
        break;
      case g:
        h = (b - r) / d + 2;
        break;
      case b:
        h = (r - g) / d + 4;
        break;
    }
    h /= 6;
  }
  return { h: h * 360, s, l };
};

// Helper function to convert HSL to RGB
const hslToRgb = (h: number, s: number, l: number): { r: number; g: number; b: number } => {
  let r, g, b;
  if (s === 0) {
    r = g = b = l;
  } else {
    const hue2rgb = (p: number, q: number, t: number) => {
      if (t < 0) t += 1;
      if (t > 1) t -= 1;
      if (t < 1 / 6) return p + (q - p) * 6 * t;
      if (t < 1 / 2) return q;
      if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
      return p;
    };
    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;
    r = hue2rgb(p, q, h / 360 + 1 / 3);
    g = hue2rgb(p, q, h / 360);
    b = hue2rgb(p, q, h / 360 - 1 / 3);
  }
  return { r: Math.round(r * 255), g: Math.round(g * 255), b: Math.round(b * 255) };
};

// Helper function to convert RGB to Hex
const rgbToHex = (r: number, g: number, b: number): string =>
  '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('');

// --- End of Manual Color Conversion Helpers ---


// Helper function to sort and desaturate a color palette
const processColors = (colors: string[], desaturationAmount = 0.075): string[] => {
  const sortedColors = [...colors].sort((a, b) => {
    const { r: rA, g: gA, b: bA } = hexToRgb(a);
    const hslA = rgbToHsl(rA, gA, bA);
    const { r: rB, g: gB, b: bB } = hexToRgb(b);
    const hslB = rgbToHsl(rB, gB, bB);
    return hslA.h - hslB.h;
  });

  return sortedColors.map(color => {
    const { r, g, b } = hexToRgb(color);
    const hsl = rgbToHsl(r, g, b);
    hsl.s = Math.max(0, hsl.s - desaturationAmount); // Desaturate
    const { r: newR, g: newG, b: newB } = hslToRgb(hsl.h, hsl.s, hsl.l);
    return rgbToHex(newR, newG, newB);
  });
};

// Base color palette for different asset types
// Warm colors for Stock (reds, oranges, yellows, light blues, greens)
const BASE_STOCK_COLORS = [
  '#8ECDDD', // Light Blue
  '#F9A825', // Bright Yellow
  '#5C6BC0', // Indigo Light
  '#FF7043', // Coral
  '#9CCC65', // Light Green
  '#26A69A', // Teal
  '#AB47BC', // Purple Light
  '#FFA726', // Orange
  '#29B6F6', // Sky Blue
  '#EC407A', // Pink
  '#66CCCC', // Aqua
  '#FFEE58', // Lemon
  '#66BB6A', // Green
  '#EF5350', // Red Light
  '#42A5F5', // Blue
  '#D4E157', // Lime
  '#FFCA28', // Amber
  '#FFD700', // Gold
  '#7E57C2', // Deep Purple Light
  '#00ACC1', // Cyan
] as const;

// Cool colors for Polymarket (blues, greens, purples)
const BASE_POLYMARKET_COLORS = [
  '#6495ED', // Cornflower Blue
  '#87CEEB', // Sky Blue
  '#ADD8E6', // Light Blue
  '#40E0D0', // Turquoise
  '#20B2AA', // Light Sea Green
  '#00CED1', // Dark Turquoise
  '#66CDAA', // Medium Aquamarine
  '#3CB371', // Medium Sea Green
  '#2E8B57', // Sea Green
  '#9370DB', // Medium Purple
  '#BA55D3', // Medium Orchid
  '#9932CC', // Dark Orchid
  '#8A2BE2', // Blue Violet
  '#483D8B', // Dark Slate Blue
  '#6A5ACD', // Slate Blue
  '#7B68EE', // Medium Slate Blue
  '#4682B4', // Steel Blue (Cool)
  '#5F9EA0', // Cadet Blue
  '#B0E0E6', // Powder Blue
  '#87CEFA', // Light Sky Blue
] as const;

// Processed colors: sorted by hue and desaturated
const STOCK_COLORS = processColors([...BASE_STOCK_COLORS], 0.075);
const POLYMARKET_COLORS = processColors([...BASE_POLYMARKET_COLORS], 0.075);

// Special color for CASH (consistent across both systems)
const CASH_COLOR = '#6b7280'; // Gray-500

/**
 * Get color for a specific asset based on its ticker and category
 */
export function getAssetColor(
  ticker: string,
  index: number,
  category: 'stock' | 'polymarket'
): string {
  // CASH always uses the same color
  if (ticker === 'CASH') {
    return CASH_COLOR;
  }

  // Select the processed color palette
  const colors = category === 'stock' ? STOCK_COLORS : POLYMARKET_COLORS;

  // Return consistent color from the sorted and desaturated palette based on the sorted index
  return colors[index % colors.length];
}

/**
 * Get all available colors for a category (useful for legends)
 */
export function getColorPalette(
  category: 'stock' | 'polymarket'
): readonly string[] {
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
  
  // Sort assets alphabetically to match the display order
  const sortedAssets = [...assets].sort((a, b) => {
    if (a === 'CASH') return 1;
    if (b === 'CASH') return -1;
    return a.localeCompare(b);
  });

  sortedAssets.forEach((asset, index) => {
    colorMap[asset] = getAssetColor(asset, index, category);
  });

  return colorMap;
}
