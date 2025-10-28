import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# Set seaborn theme
sns.set_theme(style="white")

# Data
data = {
    "Model": [
        "OpenAI GPT-o3", "OpenAI GPT-4.1", "OpenAI GPT-5",
        "Meta Llama4-Maverick", "Google Gemini-2.5-Flash", "Meta Llama4-Scout",
        "Anthropic Claude-Sonnet-4", "Anthropic Claude-Opus-4.1",
        "Qwen Qwen2.5-72B-Instruct", "Anthropic Claude-Opus-4",
        "xAI Grok-4", "Anthropic Claude-Sonnet-3.7",
        "Qwen Qwen3-235B-A22B-Instruct", "OpenAI GPT-4o",
        "Qwen Qwen3-235B-A22B-Thinking", "Google Gemini-2.5-Pro",
        "xAI Grok-3", "DeepSeek DeepSeek-R1", "Moonshot Kimi-K2-Instruct",
        "Meta Llama3.3-70B-Instruct-Turbo", "DeepSeek DeepSeek-V3.1"
    ],
    "LMArena": [
        1440, 1411, 1426, 1326, 1408, 1320, 1389, 1438,
        1300, 1412, 1415, 1385, 1371, 1343, 1397, 1452,
        1409, 1417, 1416, 1317, 1415
    ],
    "stock Return": [
        0.033, 0.031, 0.026, 0.024, 0.024, 0.023, 0.023, 0.021,
        0.019, 0.019, 0.019, 0.012, 0.009, 0.008, 0.008, 0.008,
        0.008, 0.007, 0.007, 0.002, -0.001
    ]
}

df = pd.DataFrame(data)

# Extract model family (remove company prefix)
def extract_model_family(full_name):
    # Remove company prefix
    parts = full_name.split(' ', 1)
    if len(parts) > 1:
        model_name = parts[1]
        # Extract family name (first word or pattern)
        if 'GPT' in model_name:
            family = 'GPT'
        elif 'Claude' in model_name:
            family = 'Claude'
        elif 'Llama' in model_name:
            family = 'Llama'
        elif 'Gemini' in model_name:
            family = 'Gemini'
        elif 'Grok' in model_name:
            family = 'Grok'
        elif 'DeepSeek' in model_name:
            family = 'DeepSeek'
        elif 'Qwen' in model_name:
            family = 'Qwen'
        elif 'Kimi' in model_name:
            family = 'Kimi'
        else:
            family = model_name.split('-')[0]
        return model_name, family
    return full_name, full_name

df['Model_Name'] = df['Model'].apply(lambda x: extract_model_family(x)[0])
df['Family'] = df['Model'].apply(lambda x: extract_model_family(x)[1])

# Assign colors to families (blue gradient for stock)
family_colors = {
    'GPT': ['#85C1E9', '#5DADE2', '#3498DB', '#2E86C1'],  # Light to dark blue
    'Claude': ['#A9CCE3', '#7FB3D5', '#5499C7', '#2874A6'],
    'Llama': ['#AED6F1', '#85C1E9', '#5DADE2', '#3498DB'],
    'Gemini': ['#D6EAF8', '#AED6F1', '#85C1E9', '#5DADE2'],
    'Grok': ['#5DADE2', '#3498DB', '#2E86C1', '#21618C'],
    'DeepSeek': ['#7FB3D5', '#5499C7', '#2874A6', '#1B4F72'],
    'Qwen': ['#85C1E9', '#5DADE2', '#3498DB', '#2E86C1'],
    'Kimi': ['#AED6F1', '#85C1E9', '#5DADE2', '#3498DB']
}

# Assign colors to each point based on family and performance rank within family
df['Color'] = '#2E5F8E'  # default
for family in df['Family'].unique():
    family_data = df[df['Family'] == family].sort_values('stock Return', ascending=False)
    colors = family_colors.get(family, ['#2E5F8E'])
    for idx, (i, row) in enumerate(family_data.iterrows()):
        color_idx = min(idx, len(colors) - 1)
        df.at[i, 'Color'] = colors[color_idx]

# Plot with Seaborn (square aspect, matching visualize_metrics.py)
fig, ax = plt.subplots(figsize=(14, 14))

# Plot each point with its family color
for idx, row in df.iterrows():
    ax.scatter(row['LMArena'], row['stock Return'], 
              s=800, alpha=0.7, color=row['Color'], 
              marker='^', linewidths=2, edgecolors='white', zorder=3)

# Add model names as labels (without company prefix)
x_median = df["LMArena"].median()
for i, row in df.iterrows():
    x_val = row["LMArena"]
    y_val = row["stock Return"]
    model_name = row["Model_Name"]
    
    # Smart positioning
    if x_val > x_median:
        text = f"{model_name}  "
        ha = 'right'
    else:
        text = f"  {model_name}"
        ha = 'left'
    
    ax.text(x_val, y_val, text,
           fontsize=20, va='center', ha=ha, zorder=4)

# Add y=x reference line for perfect correlation
x_min, x_max = ax.get_xlim()
y_min, y_max = ax.get_ylim()
ax.plot([x_min, x_max], [y_min, y_max], 'k--', alpha=0.3, linewidth=2, zorder=1)

# Style adjustments
ax.set_xlabel("LMArena Score", fontsize=44)
ax.set_ylabel("Stock Return Rate", fontsize=44)
ax.tick_params(labelsize=36, width=2, length=8)
ax.grid(False)

# Set spine style
for spine in ax.spines.values():
    spine.set_edgecolor('#34495e')
    spine.set_linewidth(2)

plt.tight_layout()
plt.savefig('../data/visualizations/correlation_lmarena_stock.pdf', 
           format='pdf', bbox_inches='tight', facecolor='white')
print("✓ Stock correlation plot saved to: ../data/visualizations/correlation_lmarena_stock.pdf")
plt.close()
