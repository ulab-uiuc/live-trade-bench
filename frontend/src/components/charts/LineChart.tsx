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

interface ProfitDataPoint {
  timestamp: string;
  profit: number;
  totalValue: number;
}

interface LineChartProps {
  profitHistory: ProfitDataPoint[];
  title?: string;
  size?: 'small' | 'medium' | 'large';
  showTotalValue?: boolean;
}

const LineChart: React.FC<LineChartProps> = ({
  profitHistory,
  title = "Profit History",
  size = 'medium',
  showTotalValue = false
}) => {
  if (!profitHistory || profitHistory.length === 0) {
    return (
      <div className={`line-chart-container ${size}`}>
        <h4 className="chart-title">{title}</h4>
        <div className="no-data-message">
          <span>📈 No profit history available</span>
        </div>
      </div>
    );
  }

  const labels = profitHistory.map(point => {
    const date = new Date(point.timestamp);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: size === 'small' ? undefined : 'numeric'
    });
  });

  const profitData = profitHistory.map(point => point.profit);
  const totalValueData = showTotalValue ? profitHistory.map(point => point.totalValue) : [];

  const datasets = [
    {
      label: 'Profit/Loss',
      data: profitData,
      borderColor: '#3498db',
      backgroundColor: 'rgba(52, 152, 219, 0.1)',
      borderWidth: 2,
      fill: true,
      tension: 0.4,
      pointRadius: size === 'small' ? 2 : 4,
      pointHoverRadius: size === 'small' ? 4 : 6,
    }
  ];

  if (showTotalValue && totalValueData.length > 0) {
    datasets.push({
      label: 'Total Value',
      data: totalValueData,
      borderColor: '#2ecc71',
      backgroundColor: 'rgba(46, 204, 113, 0.1)',
      borderWidth: 2,
      fill: false,
      tension: 0.4,
      pointRadius: size === 'small' ? 2 : 4,
      pointHoverRadius: size === 'small' ? 4 : 6,
    });
  }

  const data = {
    labels,
    datasets,
  };

  const options = {
    responsive: true,
    maintainAspectRatio: true,
    backgroundColor: 'transparent',
    plugins: {
      legend: {
        display: false,
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
            return `${label}: ${value >= 0 ? '+' : ''}$${value.toFixed(2)}`;
          },
        },
      },
    },
    scales: {
      x: {
        display: size !== 'small',
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
      point: {
        backgroundColor: 'rgba(52, 152, 219, 0.8)',
        borderColor: '#3498db',
        borderWidth: 2,
      },
      line: {
        borderColor: '#3498db',
        borderWidth: 2,
      },
    },
  };

  const getContainerSize = () => {
    switch (size) {
      case 'small': return { width: '300px', height: '200px' };
      case 'large': return { width: '600px', height: '400px' };
      default: return { width: '400px', height: '250px' };
    }
  };

  return (
    <div className={`line-chart-container ${size}`}>
      <h4 className="chart-title">{title}</h4>
      <div className="chart-wrapper" style={getContainerSize()}>
        <Line data={data} options={options} />
      </div>
    </div>
  );
};

export default LineChart;
