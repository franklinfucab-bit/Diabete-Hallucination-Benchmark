import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for saving without display
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import matplotlib.patches as mpatches

# 1. 准备数据
# 数据来源：用户提供的表格
data = {
    'Model': ['Qwen2.5-7B', 'Llama3.1-8B', 'DeepSeek-R1-7B', 'Gemma-7B', 'Mistral-Latest'],
    'FCT_Accuracy': [91.0, 73.0, 76.0, 80.0, 64.0],
    'NOTA_Accuracy': [57.0, 21.2, 30.0, 27.0, 26.0]
}
df = pd.DataFrame(data)

# 计算跌幅
df['Degradation'] = df['FCT_Accuracy'] - df['NOTA_Accuracy']

# 按 FCT 准确率排序，使图表更有条理 (表现最好的在最上面)
df = df.sort_values('FCT_Accuracy', ascending=True).reset_index(drop=True)

# 2. 设置绘图风格 (论文级出版风格)
sns.set_theme(style="whitegrid")
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans'] # 优先使用 Arial，常用于论文

fig, ax = plt.subplots(figsize=(12, 7))

# 定义颜色
color_fct = '#2c7bb6'  # 深蓝 (Baseline)
color_nota = '#d7191c' # 深红 (Degraded)
color_line = '#bababa' # 灰色连接线

# 3. 绘制哑铃图核心结构
# 绘制连接线 (Hlines)
ax.hlines(y=df.index, xmin=df['NOTA_Accuracy'], xmax=df['FCT_Accuracy'], 
          color=color_line, alpha=0.6, linewidth=4, zorder=1)

# 绘制点 (Scatter plot)
# FCT 点
ax.scatter(df['FCT_Accuracy'], df.index, s=200, color=color_fct, 
           edgecolor='white', linewidth=1.5, zorder=3, label='FCT Baseline (Anchor Present)')
# NOTA 点
ax.scatter(df['NOTA_Accuracy'], df.index, s=200, color=color_nota, 
           edgecolor='white', linewidth=1.5, zorder=3, label='NOTA FCT-derived (Anchor Removed)')

# 4. 添加数据标签和跌幅注释
for i, row in df.iterrows():
    # FCT 数值标签 (右侧)
    ax.text(row['FCT_Accuracy'] + 1.5, i, f"{row['FCT_Accuracy']:.1f}%", 
            va='center', ha='left', color=color_fct, fontweight='bold', fontsize=11)
    
    # NOTA 数值标签 (左侧)
    ax.text(row['NOTA_Accuracy'] - 1.5, i, f"{row['NOTA_Accuracy']:.1f}%", 
            va='center', ha='right', color=color_nota, fontweight='bold', fontsize=11)
    
    # 在连接线中间标记跌幅 (Degradation Magnitude)
    mid_point = (row['FCT_Accuracy'] + row['NOTA_Accuracy']) / 2
    ax.text(mid_point, i + 0.25, f"Δ -{row['Degradation']:.1f}%", 
            va='center', ha='center', color='#555555', fontsize=10, style='italic', 
            bbox=dict(facecolor='white', edgecolor='none', pad=0.2, alpha=0.7))

    # 特别强调 Qwen 和 Llama 的巨大跌幅 (可选，用箭头标注)
    if row['Model'] in ['Qwen2.5-7B', 'Llama3.1-8B']:
         ax.annotate('', xy=(row['NOTA_Accuracy'], i), xytext=(row['FCT_Accuracy'], i),
                    arrowprops=dict(arrowstyle='->', color=color_nota, lw=2, ls='-'), zorder=2)

# 5. 优化图表布局和标签
ax.set_yticks(df.index)
ax.set_yticklabels(df['Model'], fontweight='semibold', fontsize=12)

ax.set_xlim(0, 105)
ax.set_xlabel("Accuracy (%)", fontsize=12, fontweight='bold', labelpad=10)
ax.xaxis.set_major_formatter('{x:.0f}%') # X轴显示百分比

# 设置标题
plt.title("Stepwise Degradation: Impact of NOTA Format on Model Reasoning\n(FCT Baseline vs. FCT-derived NOTA Control Group)", 
          fontsize=14, fontweight='bold', loc='left', pad=20)

# 设置图例
legend = ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=2, frameon=False, fontsize=11)

# 移除不必要的边框
sns.despine(left=True, bottom=True)

# 调整布局以防止标签重叠
plt.tight_layout()

# 保存图片 (高分辨率)
plt.savefig('stepwise_degradation_dumbbell_chart.png', dpi=300, bbox_inches='tight')
print("Figure saved to: stepwise_degradation_dumbbell_chart.png")

# plt.show()