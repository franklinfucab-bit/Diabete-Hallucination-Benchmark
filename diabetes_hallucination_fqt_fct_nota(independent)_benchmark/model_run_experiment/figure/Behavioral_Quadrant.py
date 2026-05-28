import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set style for academic publication
sns.set_theme(style="whitegrid", font_scale=1.2)
plt.rcParams['font.family'] = 'sans-serif'

# --- 1. Data Preparation (Based on your provided table) ---
data = {
    'Model': ['Qwen2.5-7B', 'Llama3.1-8B', 'Mistral', 'DeepSeek-R1-7B', 'Gemma-7B'],
    # NOTA Accuracy (Higher is Better -> Y axis)
    'NOTA_Acc': [57.0, 21.2, 26.0, 30.0, 27.0],
    # AOTA Accuracy from table. We convert to Failure Rate (Higher is Worse -> X axis)
    'AOTA_Acc': [95.0, 74.7, 89.0, 80.0, 38.0]
}

df = pd.DataFrame(data)

# Calculate the dimensions for plotting
# Y-axis: Exclusion Capability (NOTA Accuracy)
df['Exclusion_Capability'] = df['NOTA_Acc']
# X-axis: Sycophancy Index (Failure Rate on AOTA tasks)
df['Sycophancy_Index'] = 100 - df['AOTA_Acc']

# Define colors/markers for models
model_colors = {
    'Qwen2.5-7B': '#2ca02c',    # Green (Good)
    'Llama3.1-8B': '#d62728',   # Red (Stubborn)
    'Gemma-7B': '#9467bd',      # Purple (Sycophant)
    'DeepSeek-R1-7B': '#ff7f0e',# Orange (Unstable)
    'Mistral': '#7f7f7f'        # Gray
}

# --- 2. Create the Plot ---
fig, ax = plt.subplots(figsize=(10, 8))

# Draw scatter plot
sns.scatterplot(
    data=df,
    x="Sycophancy_Index",
    y="Exclusion_Capability",
    hue="Model",
    palette=model_colors,
    s=300, # Marker size
    edgecolor='black',
    linewidth=1.5,
    alpha=0.9,
    ax=ax
)

# --- 3. Define Quadrants and Zones (The Storytelling) ---
# Define thresholds for quadrants (e.g., 40% NOTA Acc, 30% Sycophancy Fail Rate)
y_threshold = 40
x_threshold = 30

# Draw dividing lines
ax.axhline(y=y_threshold, color='gray', linestyle='--', linewidth=1)
ax.axvline(x=x_threshold, color='gray', linestyle='--', linewidth=1)

# Add background colors for quadrants (Optional, for emphasis)
# Top-Left (Ideal): High Exclusion, Low Sycophancy
ax.fill_between([0, x_threshold], y_threshold, 100, color='green', alpha=0.05)
# Bottom-Right (Worst): Low Exclusion, High Sycophancy
ax.fill_between([x_threshold, 100], 0, y_threshold, color='red', alpha=0.05)
# Bottom-Left (Stubborn): Low Exclusion, Low Sycophancy
ax.fill_between([0, x_threshold], 0, y_threshold, color='orange', alpha=0.05)


# --- 4. Add Annotations and Labels ---
# Annotate each point with model name
for i in range(df.shape[0]):
    ax.text(
        df.Sycophancy_Index[i] + 1.5, # Shift x slightly
        df.Exclusion_Capability[i] + 1, # Shift y slightly
        df.Model[i],
        fontsize=11,
        weight='bold',
        color=model_colors[df.Model[i]]
    )

# Add Quadrant Descriptive Labels (Crucial for MICCAI)
# Top-Left
ax.text(5, 90, "THE IDEAL ZONE\n(High Behavioral Alignment)", 
        fontsize=12, color='green', weight='bold', bbox=dict(facecolor='white', alpha=0.8, edgecolor='green'))

# Bottom-Right
ax.text(65, 10, 'THE "YES-MAN" ZONE\n(Structural Sycophancy)', 
        fontsize=12, color='purple', weight='bold', ha='center', bbox=dict(facecolor='white', alpha=0.8, edgecolor='purple'))

# Bottom-Left
ax.text(5, 10, 'THE STUBBORN ZONE\n(Mono-Focus Bias)', 
        fontsize=12, color='#d62728', weight='bold', bbox=dict(facecolor='white', alpha=0.8, edgecolor='#d62728'))

# --- 5. Final Polish ---
# Set axis limits and labels
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.set_xlabel("Sycophancy Index (AOTA Failure Rate %) $\\rightarrow$ Higher is Worse", fontsize=14, weight='bold')
ax.set_ylabel("Exclusion Capability (NOTA Accuracy %) $\\rightarrow$ Higher is Better", fontsize=14, weight='bold')

# Add a professional title
plt.title("Figure 3: Behavioral Safety Phenotypes of Small Medical LLMs\n(Mapping Sycophancy vs. Exclusion Logic)", 
          fontsize=16, weight='bold', pad=20)

# Move legend out of the way
plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0.)

# Show grid
ax.grid(True, linestyle=':', alpha=0.7)

plt.tight_layout()

# Save the figure (high resolution for paper)
# plt.savefig('fig3_behavioral_quadrant.png', dpi=300, bbox_inches='tight')

plt.show()