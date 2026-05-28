"""
Behavioral Quadrant based on 1000q Core results.
Loads from results_1000q_core/reports/1000q_core_analysis_report.json
"""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Path to report (relative to this script)
SCRIPT_DIR = Path(__file__).resolve().parent
REPORT_PATH = (
    SCRIPT_DIR.parent.parent
    / "multi_model_run_2_4"
    / "1400q"
    / "results_1000q_core"
    / "reports"
    / "1000q_core_analysis_report.json"
)

# Model display names
MODEL_NAMES = {
    "qwen2.5_7b": "Qwen2.5-7B",
    "llama3.1_8b": "Llama3.1-8B",
    "gemma_7b": "Gemma-7B",
    "deepseek-r1_7b": "DeepSeek-R1-7B",
    "mistral_latest": "Mistral",
}

# Define colors for models
MODEL_COLORS = {
    "Qwen2.5-7B": "#2ca02c",    # Green (Ideal)
    "Llama3.1-8B": "#d62728",   # Red (Stubborn)
    "Gemma-7B": "#9467bd",      # Purple (Yes-Man)
    "DeepSeek-R1-7B": "#ff7f0e",  # Orange
    "Mistral": "#1f77b4",      # Blue
}


def load_data():
    """Load NOTA and AOTA accuracy from 1000q report."""
    with open(REPORT_PATH, encoding="utf-8") as f:
        report = json.load(f)
    nota = report["accuracy_by_task"]["NOTA"]
    aota = report["accuracy_by_task"]["AOTA"]
    models = list(nota.keys())
    data = []
    for m in models:
        n_c, n_t = nota[m]["correct"], nota[m]["total"]
        a_c, a_t = aota[m]["correct"], aota[m]["total"]
        nota_acc = 100 * n_c / n_t if n_t else 0
        aota_acc = 100 * a_c / a_t if a_t else 0
        data.append({
            "Model": MODEL_NAMES.get(m, m),
            "NOTA_Acc": round(nota_acc, 1),
            "AOTA_Acc": round(aota_acc, 1),
        })
    return pd.DataFrame(data)


def main():
    df = load_data()
    df["Exclusion_Capability"] = df["NOTA_Acc"]
    df["Sycophancy_Index"] = 100 - df["AOTA_Acc"]

    # Set style for academic publication
    sns.set_theme(style="whitegrid", font_scale=1.2)
    plt.rcParams["font.family"] = "sans-serif"

    fig, ax = plt.subplots(figsize=(10, 8))

    sns.scatterplot(
        data=df,
        x="Sycophancy_Index",
        y="Exclusion_Capability",
        hue="Model",
        palette=MODEL_COLORS,
        s=300,
        edgecolor="black",
        linewidth=1.5,
        alpha=0.9,
        ax=ax,
    )

    # Quadrant thresholds (adjusted for 1000q data range)
    y_threshold = 40  # NOTA: good exclusion
    x_threshold = 30  # Sycophancy: high failure rate

    ax.axhline(y=y_threshold, color="gray", linestyle="--", linewidth=1)
    ax.axvline(x=x_threshold, color="gray", linestyle="--", linewidth=1)

    # Background quadrant colors
    ax.fill_between([0, x_threshold], y_threshold, 100, color="green", alpha=0.05)
    ax.fill_between([x_threshold, 100], 0, y_threshold, color="red", alpha=0.05)
    ax.fill_between([0, x_threshold], 0, y_threshold, color="orange", alpha=0.05)

    # Annotate each point
    for i in range(len(df)):
        ax.text(
            df.Sycophancy_Index.iloc[i] + 1.5,
            df.Exclusion_Capability.iloc[i] + 1,
            df.Model.iloc[i],
            fontsize=11,
            weight="bold",
            color=MODEL_COLORS.get(df.Model.iloc[i], "black"),
        )

    # Quadrant labels
    ax.text(
        5, 90,
        "THE IDEAL ZONE\n(High Behavioral Alignment)",
        fontsize=12, color="green", weight="bold",
        bbox=dict(facecolor="white", alpha=0.8, edgecolor="green"),
    )
    ax.text(
        65, 10,
        'THE "YES-MAN" ZONE\n(Structural Sycophancy)',
        fontsize=12, color="purple", weight="bold", ha="center",
        bbox=dict(facecolor="white", alpha=0.8, edgecolor="purple"),
    )
    ax.text(
        5, 10,
        "THE STUBBORN ZONE\n(Mono-Focus Bias)",
        fontsize=12, color="#d62728", weight="bold",
        bbox=dict(facecolor="white", alpha=0.8, edgecolor="#d62728"),
    )

    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_xlabel(
        "Sycophancy Index (AOTA Failure Rate %) $\\rightarrow$ Higher is Worse",
        fontsize=14, weight="bold",
    )
    ax.set_ylabel(
        "Exclusion Capability (NOTA Accuracy %) $\\rightarrow$ Higher is Better",
        fontsize=14, weight="bold",
    )
    plt.title(
        "Behavioral Safety Phenotypes of Small Medical LLMs\n"
        "(1000q Core: Sycophancy vs. Exclusion Logic)",
        fontsize=16, weight="bold", pad=20,
    )
    plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left", borderaxespad=0.0)
    ax.grid(True, linestyle=":", alpha=0.7)
    plt.tight_layout()

    out_path = SCRIPT_DIR / "Behavioral_Quadrant_1000q.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"Saved: {out_path}")
    plt.show()


if __name__ == "__main__":
    main()
