import matplotlib
matplotlib.use('Agg')
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set the aesthetic style
sns.set_theme(style="whitegrid")
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']

# Raw Data
data = {
    'Model': ['deepseek-r1_7b', 'gemma_7b', 'llama3.1_8b', 'mistral_latest', 'qwen2.5_7b'],
    'FQT': [22.0, 9.0, 97.0, 48.0, 94.0],
    'FCT': [76.0, 80.0, 73.0, 64.0, 91.0],
    'NOTA': [30.0, 27.0, 21.2, 26.0, 57.0]
}

df_wide = pd.DataFrame(data)

# Melt into long format for easier plotting with Seaborn
df_long = df_wide.melt(id_vars='Model', 
                       var_name='Test Type', 
                       value_name='Accuracy')

# Define custom colors for the tests to maintain consistency
# FQT (Easy/Memory) -> Green/Blueish
# FCT (Medium/Anchor) -> Orange/Yellowish
# NOTA (Hard/Reasoning) -> Red
custom_palette = {'FQT': '#66c2a5', 'FCT': '#fdae61', 'NOTA': '#d53e4f'}


def plot_grouped_bar():
    fig, ax = plt.subplots(figsize=(12, 7))

    # Create the bar chart
    sns.barplot(
        data=df_long, 
        x='Model', 
        y='Accuracy', 
        hue='Test Type', 
        palette=custom_palette,
        edgecolor='white',
        linewidth=1,
        ax=ax
    )

    # Add data labels on top of bars
    for container in ax.containers:
        ax.bar_label(container, fmt='%.1f%%', padding=3, fontsize=10, fontweight='bold')

    # Customization
    ax.set_ylim(0, 110) # Give space for labels
    ax.set_ylabel('Accuracy (%)', fontsize=12, fontweight='bold')
    ax.set_xlabel('')
    plt.xticks(fontsize=11, fontweight='semibold')
    plt.yticks(fontsize=11)
    
    # Move legend
    plt.legend(title='Test Type', title_fontsize='12', fontsize='11', 
               bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0.)
    
    plt.title('Model Performance Comparison Across Three Benchmarks\n(FQT vs. FCT vs. NOTA)', 
              fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('grouped_bar_chart.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: grouped_bar_chart.png")

plot_grouped_bar()


def plot_heatmap():
    # Prepare data for heatmap (needs model as index)
    df_heatmap = df_wide.set_index('Model')
    
    # Reorder columns if desired to show progression (FQT -> FCT -> NOTA)
    df_heatmap = df_heatmap[['FQT', 'FCT', 'NOTA']]

    fig, ax = plt.subplots(figsize=(8, 6))

    # Create heatmap
    # Use a diverging color map (RdYlBu_r) so low is red, high is blue
    sns.heatmap(
        df_heatmap, 
        annot=True,    # Show numbers
        fmt=".1f",     # Number format
        cmap="RdYlBu", # Red-Yellow-Blue colormap
        center=60,     # Center the colormap around 60%
        linewidths=1, 
        linecolor='white',
        cbar_kws={'label': 'Accuracy (%)'},
        annot_kws={"fontsize": 12, "fontweight": "bold"},
        ax=ax
    )

    # Customization
    ax.set_ylabel('')    
    plt.xticks(fontsize=12, fontweight='bold')
    plt.yticks(fontsize=12, fontweight='semibold', rotation=0)
    
    plt.title('Accuracy Heatmap: Models vs. Tests', 
              fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: heatmap.png")

plot_heatmap()


def plot_parallel_coordinates():
    fig, ax = plt.subplots(figsize=(11, 7))

    # Define x-positions for the categorical tests
    test_positions = {'FQT': 0, 'FCT': 1, 'NOTA': 2}
    test_labels = ['FQT\n(Memory)', 'FCT\n(Conviction)', 'NOTA\n(Reasoning)']

    # Plot lines for each model
    # Define distinct colors for models
    model_colors = sns.color_palette("husl", n_colors=len(df_wide))
    
    for i, row in df_wide.iterrows():
        model_name = row['Model']
        scores = [row['FQT'], row['FCT'], row['NOTA']]
        
        # Highlight Qwen, make others slightly transparent
        alpha = 1.0 if 'qwen' in model_name.lower() else 0.6
        linewidth = 3.5 if 'qwen' in model_name.lower() else 2.5
        
        # Plot the line
        ax.plot([0, 1, 2], scores, marker='o', markersize=10, 
                linewidth=linewidth, alpha=alpha, label=model_name, color=model_colors[i])
        
        # Add end label for NOTA score
        ax.text(2.05, scores[2], f"{model_name}\n({scores[2]:.1f}%)", 
                va='center', fontsize=10, color=model_colors[i], fontweight='bold')

    # Customization
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(test_labels, fontsize=12, fontweight='bold')
    ax.set_ylabel('Accuracy (%)', fontsize=12, fontweight='bold')
    ax.set_ylim(0, 105)
    ax.set_xlim(-0.2, 2.8) # Extra space for labels on right
    
    # Add vertical grid lines for the tests
    ax.grid(axis='x', linestyle='--', alpha=0.7)

    plt.title('Performance Trajectory Across Test Difficulty Levels', 
              fontsize=14, fontweight='bold', pad=20)
    
    # We use direct labels instead of a legend for clarity in this chart type
    # plt.legend() 
    
    plt.tight_layout()
    plt.savefig('parallel_coordinates.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: parallel_coordinates.png")

plot_parallel_coordinates()