import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# 读取JSON文件
data_path = "../data/models_data_1009_refreshed.json"
with open(data_path, "r") as f:
    data = json.load(f)

# 无风险利率（年化，假设为4%）
RISK_FREE_RATE = 0.04

def calculate_returns(profit_history: List[Dict]) -> np.ndarray:
    """从利润历史计算日收益率"""
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

def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = RISK_FREE_RATE) -> float:
    """计算夏普比率（年化）"""
    if len(returns) == 0 or np.std(returns) == 0:
        return 0.0
    
    # 日收益率转年化
    mean_return = np.mean(returns) * 252  # 252个交易日
    std_return = np.std(returns) * np.sqrt(252)
    
    sharpe = (mean_return - risk_free_rate) / std_return
    return sharpe

def calculate_sortino_ratio(returns: np.ndarray, risk_free_rate: float = RISK_FREE_RATE) -> float:
    """计算索提诺比率（年化）"""
    if len(returns) == 0:
        return 0.0
    
    # 只考虑下行波动
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
    """计算最大回撤和回撤天数"""
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
    """计算胜率"""
    if len(returns) == 0:
        return 0.0
    
    winning_days = np.sum(returns > 0)
    return winning_days / len(returns)

def calculate_volatility(returns: np.ndarray) -> float:
    """计算波动率（年化）"""
    if len(returns) == 0:
        return 0.0
    
    return np.std(returns) * np.sqrt(252)

def calculate_calmar_ratio(annual_return: float, max_drawdown: float) -> float:
    """计算卡尔马比率"""
    if max_drawdown == 0:
        return float('inf')
    return annual_return / max_drawdown

def calculate_value_at_risk(returns: np.ndarray, confidence: float = 0.95) -> float:
    """计算VaR（Value at Risk）"""
    if len(returns) == 0:
        return 0.0
    
    return np.percentile(returns, (1 - confidence) * 100)

def calculate_consecutive_losses(returns: np.ndarray) -> int:
    """计算最大连续亏损天数"""
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
    """计算模型的所有指标"""
    profit_history = model.get('profitHistory', [])
    
    if len(profit_history) < 2:
        return {
            'model_id': model['id'],
            'model_name': model['name'],
            'category': model['category'],
            'error': '历史数据不足'
        }
    
    returns = calculate_returns(profit_history)
    max_dd, max_dd_days = calculate_max_drawdown(profit_history)
    
    # 计算年化收益率
    initial_value = profit_history[0]['totalValue']
    final_value = profit_history[-1]['totalValue']
    days = len(profit_history)
    annual_return = ((final_value / initial_value) ** (252 / days) - 1) if days > 0 else 0
    
    metrics = {
        'model_id': model['id'],
        'model_name': model['name'],
        'category': model['category'],
        'status': model.get('status', 'unknown'),
        
        # 基础指标
        'total_return_pct': model.get('performance', 0),
        'profit_usd': model.get('profit', 0),
        'trades': model.get('trades', 0),
        'days_traded': len(profit_history),
        
        # 收益指标
        'annual_return_pct': annual_return * 100,
        'avg_daily_return_pct': np.mean(returns) * 100 if len(returns) > 0 else 0,
        
        # 风险调整指标
        'sharpe_ratio': calculate_sharpe_ratio(returns),
        'sortino_ratio': calculate_sortino_ratio(returns),
        'calmar_ratio': calculate_calmar_ratio(annual_return, max_dd),
        
        # 风险指标
        'volatility_annual_pct': calculate_volatility(returns) * 100,
        'max_drawdown_pct': max_dd * 100,
        'max_drawdown_days': max_dd_days,
        'var_95_pct': calculate_value_at_risk(returns) * 100,
        
        # 稳健性指标
        'win_rate_pct': calculate_win_rate(returns) * 100,
        'max_consecutive_losses': calculate_consecutive_losses(returns),
        
        # 投资组合指标
        'final_portfolio_value': final_value,
        'initial_portfolio_value': initial_value,
    }
    
    return metrics

# 计算所有模型的指标
print("=" * 100)
print("计算所有模型的风险和稳健性指标...")
print("=" * 100)

all_metrics = []
for model in data:
    metrics = calculate_all_metrics(model)
    all_metrics.append(metrics)
    
print(f"✓ 已计算 {len(all_metrics)} 个模型的指标\n")

# 按类别分组
stock_metrics = [m for m in all_metrics if m['category'] == 'stock' and 'error' not in m]
polymarket_metrics = [m for m in all_metrics if m['category'] == 'polymarket' and 'error' not in m]
benchmark_metrics = [m for m in all_metrics if m['category'] == 'benchmark' and 'error' not in m]

# 显示股票市场指标
print("=" * 100)
print("股票市场模型 - 按夏普比率排序（前20名）")
print("=" * 100)
print(f"{'排名':<5} {'模型名称':<30} {'收益%':<10} {'夏普':<10} {'索提诺':<10} {'最大回撤%':<12} {'胜率%':<10} {'波动率%':<10}")
print("-" * 100)

stock_sorted = sorted(stock_metrics, key=lambda x: x['sharpe_ratio'], reverse=True)
for i, m in enumerate(stock_sorted[:20], 1):
    print(f"{i:<5} {m['model_name'][:28]:<30} {m['total_return_pct']:<10.2f} {m['sharpe_ratio']:<10.2f} "
          f"{m['sortino_ratio']:<10.2f} {m['max_drawdown_pct']:<12.2f} {m['win_rate_pct']:<10.2f} {m['volatility_annual_pct']:<10.2f}")

# 显示Polymarket指标
print("\n" + "=" * 100)
print("Polymarket模型 - 按夏普比率排序（前20名）")
print("=" * 100)
print(f"{'排名':<5} {'模型名称':<30} {'收益%':<10} {'夏普':<10} {'索提诺':<10} {'最大回撤%':<12} {'胜率%':<10} {'波动率%':<10}")
print("-" * 100)

poly_sorted = sorted(polymarket_metrics, key=lambda x: x['sharpe_ratio'], reverse=True)
for i, m in enumerate(poly_sorted[:20], 1):
    print(f"{i:<5} {m['model_name'][:28]:<30} {m['total_return_pct']:<10.2f} {m['sharpe_ratio']:<10.2f} "
          f"{m['sortino_ratio']:<10.2f} {m['max_drawdown_pct']:<12.2f} {m['win_rate_pct']:<10.2f} {m['volatility_annual_pct']:<10.2f}")

# 显示基准指标
print("\n" + "=" * 100)
print("基准指数（Benchmark）")
print("=" * 100)
print(f"{'名称':<30} {'收益%':<10} {'夏普':<10} {'索提诺':<10} {'最大回撤%':<12} {'胜率%':<10} {'波动率%':<10}")
print("-" * 100)

for m in benchmark_metrics:
    print(f"{m['model_name'][:28]:<30} {m['total_return_pct']:<10.2f} {m['sharpe_ratio']:<10.2f} "
          f"{m['sortino_ratio']:<10.2f} {m['max_drawdown_pct']:<12.2f} {m['win_rate_pct']:<10.2f} {m['volatility_annual_pct']:<10.2f}")

# 统计对比
print("\n" + "=" * 100)
print("类别统计对比")
print("=" * 100)

def print_category_stats(metrics_list: List[Dict], category_name: str):
    if len(metrics_list) == 0:
        print(f"\n{category_name}: 无数据")
        return
    
    print(f"\n{category_name} ({len(metrics_list)} 个模型):")
    print("-" * 100)
    
    stats = {
        '平均收益率%': np.mean([m['total_return_pct'] for m in metrics_list]),
        '中位收益率%': np.median([m['total_return_pct'] for m in metrics_list]),
        '平均夏普比率': np.mean([m['sharpe_ratio'] for m in metrics_list]),
        '中位夏普比率': np.median([m['sharpe_ratio'] for m in metrics_list]),
        '平均索提诺比率': np.mean([m['sortino_ratio'] for m in metrics_list if not np.isinf(m['sortino_ratio'])]),
        '平均最大回撤%': np.mean([m['max_drawdown_pct'] for m in metrics_list]),
        '平均胜率%': np.mean([m['win_rate_pct'] for m in metrics_list]),
        '平均波动率%': np.mean([m['volatility_annual_pct'] for m in metrics_list]),
        '平均卡尔马比率': np.mean([m['calmar_ratio'] for m in metrics_list if not np.isinf(m['calmar_ratio'])]),
        '平均VaR(95%)%': np.mean([m['var_95_pct'] for m in metrics_list]),
        '平均最大连续亏损天数': np.mean([m['max_consecutive_losses'] for m in metrics_list]),
    }
    
    for key, value in stats.items():
        print(f"  {key:<25}: {value:>10.2f}")

print_category_stats(stock_metrics, "股票市场")
print_category_stats(polymarket_metrics, "Polymarket")
print_category_stats(benchmark_metrics, "基准指数")

# 保存详细指标到JSON
output_dir = Path("../data/metrics")
output_dir.mkdir(exist_ok=True)

output_file = output_dir / f"all_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(output_file, "w") as f:
    json.dump(all_metrics, f, indent=2)

print("\n" + "=" * 100)
print(f"✓ 所有指标已保存到: {output_file}")
print("=" * 100)

# 保存按类别分组的指标
for category, metrics_list in [('stock', stock_metrics), ('polymarket', polymarket_metrics), ('benchmark', benchmark_metrics)]:
    if metrics_list:
        category_file = output_dir / f"{category}_metrics.json"
        with open(category_file, "w") as f:
            json.dump(metrics_list, f, indent=2)
        print(f"✓ {category} 指标已保存到: {category_file}")

# 生成详细报告
print("\n" + "=" * 100)
print("详细指标说明:")
print("=" * 100)
print("""
1. 夏普比率 (Sharpe Ratio): 衡量风险调整后的收益，越高越好（>1为优秀，>2为非常优秀）
2. 索提诺比率 (Sortino Ratio): 类似夏普比率，但只考虑下行风险
3. 卡尔马比率 (Calmar Ratio): 年化收益率除以最大回撤，越高越好
4. 最大回撤 (Max Drawdown): 从峰值到谷值的最大跌幅，越小越好
5. 胜率 (Win Rate): 盈利交易天数占比
6. 波动率 (Volatility): 年化收益率标准差，衡量风险
7. VaR (Value at Risk): 95%置信度下的最大损失
8. 最大连续亏损天数: 稳健性指标，越小越好
""")

