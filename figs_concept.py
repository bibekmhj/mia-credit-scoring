import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
plt.rcParams.update({'font.family': 'Liberation Sans', 'font.size': 8, 'axes.spines.top': False, 'axes.spines.right': False,
                     'savefig.dpi': 300, 'figure.dpi': 120, 'axes.edgecolor': '#444444', 'axes.linewidth': 0.8})
INK, INK2 = '#1b1b1b', '#555555'
import sys
OUT = sys.argv[1] if len(sys.argv) > 1 else 'figs/'

def box(ax, x, y, w, h, t, fc='#eef3fb', ec=INK2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.3,rounding_size=1.2', fc=fc, ec=ec, lw=0.8))
    ax.text(x + w / 2, y + h / 2, t, ha='center', va='center', fontsize=8, color=INK, linespacing=1.25)

def arrow(ax, x1, y1, x2, y2, label=None, lx=0, ly=1.6, style='->', color=INK2, ls='-'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle=style, color=color, lw=0.9, ls=ls))
    if label:
        ax.text((x1 + x2) / 2 + lx, (y1 + y2) / 2 + ly, label, ha='center', va='bottom', fontsize=8, color=INK2)

# ---------------- Fig 1 threat model (conceptual)
fig, ax = plt.subplots(figsize=(6.0, 3.9)); ax.axis('off'); ax.set_xlim(0, 100); ax.set_ylim(0, 64)
ax.text(31, 61, 'Model owner', ha='center', fontsize=8, fontweight='bold', color='#1f5f99')
ax.text(87, 61, 'Adversary', ha='center', fontsize=8, fontweight='bold', color='#a02020')
ax.plot([71, 71], [4, 59], color='#999999', lw=0.8, ls='--')
bw, bh = 17, 13
xs = [0.5, 25.5, 50.5]
box(ax, xs[0], 40, bw, bh, 'Training data\n(40% member\ntrain split)', fc='#dbe9f6')
box(ax, xs[1], 40, bw, bh, 'Credit scoring\nmodel (target)', fc='#dbe9f6')
box(ax, xs[2], 40, bw, bh, 'Black-box\nprediction API', fc='#dbe9f6')
box(ax, 77, 40, 22, bh, 'Adversary\nqueries records', fc='#f6dcdc')
arrow(ax, 18.2, 46.5, 24.9, 46.5, 'trains', ly=1.0)
arrow(ax, 43.2, 46.5, 49.9, 46.5, 'serves', ly=1.0)
arrow(ax, 76.4, 46.5, 68.2, 46.5, 'queries', ly=1.0)
box(ax, xs[0], 6, bw, bh, 'Shadow pool\n(25% of data)')
box(ax, xs[1], 6, bw, bh, 'Shadow models\n(4 per run)')
box(ax, xs[2], 6, bw + 3, bh, 'Meta-classifier\n(logistic reg.,\n5 features)')
box(ax, 77, 6, 22, bh, 'Member or\nnon-member?', fc='#f6dcdc')
arrow(ax, 18.2, 12.5, 24.9, 12.5, 'trains', ly=1.0)
arrow(ax, 43.2, 12.5, 49.9, 12.5, 'feeds', ly=1.0)
arrow(ax, 88, 39.4, 88, 19.8, 'uses', lx=4, ly=-1)
arrow(ax, 76.4, 12.5, 71.6, 12.5)
ax.text(31, 1, 'Shadow-model attack pipeline', ha='center', fontsize=8, color=INK2)
fig.savefig(OUT + 'fig1_threat_model.png', bbox_inches='tight'); plt.close(fig)

# ---------------- Fig 2 pipeline (conceptual)
fig, ax = plt.subplots(figsize=(6.0, 3.3)); ax.axis('off'); ax.set_xlim(0, 104); ax.set_ylim(0, 54)
for x, t in ((38, 'Phase 1\nModel training'), (58, 'Phase 2\nAttacks'), (76.5, 'Phase 3\nMetrics'), (96, 'Phase 4\nAnalysis')):
    ax.text(x + 4.5 if x < 90 else x - 3.5, 51, t, ha='center', va='center', fontsize=8, color=INK2, linespacing=1.1)
box(ax, 0.5, 20, 14, 14, 'Public\ncredit\ndatasets\n(3)')
box(ax, 18, 20, 14, 14, 'Data\npartition\n40/10/\n25/25%')
box(ax, 36, 33, 15, 11, 'Train\nbaseline\nmodels')
box(ax, 36, 9, 15, 11, 'Apply\ndefences and\ncontrols')
box(ax, 55, 33, 15, 11, 'Threshold\nattack')
box(ax, 55, 9, 15, 11, 'Shadow-\nmodel attack\n(4 shadows)')
box(ax, 72.5, 20, 13, 14, 'AUC-ROC,\nlow-FPR\nTPR')
box(ax, 88.5, 33, 15, 11, 'Driver\nanalysis')
box(ax, 88.5, 9, 15, 11, 'Defence\ncomparison')
arrow(ax, 15.2, 27, 17.4, 27); arrow(ax, 32.6, 29, 35.4, 36); arrow(ax, 32.6, 25, 35.4, 16)
arrow(ax, 51.6, 38.5, 54.4, 38.5); arrow(ax, 51.6, 14.5, 54.4, 14.5); arrow(ax, 51.6, 35, 54.4, 17)
arrow(ax, 70.6, 38.5, 72, 31); arrow(ax, 70.6, 14.5, 72, 23)
arrow(ax, 86.1, 31, 88, 36); arrow(ax, 86.1, 23, 88, 17)
ax.text(52, 2, 'Conceptual workflow, repeated for five seeds. Partitions: member-train, member-validation, non-member, shadow pool.', ha='center', fontsize=8, color=INK2)
fig.savefig(OUT + 'fig2_pipeline.png', bbox_inches='tight'); plt.close(fig)

