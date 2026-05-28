import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Data from User's previous message
models = ['DeepSeek-R1-7B', 'Gemma-7B', 'Llama-3.1-8B', 'Mistral-Latest', 'Qwen-2.5-7B']
option_a = [27.6, 18.0, 25.5, 41.0, 20.0]
option_b = [23.5, 9.0, 48.0, 14.0, 29.0]
option_c = [25.5, 7.0, 17.3, 27.0, 17.0]
option_d = [23.5, 66.0, 9.2, 18.0, 34.0] # "All of the Above" (Trap)

# Create DataFrame
df = pd.DataFrame({
    'Model': models,
    'Option A': option_a,
    'Option B': option_b,
    'Option C': option_c,
    'Option D (All of the Above)': option_d
})

# Plotting
plt.figure(figsize=(10, 6))
sns.set_theme(style="white")

# Colors: Neutral for A/B/C, Alert Color for D (Trap)
colors = ['#d9d9d9', '#bdbdbd', '#969696', '#d62728'] # Grays for A-C, Red for D

# Stacked Bar Chart
bottom = [0] * 5
for i, col in enumerate(df.columns[1:]):
    plt.bar(df['Model'], df[col], bottom=bottom, label=col, color=colors[i], edgecolor='white', width=0.6)
    
    # Add labels in the center of the bar segments
    for j, val in enumerate(df[col]):
        if val > 5: # Only label if segment is big enough
            plt.text(j, bottom[j] + val/2, f"{val:.1f}%", ha='center', va='center', color='white' if i==3 else 'black', fontsize=10, fontweight='bold')
    
    # Update bottom
    bottom = [sum(x) for x in zip(bottom, df[col])]

plt.title('Figure: "Blind Faith" Test - Model Response Distribution\n(Scenario: All Options Incorrect + "All of the Above" Trap)', fontsize=14, fontweight='bold', pad=20)
plt.ylabel('Percentage of Responses (%)', fontsize=12)
plt.ylim(0, 100)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title="Response Choice")
plt.tight_layout()

plt.savefig('aota_trap_distribution.png')
plt.show()