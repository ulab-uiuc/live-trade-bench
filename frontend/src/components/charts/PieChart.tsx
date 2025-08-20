import React from 'react';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js';
import { Pie } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

interface PieChartProps {
  holdings: { [ticker: string]: number };
  totalValue: number;
  title?: string;
  size?: 'small' | 'medium' | 'large';
}

const PieChart: React.FC<PieChartProps> = ({
  holdings,
  totalValue,
  title = "Stock Allocation",
  size = 'medium'
}) => {
  const generateColors = (count: number) => {
    const colors = [
      '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
      '#1abc9c', '#34495e', '#e67e22', '#95a5a6', '#d35400'
    ];
    return colors.slice(0, count);
  };

  const stockEntries = Object.entries(holdings).filter(([_, value]) => value > 0);

  if (stockEntries.length === 0) {
    return (
      <div className={`pie-chart-container ${size}`}>
        <h4 className="chart-title">{title}</h4>
        <div className="no-data-message">
          <span>💰 100% Cash</span>
        </div>
      </div>
    );
  }

  const labels = stockEntries.map(([ticker]) => ticker);
  const values = stockEntries.map(([_, shares]) => shares);
  const total = values.reduce((sum, val) => sum + val, 0);
  const percentages = values.map(val => ((val / total) * 100));

  const colors = generateColors(labels.length);

  const data = {
    labels: labels,
    datasets: [
      {
        data: percentages,
        backgroundColor: colors,
        borderColor: colors.map(color => color + '80'),
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: true,
    backgroundColor: 'transparent',
    plugins: {
      legend: {
        position: 'right' as const,
        labels: {
          padding: 15,
          usePointStyle: true,
          color: '#a0a0b8',
          font: {
            size: size === 'small' ? 10 : size === 'medium' ? 12 : 14,
          },
          generateLabels: (chart: any) => {
            const data = chart.data;
            if (data.labels.length && data.datasets.length) {
              return data.labels.map((label: string, index: number) => {
                const percentage = data.datasets[0].data[index];
                return {
                  text: `${label}: ${percentage.toFixed(1)}%`,
                  fillStyle: data.datasets[0].backgroundColor[index],
                  strokeStyle: data.datasets[0].borderColor[index],
                  pointStyle: 'circle',
                };
              });
            }
            return [];
          },
        },
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#ffffff',
        bodyColor: '#a0a0b8',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        callbacks: {
          label: (context: any) => {
            const label = context.label || '';
            const percentage = context.parsed;
            const shares = values[context.dataIndex];
            return `${label}: ${shares} shares (${percentage.toFixed(1)}%)`;
          },
        },
      },
    },
    elements: {
      arc: {
        borderWidth: 2,
        borderColor: 'rgba(255, 255, 255, 0.1)',
      },
    },
  };

  const getContainerSize = () => {
    switch (size) {
      case 'small': return { width: '300px', height: '200px' };
      case 'large': return { width: '500px', height: '350px' };
      default: return { width: '400px', height: '250px' };
    }
  };

  return (
    <div className={`pie-chart-container ${size}`}>
      <h4 className="chart-title">{title}</h4>
      <div className="chart-wrapper" style={getContainerSize()}>
        <Pie data={data} options={options} />
      </div>
    </div>
  );
};

export default PieChart;
