import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Set seaborn theme
sns.set_theme(style="white")

# Data for Polymarket (from table)
data = {
    "Model": [
        "Anthropic Claude-Sonnet-3.7", "xAI Grok-4", "Qwen Qwen2.5-72B-Instruct",
        "Anthropic Claude-Opus-4", "Meta Llama3.3-70B-Instruct-Turbo", "Meta Llama4-Scout",
        "xAI Grok-3", "DeepSeek DeepSeek-V3.1", "Meta Llama4-Maverick",
        "DeepSeek DeepSeek-R1", "OpenAI GPT-4o", "OpenAI GPT-5",
        "Anthropic Claude-Opus-4.1", "Google Gemini-2.5-Flash", "OpenAI GPT-4.1",
        "Google Gemini-2.5-Pro", "Anthropic Claude-Sonnet-4", "Moonshot Kimi-K2-Instruct",
        "Qwen Qwen3-235B-A22B-Instruct", "Qwen Qwen3-235B-A22B-Thinking", "OpenAI GPT-o3"
    ],
    "LMArena": [
        1385, 1415, 1300, 1412, 1317, 1320, 1409, 1415, 1326,
        1417, 1343, 1426, 1438, 1408, 1411, 1452, 1389, 1416,
        1371, 1397, 1440
    ],
    "Polymarket SR": [
        2.38, 1.01, 0.43, 0.09, 0.40, -1.18, -0.55, -0.07, -1.92,
        0.14, -3.26, -0.49, -3.02, -0.82, -1.74, -1.65, -2.40, -5.26,
        -2.97, -1.81, -3.68
    ]
}

df = pd.DataFrame(data)

# Extract model family (remove company prefix)
def extract_model_family(full_name):
    parts = full_name.split(' ', 1)
    if len(parts) > 1:
        model_name = parts[1]
        # Extract family name
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

# Assign distinct colors to each family (Polymarket - warm colors: red, orange, yellow)
family_colors = {
    'GPT': '#D32F2F',        # Red
    'Claude': '#F57C00',     # Orange
    'Llama': '#E64A19',      # Deep orange
    'Gemini': '#FFA000',     # Amber
    'Grok': '#FF6F00',       # Orange
    'DeepSeek': '#C62828',   # Dark red
    'Qwen': '#EF6C00',       # Orange
    'Kimi': '#F9A825'        # Yellow
}

# Assign colors to each point based on family
df['Color'] = '#F57C00'  # default
for family in df['Family'].unique():
    color = family_colors.get(family, '#F57C00')
    df.loc[df['Family'] == family, 'Color'] = color

# Plot with Seaborn (square aspect, matching visualize_metrics.py)
fig, ax = plt.subplots(figsize=(14, 14))

# Plot each point with its family color
for idx, row in df.iterrows():
    ax.scatter(row['LMArena'], row['Polymarket SR'], 
              s=2000, alpha=0.7, color=row['Color'], 
              marker='^', linewidths=2, edgecolors='white', zorder=3)

# Manual position offsets for each model (x_offset, y_offset)
# You can edit these values to adjust label positions
position_offsets = {
    "Claude-Sonnet-3.7": (0, 0),
    "Grok-4": (0, 0),
    "Qwen2.5-72B-Instruct": (-8, 0.3),
    "Claude-Opus-4": (0, 0),
    "Llama3.3-70B-Instruct-Turbo": (0, 0),
    "Llama4-Scout": (0, 0),
    "Grok-3": (20, 0),
    "DeepSeek-V3.1": (48, -0.1),
    "Llama4-Maverick": (0, 0),
    "DeepSeek-R1": (45, 0),
    "GPT-4o": (0, 0),
    "GPT-5": (-20, 0),
    "Claude-Opus-4.1": (0, -0.2),
    "Gemini-2.5-Flash": (2, -0.1),
    "GPT-4.1": (-10, 0.1),
    "Gemini-2.5-Pro": (5, -0.3),
    "Claude-Sonnet-4": (0, 0),
    "Kimi-K2-Instruct": (0, 0),
    "Qwen3-235B-A22B-Instruct": (-75, 0.1),
    "Qwen3-235B-A22B-Thinking": (-20, 0.5),
    "GPT-o3": (0, 0),
}

# Add model names as labels (without company prefix)
x_median = df["LMArena"].median()
for i, row in df.iterrows():
    x_val = row["LMArena"]
    y_val = row["Polymarket SR"]
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
slope, intercept, r_value, p_value, std_err = stats.linregress(df['LMArena'], df['Polymarket SR'])
x_fit = np.array([df['LMArena'].min(), df['LMArena'].max()])
y_fit = slope * x_fit + intercept
ax.plot(x_fit, y_fit, 'k--', alpha=0.4, linewidth=2.5, zorder=1)

# Style adjustments
ax.set_xlabel("LMArena Score", fontsize=44)
ax.set_ylabel("Polymarket Sharpe Ratio", fontsize=44)
ax.tick_params(labelsize=36, width=2, length=8)
ax.grid(False)

# Set spine style
for spine in ax.spines.values():
    spine.set_edgecolor('#34495e')
    spine.set_linewidth(2)

plt.tight_layout()
plt.savefig('../data/visualizations/correlation_lmarena_polymarket.pdf', 
           format='pdf', bbox_inches='tight', facecolor='white')
print("✓ Polymarket correlation plot saved to: ../data/visualizations/correlation_lmarena_polymarket.pdf")
plt.close()
