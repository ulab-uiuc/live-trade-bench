import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Read JSON file
data_path = "../data/models_data_50_days.json"
with open(data_path, "r") as f:
    data = json.load(f)

# Check data statistics
print("=" * 100)
print("Data File Check:")
print("=" * 100)
print(f"Total models: {len(data)}")

categories = {}
for model in data:
    cat = model.get('category', 'unknown')
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(model)

for cat, models in categories.items():
    if models:
        example = models[0]
        days = len(example.get('profitHistory', []))
        print(f"{cat.capitalize()}: {len(models)} models, {days} days of data")
print("=" * 100)
print()

# Risk-free rates (annualized)
RISK_FREE_RATE_STOCK = 0.04  # 4% for stock market (10-year US Treasury)
RISK_FREE_RATE_POLYMARKET = 0.00  # 0% for polymarket (short-term, high-risk environment)

def calculate_returns(profit_history: List[Dict]) -> np.ndarray:
    """Calculate daily returns from profit history"""
    if len(profit_history) < 2:
        return np.array([])
    
    returns = []
    for i in range(1, len(profit_history)):
        prev_value = profit_history[i-1]['totalValue']
        curr_value = profit_history[i]['totalValue']
        if prev_value > 0:
            daily_return = (curr_value - prev_value) / prev_value
            returns.append(daily_return)
    
    return np.array(returns)

def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = RISK_FREE_RATE_STOCK) -> float:
    """Calculate Sharpe Ratio (annualized)"""
    if len(returns) == 0 or np.std(returns) == 0:
        return 0.0
    
    # Convert daily returns to annualized
    mean_return = np.mean(returns) * 252  # 252 trading days
    std_return = np.std(returns) * np.sqrt(252)
    
    sharpe = (mean_return - risk_free_rate) / std_return
    return sharpe

def calculate_sortino_ratio(returns: np.ndarray, risk_free_rate: float = RISK_FREE_RATE_STOCK) -> float:
    """Calculate Sortino Ratio (annualized)"""
    if len(returns) == 0:
        return 0.0
    
    # Only consider downside volatility
    downside_returns = returns[returns < 0]
    if len(downside_returns) == 0:
        return float('inf')
    
    mean_return = np.mean(returns) * 252
    downside_std = np.std(downside_returns) * np.sqrt(252)
    
    if downside_std == 0:
        return float('inf')
    
    sortino = (mean_return - risk_free_rate) / downside_std
    return sortino

def calculate_max_drawdown(profit_history: List[Dict]) -> Tuple[float, int]:
    """Calculate maximum drawdown and drawdown days"""
    if len(profit_history) == 0:
        return 0.0, 0
    
    values = [h['totalValue'] for h in profit_history]
    peak = values[0]
    max_dd = 0.0
    max_dd_days = 0
    current_dd_days = 0
    
    for value in values:
        if value > peak:
            peak = value
            current_dd_days = 0
        else:
            drawdown = (peak - value) / peak
            current_dd_days += 1
            if drawdown > max_dd:
                max_dd = drawdown
                max_dd_days = current_dd_days
    
    return max_dd, max_dd_days

def calculate_win_rate(returns: np.ndarray) -> float:
    """Calculate win rate"""
    if len(returns) == 0:
        return 0.0
    
    winning_days = np.sum(returns > 0)
    return winning_days / len(returns)

def calculate_volatility(returns: np.ndarray) -> float:
    """Calculate volatility (annualized)"""
    if len(returns) == 0:
        return 0.0
    
    return np.std(returns) * np.sqrt(252)

def calculate_calmar_ratio(annual_return: float, max_drawdown: float) -> float:
    """Calculate Calmar Ratio"""
    if max_drawdown == 0:
        return float('inf')
    return annual_return / max_drawdown

def calculate_value_at_risk(returns: np.ndarray, confidence: float = 0.95) -> float:
    """Calculate VaR (Value at Risk)"""
    if len(returns) == 0:
        return 0.0
    
    return np.percentile(returns, (1 - confidence) * 100)

def calculate_consecutive_losses(returns: np.ndarray) -> int:
    """Calculate maximum consecutive loss days"""
    if len(returns) == 0:
        return 0
    
    max_consecutive = 0
    current_consecutive = 0
    
    for ret in returns:
        if ret < 0:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 0
    
    return max_consecutive

def calculate_all_metrics(model: Dict) -> Dict:
    """Calculate all metrics for a model"""
    profit_history = model.get('profitHistory', [])
    
    if len(profit_history) < 2:
        return {
            'model_id': model['id'],
            'model_name': model['name'],
            'category': model['category'],
            'error': 'Insufficient historical data'
        }
    
    returns = calculate_returns(profit_history)
    max_dd, max_dd_days = calculate_max_drawdown(profit_history)
    
    # Calculate annualized return
    initial_value = profit_history[0]['totalValue']
    final_value = profit_history[-1]['totalValue']
    days = len(profit_history)
    annual_return = ((final_value / initial_value) ** (252 / days) - 1) if days > 0 else 0
    
    # Select appropriate risk-free rate based on category
    category = model.get('category', '').lower()
    if category == 'polymarket':
        risk_free_rate = RISK_FREE_RATE_POLYMARKET
    else:  # stock or benchmark
        risk_free_rate = RISK_FREE_RATE_STOCK
    
    metrics = {
        'model_id': model['id'],
        'model_name': model['name'],
        'category': model['category'],
        'status': model.get('status', 'unknown'),
        'risk_free_rate': risk_free_rate,  # Store which rate was used
        
        # Basic metrics
        'total_return_pct': model.get('performance', 0),
        'profit_usd': model.get('profit', 0),
        'trades': model.get('trades', 0),
        'days_traded': len(profit_history),
        
        # Return metrics
        'annual_return_pct': annual_return * 100,
        'avg_daily_return_pct': np.mean(returns) * 100 if len(returns) > 0 else 0,
        
        # Risk-adjusted metrics (using category-specific risk-free rate)
        'sharpe_ratio': calculate_sharpe_ratio(returns, risk_free_rate),
        'sortino_ratio': calculate_sortino_ratio(returns, risk_free_rate),
        'calmar_ratio': calculate_calmar_ratio(annual_return, max_dd),
        
        # Risk metrics
        'volatility_annual_pct': calculate_volatility(returns) * 100,
        'max_drawdown_pct': max_dd * 100,
        'max_drawdown_days': max_dd_days,
        'var_95_pct': calculate_value_at_risk(returns) * 100,
        
        # Robustness metrics
        'win_rate_pct': calculate_win_rate(returns) * 100,
        'max_consecutive_losses': calculate_consecutive_losses(returns),
        
        # Portfolio metrics
        'final_portfolio_value': final_value,
        'initial_portfolio_value': initial_value,
    }
    
    return metrics

# Calculate metrics for all models
print("=" * 100)
print("Calculating risk and robustness metrics for all models...")
print("=" * 100)

all_metrics = []
for model in data:
    metrics = calculate_all_metrics(model)
    all_metrics.append(metrics)
    
print(f"✓ Calculated metrics for {len(all_metrics)} models\n")

# Calculate overall composite scores
def calculate_composite_score(metrics_list: List[Dict]) -> List[Dict]:
    """
    Calculate composite performance score based on 5 key metrics:
    - CR (Total Return): higher is better
    - SR (Sharpe Ratio): higher is better  
    - MDD (Max Drawdown): lower is better
    - WR (Win Rate): higher is better
    - σ (Volatility): lower is better
    
    Each metric is normalized to 0-1 scale, then averaged with equal weights (0.2 each)
    """
    if len(metrics_list) == 0:
        return metrics_list
    
    # Extract metrics for normalization
    returns = np.array([m['total_return_pct'] for m in metrics_list])
    sharpes = np.array([m['sharpe_ratio'] for m in metrics_list])
    mdds = np.array([m['max_drawdown_pct'] for m in metrics_list])
    winrates = np.array([m['win_rate_pct'] for m in metrics_list])
    vols = np.array([m['volatility_annual_pct'] for m in metrics_list])
    
    # Min-max normalization (0-1 scale)
    def normalize(x):
        x_min, x_max = x.min(), x.max()
        if x_max == x_min:
            return np.ones_like(x) * 0.5
        return (x - x_min) / (x_max - x_min)
    
    # Normalize each metric
    cr_norm = normalize(returns)  # Higher is better
    sr_norm = normalize(sharpes)  # Higher is better
    mdd_norm = 1 - normalize(mdds)  # Lower is better (invert)
    wr_norm = normalize(winrates)  # Higher is better
    vol_norm = 1 - normalize(vols)  # Lower is better (invert)
    
    # Calculate composite score (equal weights: 0.2 each)
    weights = {'cr': 0.2, 'sr': 0.2, 'mdd': 0.2, 'wr': 0.2, 'vol': 0.2}
    
    for i, m in enumerate(metrics_list):
        composite = (
            weights['cr'] * cr_norm[i] +
            weights['sr'] * sr_norm[i] +
            weights['mdd'] * mdd_norm[i] +
            weights['wr'] * wr_norm[i] +
            weights['vol'] * vol_norm[i]
        )
        m['composite_score'] = composite * 100  # Scale to 0-100
        m['score_components'] = {
            'cr_normalized': float(cr_norm[i]),
            'sr_normalized': float(sr_norm[i]),
            'mdd_normalized': float(mdd_norm[i]),
            'wr_normalized': float(wr_norm[i]),
            'vol_normalized': float(vol_norm[i])
        }
    
    return metrics_list

# Group by category
stock_metrics = [m for m in all_metrics if m['category'] == 'stock' and 'error' not in m]
polymarket_metrics = [m for m in all_metrics if m['category'] == 'polymarket' and 'error' not in m]
benchmark_metrics = [m for m in all_metrics if m['category'] == 'benchmark' and 'error' not in m]

# Calculate composite scores
stock_metrics = calculate_composite_score(stock_metrics)
polymarket_metrics = calculate_composite_score(polymarket_metrics)

# Display stock market metrics
print("=" * 110)
print(f"Stock Market Models - Sorted by Composite Score (Total: {len(stock_metrics)})")
print("=" * 110)
print(f"{'Rank':<5} {'Model Name':<30} {'Score':<8} {'Return%':<10} {'Sharpe':<10} {'MaxDD%':<10} {'WinRate%':<10} {'Vol%':<10}")
print("-" * 110)

stock_sorted = sorted(stock_metrics, key=lambda x: x['composite_score'], reverse=True)
for i, m in enumerate(stock_sorted, 1):
    print(f"{i:<5} {m['model_name'][:28]:<30} {m['composite_score']:<8.2f} {m['total_return_pct']:<10.2f} {m['sharpe_ratio']:<10.2f} "
          f"{m['max_drawdown_pct']:<10.2f} {m['win_rate_pct']:<10.2f} {m['volatility_annual_pct']:<10.2f}")

# Display Polymarket metrics
print("\n" + "=" * 110)
print(f"Polymarket Models - Sorted by Composite Score (Total: {len(polymarket_metrics)})")
print("=" * 110)
print(f"{'Rank':<5} {'Model Name':<30} {'Score':<8} {'Return%':<10} {'Sharpe':<10} {'MaxDD%':<10} {'WinRate%':<10} {'Vol%':<10}")
print("-" * 110)

poly_sorted = sorted(polymarket_metrics, key=lambda x: x['composite_score'], reverse=True)
for i, m in enumerate(poly_sorted, 1):
    print(f"{i:<5} {m['model_name'][:28]:<30} {m['composite_score']:<8.2f} {m['total_return_pct']:<10.2f} {m['sharpe_ratio']:<10.2f} "
          f"{m['max_drawdown_pct']:<10.2f} {m['win_rate_pct']:<10.2f} {m['volatility_annual_pct']:<10.2f}")

# Display benchmark metrics
print("\n" + "=" * 100)
print("Benchmark Indices")
print("=" * 100)
print(f"{'Name':<30} {'Return%':<10} {'Sharpe':<10} {'MaxDD%':<12} {'WinRate%':<10} {'Vol%':<10}")
print("-" * 100)

for m in benchmark_metrics:
    print(f"{m['model_name'][:28]:<30} {m['total_return_pct']:<10.2f} {m['sharpe_ratio']:<10.2f} "
          f"{m['max_drawdown_pct']:<12.2f} {m['win_rate_pct']:<10.2f} {m['volatility_annual_pct']:<10.2f}")

# Statistical comparison
print("\n" + "=" * 100)
print("Category Statistical Comparison")
print("=" * 100)

def print_category_stats(metrics_list: List[Dict], category_name: str):
    if len(metrics_list) == 0:
        print(f"\n{category_name}: No data")
        return
    
    print(f"\n{category_name} ({len(metrics_list)} models):")
    print("-" * 100)
    
    stats = {
        'Avg Return%': np.mean([m['total_return_pct'] for m in metrics_list]),
        'Median Return%': np.median([m['total_return_pct'] for m in metrics_list]),
        'Avg Sharpe Ratio': np.mean([m['sharpe_ratio'] for m in metrics_list]),
        'Median Sharpe Ratio': np.median([m['sharpe_ratio'] for m in metrics_list]),
        'Avg Max Drawdown%': np.mean([m['max_drawdown_pct'] for m in metrics_list]),
        'Avg Win Rate%': np.mean([m['win_rate_pct'] for m in metrics_list]),
        'Avg Volatility%': np.mean([m['volatility_annual_pct'] for m in metrics_list]),
        'Avg Calmar Ratio': np.mean([m['calmar_ratio'] for m in metrics_list if not np.isinf(m['calmar_ratio'])]),
        'Avg VaR(95%)%': np.mean([m['var_95_pct'] for m in metrics_list]),
        'Avg Max Consecutive Losses': np.mean([m['max_consecutive_losses'] for m in metrics_list]),
    }
    
    for key, value in stats.items():
        print(f"  {key:<28}: {value:>10.2f}")

print_category_stats(stock_metrics, "Stock Market")
print_category_stats(polymarket_metrics, "Polymarket")
print_category_stats(benchmark_metrics, "Benchmark")

# Save detailed metrics to JSON
output_dir = Path("../data/metrics")
output_dir.mkdir(exist_ok=True)

output_file = output_dir / f"all_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(output_file, "w") as f:
    json.dump(all_metrics, f, indent=2)

print("\n" + "=" * 100)
print(f"✓ All metrics saved to: {output_file}")
print("=" * 100)

# Save metrics grouped by category
for category, metrics_list in [('stock', stock_metrics), ('polymarket', polymarket_metrics), ('benchmark', benchmark_metrics)]:
    if metrics_list:
        category_file = output_dir / f"{category}_metrics.json"
        with open(category_file, "w") as f:
            json.dump(metrics_list, f, indent=2)
        print(f"\n✓ {category} metrics saved to: {category_file}")

# Generate detailed report
print("\n" + "=" * 100)
print("Detailed Metrics Explanation:")
print("=" * 100)
print("""
1. Composite Score: Overall performance score (0-100) based on 5 key metrics with equal weights:
   - Total Return (20%): Cumulative return, higher is better
   - Sharpe Ratio (20%): Risk-adjusted return, higher is better
   - Max Drawdown (20%): Maximum loss, lower is better (inverted in score)
   - Win Rate (20%): Percentage of profitable days, higher is better
   - Volatility (20%): Price fluctuation, lower is better (inverted in score)
   
2. Sharpe Ratio: Measures risk-adjusted return, higher is better (>1 is good, >2 is excellent)
3. Calmar Ratio: Annualized return divided by maximum drawdown, higher is better
4. Max Drawdown: Maximum loss from peak to trough, lower is better
5. Win Rate: Percentage of profitable trading days
6. Volatility: Annualized standard deviation of returns, measures risk
7. VaR (Value at Risk): Maximum loss at 95% confidence level
8. Max Consecutive Losses: Robustness metric, lower is better
""")

