import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# Table: Clinical Sub-domain vs FCT, FQT, NOTA counts
subdomains = [
    'Complications\n(Neuropathy, Retinopathy)',
    'Medications\n(Insulin, SGLT2i)',
    'Acute Care\n(Hypoglycemia)',
    'Lifestyle & Prevention'
]
data = {
    'FCT': [209, 299, 81, 373],
    'FQT': [501, 0, 251, 248],
    'NOTA': [359, 384, 133, 124],
}
# Consistent colors per sub-domain across all pies
subdomain_colors = ['#2c7bb6', '#66c2a5', '#fdae61', '#9e4a9b']
# FCT/NOTA total 962/1000/1000
test_totals = {'FCT': 962, 'FQT': 1000, 'NOTA': 1000}

sns.set_theme(style='white')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']

fig, axes = plt.subplots(1, 3, figsize=(14, 6))
test_types = ['FCT', 'FQT', 'NOTA']
for idx, test in enumerate(test_types):
    counts = data[test]
    # Filter out zero so pie doesn't show empty wedge (FQT Medications=0)
    labels = [subdomains[i] for i in range(4) if counts[i] > 0]
    sizes = [c for c in counts if c > 0]
    colors = [subdomain_colors[i] for i in range(4) if counts[i] > 0]
    explode = [0.02] * len(sizes)
    total = sum(sizes)
    def make_autopct(sizes, total):
        def inner(pct):
            val = int(round(pct / 100 * total))
            return f'{pct:.1f}%\n({val})'
        return inner
    wedges, texts, autotexts = axes[idx].pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct=make_autopct(sizes, total),
        startangle=90,
        explode=explode,
        textprops={'fontsize': 10},
        wedgeprops={'edgecolor': 'white', 'linewidth': 1.2}
    )
    for t in autotexts:
        t.set_fontsize(9)
        t.set_fontweight('bold')
    axes[idx].set_title(f'{test}\n(n={test_totals[test]})', fontsize=12, fontweight='bold')

plt.suptitle('Benchmark Question Counts by Clinical Sub-domain and Test Type', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()

plt.savefig('clinical_subdomain_test_type_counts.png', dpi=300, bbox_inches='tight')
plt.close()
print('Saved: clinical_subdomain_test_type_counts.png')
