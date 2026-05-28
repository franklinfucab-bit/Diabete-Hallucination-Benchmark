import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_fig1_revised():
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # Shared Styles
    box_style = dict(boxstyle="round,pad=0.4", ec="black", lw=2)
    arrow_props = dict(facecolor='black', arrowstyle='->', lw=1.5)
    font_title = dict(ha="center", va="bottom", weight='bold', fontsize=11)
    font_body = dict(ha="center", va="center", fontsize=10)

    # --- 1. The Subjects (Input) ---
    rect_input = patches.Rectangle((0.5, 3), 2, 2, facecolor='#f0f0f0', edgecolor='black', lw=2)
    ax.add_patch(rect_input)
    ax.text(1.5, 4.5, "Input Subjects", **font_title)
    ax.text(1.5, 3.8, "Small Medical LLMs\n(<7B)", **font_body)
    ax.text(1.5, 3.3, "(Llama, Gemma, etc.)", ha="center", va="center", fontsize=9, style='italic')

    ax.annotate("", xy=(3.0, 4), xytext=(2.5, 4), arrowprops=arrow_props)

    # --- 2. Phase 1: Semantic Baseline (The Filter) ---
    # Draw a container for Phase 1
    rect_p1 = patches.Rectangle((3.0, 1), 3, 6, facecolor='#e6f2ff', edgecolor='#2c7bb6', lw=2, linestyle='--')
    ax.add_patch(rect_p1)
    ax.text(4.5, 7.2, "PHASE 1:\nSemantic Baseline", color='#2c7bb6', **font_title)
    
    # Task Box
    ax.text(4.5, 4, "Task: FCT\n(False Confidence Test)", bbox=dict(boxstyle="round", fc="white", ec="#2c7bb6"), **font_body)
    ax.text(4.5, 3, "Goal: Test Nuance\nDiscernment", ha="center", fontsize=9, color='#2c7bb6')

    ax.annotate("", xy=(6.5, 4), xytext=(6.0, 4), arrowprops=arrow_props)

    # --- 3. Phase 2: Structural Stress (The Prism) ---
    # Draw a container for Phase 2
    rect_p2 = patches.Rectangle((6.5, 1), 4, 6, facecolor='#fff2e6', edgecolor='#d62728', lw=2, linestyle='--')
    ax.add_patch(rect_p2)
    ax.text(8.5, 7.2, "PHASE 2:\nTri-Dimensional Stress Test", color='#d62728', **font_title)

    # Dimension 1: FQT
    ax.text(8.5, 5.5, "1. Premise Check (FQT)\n(Validity)", bbox=dict(boxstyle="round", fc="white", ec="#d62728"), size=9, ha="center")
    # Dimension 2: AOTA
    ax.text(8.5, 4.0, "2. Sycophancy (AOTA)\n(Resistance)", bbox=dict(boxstyle="round", fc="white", ec="#d62728"), size=9, ha="center")
    # Dimension 3: NOTA
    ax.text(8.5, 2.5, "3. Exclusion Logic (NOTA)\n(Reasoning)", bbox=dict(boxstyle="round", fc="white", ec="#d62728"), size=9, ha="center")

    ax.annotate("", xy=(11.0, 4), xytext=(10.5, 4), arrowprops=arrow_props)

    # --- 4. Output: Behavioral Phenotypes (The Diagnosis) ---
    rect_out = patches.Rectangle((11.0, 1), 2.5, 6, facecolor='#f2f2f2', edgecolor='black', lw=2)
    ax.add_patch(rect_out)
    ax.text(12.25, 7.2, "OUTPUT:\nSafety Phenotypes", **font_title)

    # Outcome 1
    ax.text(12.25, 5.5, "Format-Induced\nSycophancy\n(Llama-3.1)", bbox=dict(boxstyle="round", fc="#ffcccc", ec="red"), size=8, ha="center")
    # Outcome 2
    ax.text(12.25, 4.0, "Clinical\nYes-Man\n(Gemma-7B)", bbox=dict(boxstyle="round", fc="#e6ccff", ec="purple"), size=8, ha="center")
    # Outcome 3
    ax.text(12.25, 2.5, "Reasoning\nInstability\n(DeepSeek-R1)", bbox=dict(boxstyle="round", fc="#ffecd9", ec="orange"), size=8, ha="center")

    # Final Title
    plt.title("Figure 1: The Dual-Phase Evaluation Framework", weight='bold', fontsize=14, pad=20)
    plt.tight_layout()
    plt.savefig('fig1_framework_revised.png', dpi=300)
    plt.show()

draw_fig1_revised()