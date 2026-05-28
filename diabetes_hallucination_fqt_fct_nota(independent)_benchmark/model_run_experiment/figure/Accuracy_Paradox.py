import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np

# --- 1. Data Preparation ---
data = {
    'Model': ['Qwen2.5-7B', 'Mistral-Latest', 'DeepSeek-R1-7B', 'Llama-3.1-8B', 'Gemma-7B'],
    'FCT (Knowledge)':      [91.0, 64.0, 76.0, 73.0, 80.0],
    'AOTA (Anti-Sycophancy)':[95.0, 89.0, 80.0, 74.7, 38.0], # Gemma Crash Here (Step 2)
    'FQT (Identification)': [94.0, 48.0, 22.0, 97.0, 9.0],   # Llama Spike Here (Step 3)
    'NOTA (Reasoning)':     [57.0, 26.0, 30.0, 21.2, 27.0]   # Final Collapse (Step 4)
}

df = pd.DataFrame(data)

# --- 2. Setup Plot ---
plt.figure(figsize=(14, 8))
sns.set_theme(style="white", font_scale=1.1)

# New Order: FCT -> AOTA -> FQT -> NOTA
columns = ['FCT (Knowledge)', 'AOTA (Anti-Sycophancy)', 'FQT (Identification)', 'NOTA (Reasoning)']
x_coords = [0, 1, 2, 3]

# Colors
colors = {
    'Qwen2.5-7B': '#2ca02c',      # Green
    'Mistral-Latest': '#7f7f7f',  # Gray
    'DeepSeek-R1-7B': '#ff7f0e',  # Orange
    'Llama-3.1-8B': '#d62728',    # Red (The Paradox)
    'Gemma-7B': '#9467bd'         # Purple (The Crash)
}

# --- 3. Plotting ---
for i, row in df.iterrows():
    model = row['Model']
    y_values = [row[col] for col in columns]
    color = colors.get(model, 'black')
    
    # Highlight Key Models
    if model in ['Gemma-7B', 'Llama-3.1-8B', 'Qwen2.5-7B']:
        alpha = 1.0
        linewidth = 3.5
        zorder = 10
        marker_size = 9
    else:
        alpha = 0.4
        linewidth = 2
        zorder = 1
        marker_size = 7
        
    # Plot Line
    plt.plot(x_coords, y_values, marker='o', markersize=marker_size, 
             linewidth=linewidth, color=color, alpha=alpha, label=model, zorder=zorder)
    
    # --- Storytelling Annotations (Updated Coordinates) ---
    
    # Story 1: Gemma's Early Crash (Step 2: AOTA)
    if model == 'Gemma-7B':
        plt.text(1.05, y_values[1], "38%\n(Sycophancy)", color=color, fontsize=11, fontweight='bold', va='center')

    # Story 2: Llama's Rollercoaster (Step 3 High -> Step 4 Low)
    if model == 'Llama-3.1-8B':
        # Step 3: FQT (High)
        plt.text(2.05, y_values[2], "97%\n(Clear Mind)", color=color, fontsize=11, fontweight='bold', va='center')
        # Step 4: NOTA (Low)
        plt.text(3.05, y_values[3], "21%\n(Format Bias)", color=color, fontsize=11, fontweight='bold', va='center')

    # Story 3: Qwen's Consistency
    if model == 'Qwen2.5-7B':
        plt.text(3.05, y_values[3], "57%", color=color, fontsize=10, fontweight='bold', va='bottom')

# --- 4. Formatting ---
plt.xticks(x_coords, columns, fontsize=12, fontweight='bold')
plt.yticks(np.arange(0, 110, 10))
plt.ylim(0, 110)
plt.xlim(-0.1, 3.5)
plt.ylabel("Accuracy (%)", fontsize=13, fontweight='bold')

# Zone Shading
plt.axhspan(80, 100, color='green', alpha=0.05)
plt.axhspan(0, 40, color='red', alpha=0.05)
plt.text(0.1, 5, "LOGIC COLLAPSE ZONE", color='red', alpha=0.3, fontweight='bold')

plt.title("Figure 2: The Stress Test Trajectory\nHighlighting Gemma's Early Crash vs. Llama's Late Collapse", 
          fontsize=16, fontweight='bold', pad=20)

plt.legend(loc='upper right', bbox_to_anchor=(1.0, 1.05), ncol=3)
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.grid(axis='x', linestyle=':', alpha=0.5)

plt.tight_layout()
plt.savefig('fig2_reordered.png', dpi=300)
plt.show()