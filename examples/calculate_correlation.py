import json
import numpy as np
from scipy import stats
from pathlib import Path

# Read metrics files
data_dir = Path("../data/metrics")
stock_file = data_dir / "stock_metrics.json"
polymarket_file = data_dir / "polymarket_metrics.json"

with open(stock_file, "r") as f:
    stock_metrics = json.load(f)

with open(polymarket_file, "r") as f:
    polymarket_metrics = json.load(f)

print("=" * 100)
print("Sharpe Ratio Correlation Analysis: Stock vs Polymarket")
print("=" * 100)

# Extract model names (removing company prefixes for matching)
def clean_model_name(name):
    """Remove company prefix from model name"""
    prefixes = ["OpenAI ", "Anthropic ", "Google ", "Meta ", "xAI ", "DeepSeek ", "Alibaba "]
    for prefix in prefixes:
        if name.startswith(prefix):
            return name[len(prefix):]
    return name

# Create dictionaries for easy lookup
stock_dict = {clean_model_name(m['model_name']): m for m in stock_metrics}
poly_dict = {clean_model_name(m['model_name']): m for m in polymarket_metrics}

# Find common models
common_models = set(stock_dict.keys()) & set(poly_dict.keys())

print(f"\nTotal stock models: {len(stock_metrics)}")
print(f"Total polymarket models: {len(polymarket_metrics)}")
print(f"Common models: {len(common_models)}")

if len(common_models) == 0:
    print("\n⚠️  No common models found between stock and polymarket!")
    print("\nStock models:")
    for name in sorted(stock_dict.keys())[:10]:
        print(f"  - {name}")
    print("\nPolymarket models:")
    for name in sorted(poly_dict.keys())[:10]:
        print(f"  - {name}")
else:
    # Extract Sharpe ratios for common models
    stock_sharpes = []
    poly_sharpes = []
    model_names = []
    
    for model_name in sorted(common_models):
        stock_sr = stock_dict[model_name]['sharpe_ratio']
        poly_sr = poly_dict[model_name]['sharpe_ratio']
        
        stock_sharpes.append(stock_sr)
        poly_sharpes.append(poly_sr)
        model_names.append(model_name)
    
    # Convert to numpy arrays
    stock_sharpes = np.array(stock_sharpes)
    poly_sharpes = np.array(poly_sharpes)
    
    # Calculate correlations - Overall
    pearson_corr, pearson_p = stats.pearsonr(stock_sharpes, poly_sharpes)
    spearman_corr, spearman_p = stats.spearmanr(stock_sharpes, poly_sharpes)
    
    # Sort by stock sharpe ratio for top/bottom analysis
    sorted_indices = np.argsort(stock_sharpes)[::-1]
    
    # Top-10 models
    top10_indices = sorted_indices[:10]
    top10_stock = stock_sharpes[top10_indices]
    top10_poly = poly_sharpes[top10_indices]
    
    if len(top10_stock) >= 3:  # Need at least 3 points for correlation
        top10_pearson, top10_pearson_p = stats.pearsonr(top10_stock, top10_poly)
        top10_spearman, top10_spearman_p = stats.spearmanr(top10_stock, top10_poly)
    else:
        top10_pearson = top10_pearson_p = top10_spearman = top10_spearman_p = np.nan
    
    # Bottom-10 models
    bottom10_indices = sorted_indices[-10:]
    bottom10_stock = stock_sharpes[bottom10_indices]
    bottom10_poly = poly_sharpes[bottom10_indices]
    
    if len(bottom10_stock) >= 3:
        bottom10_pearson, bottom10_pearson_p = stats.pearsonr(bottom10_stock, bottom10_poly)
        bottom10_spearman, bottom10_spearman_p = stats.spearmanr(bottom10_stock, bottom10_poly)
    else:
        bottom10_pearson = bottom10_pearson_p = bottom10_spearman = bottom10_spearman_p = np.nan
    
    print("\n" + "=" * 100)
    print("Correlation Results: Overall")
    print("=" * 100)
    print(f"Pearson Correlation:   {pearson_corr:.4f}  (p-value: {pearson_p:.4e})")
    print(f"Spearman Correlation:  {spearman_corr:.4f}  (p-value: {spearman_p:.4e})")
    print(f"Sample size: {len(stock_sharpes)} models")
    
    print("\n" + "=" * 100)
    print("Correlation Results: Top-10 Models (by Stock Sharpe Ratio)")
    print("=" * 100)
    if not np.isnan(top10_pearson):
        print(f"Pearson Correlation:   {top10_pearson:.4f}  (p-value: {top10_pearson_p:.4e})")
        print(f"Spearman Correlation:  {top10_spearman:.4f}  (p-value: {top10_spearman_p:.4e})")
        print(f"Sample size: {len(top10_stock)} models")
    else:
        print("Insufficient data for correlation")
    
    print("\n" + "=" * 100)
    print("Correlation Results: Bottom-10 Models (by Stock Sharpe Ratio)")
    print("=" * 100)
    if not np.isnan(bottom10_pearson):
        print(f"Pearson Correlation:   {bottom10_pearson:.4f}  (p-value: {bottom10_pearson_p:.4e})")
        print(f"Spearman Correlation:  {bottom10_spearman:.4f}  (p-value: {bottom10_spearman_p:.4e})")
        print(f"Sample size: {len(bottom10_stock)} models")
    else:
        print("Insufficient data for correlation")
    
    # Interpretation
    print("\n" + "=" * 100)
    print("Interpretation")
    print("=" * 100)
    
    def interpret_correlation(corr, p_value, label):
        if p_value < 0.001:
            sig = "***"
        elif p_value < 0.01:
            sig = "**"
        elif p_value < 0.05:
            sig = "*"
        else:
            sig = "not significant"
        
        if abs(corr) > 0.7:
            strength = "Strong"
        elif abs(corr) > 0.4:
            strength = "Moderate"
        elif abs(corr) > 0.2:
            strength = "Weak"
        else:
            strength = "Very weak"
        
        direction = "positive" if corr > 0 else "negative"
        
        print(f"\n{label}:")
        print(f"  {strength} {direction} correlation ({sig})")
        print(f"  r = {corr:.4f}, p = {p_value:.4e}")
    
    interpret_correlation(pearson_corr, pearson_p, "Overall Correlation")
    
    if not np.isnan(top10_pearson):
        interpret_correlation(top10_pearson, top10_pearson_p, "Top-10 Models Correlation")
    
    if not np.isnan(bottom10_pearson):
        interpret_correlation(bottom10_pearson, bottom10_pearson_p, "Bottom-10 Models Correlation")
    
    print(f"\n{'=' * 100}")
    print("Key Insights:")
    print("=" * 100)
    print(f"• Overall: Models with {'higher' if pearson_corr > 0 else 'lower'} Sharpe Ratios in stock market")
    print(f"  tend to {'also have higher' if pearson_corr > 0 else 'have lower'} Sharpe Ratios in polymarket")
    
    if not np.isnan(top10_pearson) and not np.isnan(bottom10_pearson):
        if abs(top10_pearson) > abs(bottom10_pearson):
            print(f"• Top performers show STRONGER correlation (r={top10_pearson:.4f}) than bottom performers (r={bottom10_pearson:.4f})")
        else:
            print(f"• Bottom performers show STRONGER correlation (r={bottom10_pearson:.4f}) than top performers (r={top10_pearson:.4f})")
        
        if (top10_pearson > 0) == (bottom10_pearson > 0):
            print(f"• Both groups show {('positive' if top10_pearson > 0 else 'negative')} correlation")
        else:
            print(f"• Top performers: {('positive' if top10_pearson > 0 else 'negative')}, Bottom performers: {('positive' if bottom10_pearson > 0 else 'negative')} - different patterns!")
    
    # Statistical summary
    print("\n" + "=" * 100)
    print("Statistical Summary")
    print("=" * 100)
    print(f"{'Metric':<30} {'Stock':<15} {'Polymarket':<15}")
    print("-" * 100)
    print(f"{'Mean Sharpe Ratio':<30} {np.mean(stock_sharpes):<15.4f} {np.mean(poly_sharpes):<15.4f}")
    print(f"{'Median Sharpe Ratio':<30} {np.median(stock_sharpes):<15.4f} {np.median(poly_sharpes):<15.4f}")
    print(f"{'Std Dev':<30} {np.std(stock_sharpes):<15.4f} {np.std(poly_sharpes):<15.4f}")
    print(f"{'Min':<30} {np.min(stock_sharpes):<15.4f} {np.min(poly_sharpes):<15.4f}")
    print(f"{'Max':<30} {np.max(stock_sharpes):<15.4f} {np.max(poly_sharpes):<15.4f}")
    
    # Show top and bottom performers
    print("\n" + "=" * 100)
    print("Model-by-Model Comparison (Top 10 by Stock Sharpe Ratio)")
    print("=" * 100)
    print(f"{'Rank':<5} {'Model Name':<35} {'Stock SR':<12} {'Poly SR':<12} {'Difference':<12}")
    print("-" * 100)
    
    for i, idx in enumerate(sorted_indices[:10], 1):
        model = model_names[idx]
        stock_sr = stock_sharpes[idx]
        poly_sr = poly_sharpes[idx]
        diff = stock_sr - poly_sr
        
        print(f"{i:<5} {model[:33]:<35} {stock_sr:<12.4f} {poly_sr:<12.4f} {diff:<+12.4f}")
    
    print("\n" + "=" * 100)
    print("Model-by-Model Comparison (Bottom 10 by Stock Sharpe Ratio)")
    print("=" * 100)
    print(f"{'Rank':<5} {'Model Name':<35} {'Stock SR':<12} {'Poly SR':<12} {'Difference':<12}")
    print("-" * 100)
    
    for i, idx in enumerate(sorted_indices[-10:][::-1], 1):
        model = model_names[idx]
        stock_sr = stock_sharpes[idx]
        poly_sr = poly_sharpes[idx]
        diff = stock_sr - poly_sr
        
        print(f"{i:<5} {model[:33]:<35} {stock_sr:<12.4f} {poly_sr:<12.4f} {diff:<+12.4f}")
    
    # Save correlation data
    correlation_data = {
        'overall': {
            'pearson_correlation': float(pearson_corr),
            'pearson_p_value': float(pearson_p),
            'spearman_correlation': float(spearman_corr),
            'spearman_p_value': float(spearman_p),
            'n_models': len(common_models)
        },
        'top10': {
            'pearson_correlation': float(top10_pearson) if not np.isnan(top10_pearson) else None,
            'pearson_p_value': float(top10_pearson_p) if not np.isnan(top10_pearson_p) else None,
            'spearman_correlation': float(top10_spearman) if not np.isnan(top10_spearman) else None,
            'spearman_p_value': float(top10_spearman_p) if not np.isnan(top10_spearman_p) else None,
            'n_models': len(top10_stock)
        },
        'bottom10': {
            'pearson_correlation': float(bottom10_pearson) if not np.isnan(bottom10_pearson) else None,
            'pearson_p_value': float(bottom10_pearson_p) if not np.isnan(bottom10_pearson_p) else None,
            'spearman_correlation': float(bottom10_spearman) if not np.isnan(bottom10_spearman) else None,
            'spearman_p_value': float(bottom10_spearman_p) if not np.isnan(bottom10_spearman_p) else None,
            'n_models': len(bottom10_stock)
        },
        'models': [
            {
                'model_name': model_names[i],
                'stock_sharpe_ratio': float(stock_sharpes[i]),
                'polymarket_sharpe_ratio': float(poly_sharpes[i]),
                'difference': float(stock_sharpes[i] - poly_sharpes[i])
            }
            for i in range(len(model_names))
        ]
    }
    
    output_file = data_dir / "sharpe_correlation.json"
    with open(output_file, "w") as f:
        json.dump(correlation_data, f, indent=2)
    
    print("\n" + "=" * 100)
    print(f"✓ Correlation data saved to: {output_file}")
    print("=" * 100)

