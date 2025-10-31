import json
from pathlib import Path
from datetime import datetime

# 读取JSON文件
data_path = "../data/models_data_1009_refreshed.json"
with open(data_path, "r") as f:
    data = json.load(f)

# 创建输出目录
output_dir = Path("../data/portfolio_snapshots")
output_dir.mkdir(exist_ok=True)

print(f"总共有 {len(data)} 个模型\n")

# 按类别分组
categories = {}
for model in data:
    category = model.get("category", "unknown")
    if category not in categories:
        categories[category] = []
    categories[category].append(model)

print("=" * 80)
print("类别统计:")
print("=" * 80)
for category, models in categories.items():
    print(f"{category}: {len(models)} 个模型")

print("\n" + "=" * 80)
print("性能排行榜（按利润率排序）:")
print("=" * 80)

# 按性能排序
sorted_models = sorted(data, key=lambda x: x.get("performance", 0), reverse=True)

print(f"{'排名':<5} {'模型ID':<35} {'类别':<12} {'性能%':<12} {'利润':<12} {'交易次数':<10}")
print("-" * 90)
for i, model in enumerate(sorted_models[:20], 1):  # 显示前20名
    model_id = model.get("id", "N/A")
    category = model.get("category", "N/A")
    performance = model.get("performance", 0)
    profit = model.get("profit", 0)
    trades = model.get("trades", 0)
    print(f"{i:<5} {model_id:<35} {category:<12} {performance:<12.2f} {profit:<12.2f} {trades:<10}")

# 查看特定模型的详细信息
print("\n" + "=" * 80)
print("示例：查看特定模型的详细信息")
print("=" * 80)

# 找一个stock模型作为示例
stock_models = [m for m in data if m.get("category") == "stock"]
if stock_models:
    example_model = stock_models[0]
    print(f"\n模型ID: {example_model['id']}")
    print(f"模型名称: {example_model['name']}")
    print(f"类别: {example_model['category']}")
    print(f"状态: {example_model['status']}")
    print(f"性能: {example_model['performance']:.2f}%")
    print(f"利润: ${example_model['profit']:.2f}")
    print(f"交易次数: {example_model['trades']}")
    
    print("\n资产分配:")
    for asset, allocation in example_model.get('asset_allocation', {}).items():
        print(f"  {asset}: {allocation*100:.2f}%")
    
    if 'portfolio' in example_model:
        portfolio = example_model['portfolio']
        print(f"\n投资组合:")
        print(f"  现金: ${portfolio.get('cash', 0):.2f}")
        print(f"  总价值: ${portfolio.get('total_value', 0):.2f}")
        print(f"  持仓数量: {len(portfolio.get('positions', {}))}")

# 辅助函数示例
print("\n" + "=" * 80)
print("辅助函数示例:")
print("=" * 80)

def get_model_by_id(data, model_id):
    """根据ID获取模型"""
    for model in data:
        if model.get("id") == model_id:
            return model
    return None

def get_models_by_category(data, category):
    """根据类别获取所有模型"""
    return [m for m in data if m.get("category") == category]

def get_top_performers(data, n=10, category=None):
    """获取性能最好的前N个模型"""
    filtered = data if category is None else [m for m in data if m.get("category") == category]
    return sorted(filtered, key=lambda x: x.get("performance", 0), reverse=True)[:n]

def calculate_average_performance(data, category=None):
    """计算平均性能"""
    filtered = data if category is None else [m for m in data if m.get("category") == category]
    if not filtered:
        return 0
    return sum(m.get("performance", 0) for m in filtered) / len(filtered)

# 使用示例
print(f"Stock类别的平均性能: {calculate_average_performance(data, 'stock'):.2f}%")
print(f"Benchmark类别的平均性能: {calculate_average_performance(data, 'benchmark'):.2f}%")

print("\n" + "=" * 80)
print("可以使用以下函数来获取数据:")
print("  - get_model_by_id(data, model_id)")
print("  - get_models_by_category(data, category)")
print("  - get_top_performers(data, n=10, category=None)")
print("  - calculate_average_performance(data, category=None)")
print("=" * 80)

# 提取所有模型的投资组合持仓信息并保存
print("\n" + "=" * 80)
print("保存所有投资组合持仓信息...")
print("=" * 80)

all_portfolio_snapshots = []

for model in data:
    model_id = model.get("id", "unknown")
    model_name = model.get("name", "unknown")
    category = model.get("category", "unknown")
    
    # 获取当前投资组合信息
    if "portfolio" in model:
        portfolio = model["portfolio"]
        positions = portfolio.get("positions", {})
        
        # 为每个持仓创建记录
        for symbol, position_data in positions.items():
            snapshot = {
                "model_id": model_id,
                "model_name": model_name,
                "category": category,
                "symbol": symbol,
                "quantity": position_data.get("quantity", 0),
                "average_price": position_data.get("average_price", 0),
                "current_price": position_data.get("current_price", 0),
                "market_value": position_data.get("quantity", 0) * position_data.get("current_price", 0),
                "url": position_data.get("url", ""),
                "timestamp": datetime.now().isoformat(),
                "portfolio_cash": portfolio.get("cash", 0),
                "portfolio_total_value": portfolio.get("total_value", 0)
            }
            all_portfolio_snapshots.append(snapshot)
    
    # 如果有历史交易记录，也提取带时间戳的持仓快照
    if "history" in model:
        for trade in model["history"]:
            if "portfolio_snapshot" in trade:
                snapshot_data = trade["portfolio_snapshot"]
                timestamp = trade.get("timestamp", datetime.now().isoformat())
                
                for symbol, position_data in snapshot_data.get("positions", {}).items():
                    historical_snapshot = {
                        "model_id": model_id,
                        "model_name": model_name,
                        "category": category,
                        "symbol": symbol,
                        "quantity": position_data.get("quantity", 0),
                        "average_price": position_data.get("average_price", 0),
                        "current_price": position_data.get("current_price", 0),
                        "market_value": position_data.get("quantity", 0) * position_data.get("current_price", 0),
                        "url": position_data.get("url", ""),
                        "timestamp": timestamp,
                        "portfolio_cash": snapshot_data.get("cash", 0),
                        "portfolio_total_value": snapshot_data.get("total_value", 0),
                        "is_historical": True
                    }
                    all_portfolio_snapshots.append(historical_snapshot)

# 保存到JSON文件
output_file = output_dir / f"all_positions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(output_file, "w") as f:
    json.dump(all_portfolio_snapshots, f, indent=2)

print(f"\n✓ 已保存 {len(all_portfolio_snapshots)} 条持仓记录到: {output_file}")

# 按模型分组保存
print("\n按模型分组保存持仓信息...")
portfolio_by_model = {}
for snapshot in all_portfolio_snapshots:
    model_id = snapshot["model_id"]
    if model_id not in portfolio_by_model:
        portfolio_by_model[model_id] = []
    portfolio_by_model[model_id].append(snapshot)

# 保存每个模型的持仓信息
for model_id, snapshots in portfolio_by_model.items():
    model_file = output_dir / f"{model_id.replace('/', '_')}_positions.json"
    with open(model_file, "w") as f:
        json.dump(snapshots, f, indent=2)

print(f"✓ 已为 {len(portfolio_by_model)} 个模型创建单独的持仓文件")

# 统计信息
print("\n" + "=" * 80)
print("持仓统计:")
print("=" * 80)
print(f"总持仓记录数: {len(all_portfolio_snapshots)}")
print(f"唯一股票代码数: {len(set(s['symbol'] for s in all_portfolio_snapshots))}")
print(f"有持仓的模型数: {len(portfolio_by_model)}")

# 显示前几条记录作为示例
print("\n前5条持仓记录示例:")
print("-" * 80)
for i, snapshot in enumerate(all_portfolio_snapshots[:5], 1):
    print(f"\n记录 {i}:")
    print(f"  模型: {snapshot['model_name']} ({snapshot['model_id']})")
    print(f"  股票: {snapshot['symbol']}")
    print(f"  数量: {snapshot['quantity']:.4f}")
    print(f"  当前价格: ${snapshot['current_price']:.2f}")
    print(f"  市值: ${snapshot['market_value']:.2f}")
    print(f"  时间戳: {snapshot['timestamp']}")

print("\n" + "=" * 80)
print(f"所有文件已保存到目录: {output_dir.absolute()}")
print("=" * 80)

# 取消注释下面这行来使用调试器
# breakpoint()