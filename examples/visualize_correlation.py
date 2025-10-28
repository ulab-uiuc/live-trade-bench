import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# Set seaborn theme
sns.set_theme(style="white")

# Data (from table)
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
    "Stock SR": [
        2.57, 2.64, 2.19, 1.65, 0.72, 1.99, 0.72, 1.51,
        2.18, 1.72, 1.75, 1.45, 1.32, 1.39, 0.60, 0.61,
        1.26, 0.78, 1.15, 0.88, 0.86
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

# Assign distinct colors to each family (Stock - cool colors: blue, green, teal)
family_colors = {
    'GPT': '#1565C0',        # Blue
    'Claude': '#0288D1',     # Light blue
    'Llama': '#00695C',      # Teal
    'Gemini': '#2E7D32',     # Green
    'Grok': '#0277BD',       # Sky blue
    'DeepSeek': '#004D40',   # Dark teal
    'Qwen': '#00796B',       # Medium teal
    'Kimi': '#0097A7'        # Cyan
}

# Assign colors to each point based on family
df['Color'] = '#2E5F8E'  # default
for family in df['Family'].unique():
    color = family_colors.get(family, '#2E5F8E')
    df.loc[df['Family'] == family, 'Color'] = color

# Plot with Seaborn (square aspect, matching visualize_metrics.py)
fig, ax = plt.subplots(figsize=(14, 14))

# Plot each point with its family color
for idx, row in df.iterrows():
    ax.scatter(row['LMArena'], row['Stock SR'], 
              s=2000, alpha=0.7, color=row['Color'], 
              marker='^', linewidths=2, edgecolors='white', zorder=3)

# Manual position offsets for each model (x_offset, y_offset)
# You can edit these values to adjust label positions
position_offsets = {
    "GPT-o3": (0, 0),
    "GPT-4.1": (0, 0),
    "GPT-5": (0, 0),
    "Llama4-Maverick": (0, 0),
    "Gemini-2.5-Flash": (0, 0),
    "Llama4-Scout": (0, 0),
    "Claude-Sonnet-4": (-60, 0),
    "Claude-Opus-4.1": (0, 0.05),
    "Qwen2.5-72B-Instruct": (0, 0),
    "Claude-Opus-4": (0, 0),
    "Grok-4": (30, 0),
    "Claude-Sonnet-3.7": (0, -0.03),
    "Qwen3-235B-A22B-Instruct": (0, 0),
    "GPT-4o": (0, 0),
    "Qwen3-235B-A22B-Thinking": (-84, 0),
    "Gemini-2.5-Pro": (0, 0),
    "Grok-3": (0, 0),
    "DeepSeek-R1": (45, 0.05),
    "Kimi-K2-Instruct": (0, 0),
    "Llama3.3-70B-Instruct-Turbo": (0, 0),
    "DeepSeek-V3.1": (40, 0.08),
}

# Add model names as labels (without company prefix)
x_median = df["LMArena"].median()
for i, row in df.iterrows():
    x_val = row["LMArena"]
    y_val = row["Stock SR"]
    model_name = row["Model_Name"]
    
    # Get manual offset for this model
    x_offset, y_offset = position_offsets.get(model_name, (0, 0))
    
    # Smart positioning
    if x_val > x_median:
        text = f"{model_name}  "
        ha = 'right'
    else:
        text = f"  {model_name}"
        ha = 'left'
    
    ax.text(x_val + x_offset, y_val + y_offset, text,
           fontsize=30, va='center', ha=ha, zorder=4)

# Add linear regression fit line
from scipy import stats
slope, intercept, r_value, p_value, std_err = stats.linregress(df['LMArena'], df['Stock SR'])
x_fit = np.array([df['LMArena'].min(), df['LMArena'].max()])
y_fit = slope * x_fit + intercept
ax.plot(x_fit, y_fit, 'k--', alpha=0.4, linewidth=2.5, zorder=1)

# Style adjustments
ax.set_xlabel("LMArena Score", fontsize=44)
ax.set_ylabel("Stock Sharpe Ratio", fontsize=44)
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
