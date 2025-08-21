import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface PortfolioHistoryPoint {
  timestamp: string;
  holdings: { [ticker: string]: number };
  prices: { [ticker: string]: number };
  cash: number;
  totalValue: number;
}

interface AreaChartProps {
  portfolioHistory: PortfolioHistoryPoint[];
  title?: string;
  size?: 'small' | 'medium' | 'large';
}

const AreaChart: React.FC<AreaChartProps> = ({
  portfolioHistory,
  title = "Portfolio Composition Over Time",
  size = 'medium'
}) => {
  if (!portfolioHistory || portfolioHistory.length === 0) {
    return (
      <div className={`area-chart-container ${size}`}>
        <h4 className="chart-title">{title}</h4>
        <div className="no-data-message">
          <span>📊 No portfolio history available</span>
        </div>
      </div>
    );
  }

  const generateColors = (count: number) => {
    const baseColors = [
      { bg: 'rgba(52, 152, 219, 0.6)', border: '#3498db' },
      { bg: 'rgba(231, 76, 60, 0.6)', border: '#e74c3c' },
      { bg: 'rgba(46, 204, 113, 0.6)', border: '#2ecc71' },
      { bg: 'rgba(243, 156, 18, 0.6)', border: '#f39c12' },
      { bg: 'rgba(155, 89, 182, 0.6)', border: '#9b59b6' },
      { bg: 'rgba(26, 188, 156, 0.6)', border: '#1abc9c' },
      { bg: 'rgba(52, 73, 94, 0.6)', border: '#34495e' },
      { bg: 'rgba(230, 126, 34, 0.6)', border: '#e67e22' },
      { bg: 'rgba(149, 165, 166, 0.6)', border: '#95a5a6' },
      { bg: 'rgba(211, 84, 0, 0.6)', border: '#d35400' }
    ];
    return baseColors.slice(0, count);
  };

  const labels = portfolioHistory.map(point => {
    const date = new Date(point.timestamp);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: size === 'small' ? undefined : 'numeric'
    });
  });

  const allTickers = new Set<string>();
  portfolioHistory.forEach(point => {
    Object.keys(point.holdings).forEach(ticker => {
      if (point.holdings[ticker] > 0) {
        allTickers.add(ticker);
      }
    });
  });

  const tickersArray = Array.from(allTickers);
  const colors = generateColors(tickersArray.length + 1);

  const datasets = [];

  tickersArray.forEach((ticker, index) => {
    const data = portfolioHistory.map(point => {
      const shares = point.holdings[ticker] || 0;
      const price = point.prices[ticker] || 0;
      return shares * price;
    });

    datasets.push({
      label: ticker,
      data,
      backgroundColor: colors[index].bg,
      borderColor: colors[index].border,
      borderWidth: 1,
      fill: true,
      tension: 0.4,
      pointRadius: size === 'small' ? 1 : 2,
      pointHoverRadius: size === 'small' ? 3 : 4,
    });
  });

  const cashData = portfolioHistory.map(point => point.cash);
  datasets.push({
    label: 'Cash',
    data: cashData,
    backgroundColor: colors[tickersArray.length].bg,
    borderColor: colors[tickersArray.length].border,
    borderWidth: 1,
    fill: true,
    tension: 0.4,
    pointRadius: size === 'small' ? 1 : 2,
    pointHoverRadius: size === 'small' ? 3 : 4,
  });

  const data = {
    labels,
    datasets,
  };

  const options = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: '#a0a0b8',
          font: {
            size: size === 'small' ? 8 : size === 'medium' ? 10 : 12,
          },
          usePointStyle: true,
          padding: size === 'small' ? 10 : 15,
        },
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#ffffff',
        bodyColor: '#a0a0b8',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        callbacks: {
          label: (context: any) => {
            const label = context.dataset.label || '';
            const value = context.parsed.y;
            return `${label}: $${value.toFixed(2)}`;
          },
          footer: (tooltipItems: any[]) => {
            const total = tooltipItems.reduce((sum, item) => sum + item.parsed.y, 0);
            return `Total: $${total.toFixed(2)}`;
          },
        },
      },
    },
    scales: {
      x: {
        display: size !== 'small',
        stacked: true,
        grid: {
          display: false,
        },
        ticks: {
          color: '#6b6b80',
          font: {
            size: size === 'small' ? 8 : 10,
          },
          maxTicksLimit: size === 'small' ? 4 : 8,
        },
      },
      y: {
        display: size !== 'small',
        stacked: true,
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
        ticks: {
          color: '#6b6b80',
          font: {
            size: size === 'small' ? 8 : 10,
          },
          callback: (value: any) => {
            return `$${value}`;
          },
        },
      },
    },
    interaction: {
      mode: 'nearest' as const,
      axis: 'x' as const,
      intersect: false,
    },
    elements: {
      line: {
        tension: 0.4,
      },
    },
  };

  const getContainerSize = () => {
    switch (size) {
      case 'small': return { width: '300px', height: '200px' };
      case 'large': return { width: '700px', height: '400px' };
      default: return { width: '500px', height: '300px' };
    }
  };

  return (
    <div className={`area-chart-container ${size}`}>
      <h4 className="chart-title">{title}</h4>
      <div className="chart-wrapper" style={getContainerSize()}>
        <Line data={data} options={options} />
      </div>
    </div>
  );
};

export default AreaChart;
