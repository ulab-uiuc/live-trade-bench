import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Set seaborn theme
sns.set_theme(style="white")

# Data for Polymarket
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
    "Polymarket Return": [
        0.223, 0.099, 0.038, -0.019, -0.025, -0.098, -0.106, -0.125, -0.146,
        -0.227, -0.242, -0.245, -0.271, -0.287, -0.327, -0.400, -0.412, -0.493,
        -0.509, -0.576, -0.589
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

# Assign colors to families (orange gradient for polymarket)
family_colors = {
    'GPT': ['#FFB366', '#FF9933', '#FF8000', '#E67300'],  # Light to dark orange
    'Claude': ['#FFCC99', '#FFB366', '#FF9933', '#FF8000'],
    'Llama': ['#FFD9B3', '#FFCC99', '#FFB366', '#FF9933'],
    'Gemini': ['#FFE6CC', '#FFD9B3', '#FFCC99', '#FFB366'],
    'Grok': ['#FF9933', '#FF8000', '#E67300', '#CC6600'],
    'DeepSeek': ['#FFB366', '#FF9933', '#FF8000', '#E67300'],
    'Qwen': ['#FF9933', '#FF8000', '#E67300', '#CC6600'],
    'Kimi': ['#FFD9B3', '#FFCC99', '#FFB366', '#FF9933']
}

# Assign colors to each point based on family and performance rank within family
df['Color'] = '#F57C00'  # default
for family in df['Family'].unique():
    family_data = df[df['Family'] == family].sort_values('Polymarket Return', ascending=False)
    colors = family_colors.get(family, ['#F57C00'])
    for idx, (i, row) in enumerate(family_data.iterrows()):
        color_idx = min(idx, len(colors) - 1)
        df.at[i, 'Color'] = colors[color_idx]

# Plot with Seaborn (square aspect, matching visualize_metrics.py)
fig, ax = plt.subplots(figsize=(14, 14))

# Plot each point with its family color
for idx, row in df.iterrows():
    ax.scatter(row['LMArena'], row['Polymarket Return'], 
              s=800, alpha=0.7, color=row['Color'], 
              marker='^', linewidths=2, edgecolors='white', zorder=3)

# Add model names as labels (without company prefix)
x_median = df["LMArena"].median()
for i, row in df.iterrows():
    x_val = row["LMArena"]
    y_val = row["Polymarket Return"]
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
ax.set_ylabel("Polymarket Return Rate", fontsize=44)
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
