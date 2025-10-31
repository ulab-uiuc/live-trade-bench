import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
from pathlib import Path
from datetime import datetime

# Set seaborn theme
sns.set_theme(style="white")

# Read metrics data
metrics_dir = Path("../data/metrics")
metrics_files = list(metrics_dir.glob("all_metrics_*.json"))

if not metrics_files:
    print("Error: Cannot find metrics file. Please run calculate_metrics.py first")
    exit(1)

# Use the latest metrics file
latest_file = sorted(metrics_files)[-1]
print(f"Reading metrics file: {latest_file}\n")

with open(latest_file, "r") as f:
    all_metrics = json.load(f)

# Filter out error data
all_metrics = [m for m in all_metrics if 'error' not in m]

# Group by category
stock_metrics = [m for m in all_metrics if m['category'] == 'stock']
polymarket_metrics = [m for m in all_metrics if m['category'] == 'polymarket']
benchmark_metrics = [m for m in all_metrics if m['category'] == 'benchmark']

print(f"Stock models: {len(stock_metrics)}")
print(f"Polymarket models: {len(polymarket_metrics)}")
print(f"Benchmarks: {len(benchmark_metrics)}\n")

# Create output directory
output_dir = Path("../data/visualizations")
output_dir.mkdir(exist_ok=True)

def create_beautiful_plot(metrics_list, benchmark_list, category_name, output_name):
    """Create a beautiful risk-return scatter plot using seaborn relplot"""
    
    if not metrics_list:
        print(f"No data for {category_name}")
        return
    
    # Prepare data as DataFrame for seaborn
    data = []
    for m in metrics_list:
        data.append({
            'Annualized Volatility (%)': m['volatility_annual_pct'],
            'Total Return (%)': m['total_return_pct'],
            'Sharpe Ratio': m['sharpe_ratio'],
            'Model': m['model_name'],
            'Type': 'Model'
        })
    
    # Add benchmark data if available
    if benchmark_list:
        for m in benchmark_list:
            data.append({
                'Annualized Volatility (%)': m['volatility_annual_pct'],
                'Total Return (%)': m['total_return_pct'],
                'Sharpe Ratio': m['sharpe_ratio'],
                'Model': m['model_name'],
                'Type': 'Benchmark'
            })
    
    df = pd.DataFrame(data)
    
    # Choose color palette based on category
    if category_name.lower() == 'polymarket':
        # Orange gradient for Polymarket
        colors = ['#FFA726', '#F57C00', '#E65100']  # 浅橙到深橙
        custom_palette = LinearSegmentedColormap.from_list('custom_orange', colors)
    else:
        # Blue gradient for Stock
        colors = ['#4A90E2', '#2E5F8E', '#1A3A5C']  # 中蓝到深蓝
        custom_palette = LinearSegmentedColormap.from_list('custom_blue', colors)
    
    # Create the relplot with custom color palette (square aspect)
    g = sns.relplot(
        data=df,
        x='Annualized Volatility (%)',
        y='Total Return (%)',
        hue='Sharpe Ratio',
        size='Sharpe Ratio',
        sizes=(500, 5000),  # 放大50倍（原来约100-2000）
        alpha=0.7,
        palette=custom_palette,  # 使用自定义渐变色
        height=14,
        aspect=1.0,  # 正方形
        edgecolor='white',
        linewidth=3,
        legend=False  # 删除图例
    )
    
    # Customize the plot (no bold text)
    g.set_titles(size=50)
    g.set_axis_labels('Annualized Volatility (%)', 'Total Return (%)', 
                      fontsize=44)
    g.ax.tick_params(labelsize=36, width=2, length=8)
    
    # Add title (no bold)
    
    # No reference lines
    
    # Add labels for all models with smart positioning
    x_data = df['Annualized Volatility (%)'].values
    y_data = df['Total Return (%)'].values
    x_median = np.median(x_data)
    
    for idx, row in df.iterrows():
        x_val = row['Annualized Volatility (%)']
        y_val = row['Total Return (%)']
        model_name = row['Model']
        
        # Smart positioning: put label on left if point is on right side
        if x_val > x_median:
            # Point on right, label on left
            text = f"{model_name}  "
            ha = 'right'
        else:
            # Point on left, label on right
            text = f"  {model_name}"
            ha = 'left'
        
        g.ax.text(x_val, y_val, text, 
                 fontsize=20,
                 va='center',
                 ha=ha,
                 zorder=4)
    
    # Set spine style
    for spine in g.ax.spines.values():
        spine.set_edgecolor('#34495e')
        spine.set_linewidth(2)
    
    # No grid
    g.ax.grid(False)
    
    plt.tight_layout()
    
    # Save figure as PDF
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f"{output_name}_{timestamp}.pdf"
    g.savefig(output_file, format='pdf', bbox_inches='tight', facecolor='white')
    print(f"✓ {category_name} plot saved to: {output_file}")
    
    plt.close()

# Generate Stock market plot
print("\nGenerating visualizations...")
print("=" * 80)

create_beautiful_plot(
    stock_metrics,
    benchmark_metrics,
    'Stock',
    'stock_risk_return'
)

# Generate Polymarket plot
create_beautiful_plot(
    polymarket_metrics,
    [],  # No benchmark for Polymarket
    'Polymarket',
    'polymarket_risk_return'
)

print("\n" + "=" * 80)
print("Visualization Complete!")
print("=" * 80)
print("""
Chart Explanation:
------------------
X-axis (Annualized Volatility): Represents investment risk (lower is better)
Y-axis (Total Return): Represents investment return (higher is better)
Dot Size: Based on Sharpe Ratio (larger = better risk-adjusted return)
Dot Color: Green = high Sharpe, Yellow = medium, Red = low Sharpe
Ideal Position: Upper-left quadrant (low risk, high return)

Files saved in: {}
""".format(output_dir.absolute()))
print("=" * 80)
