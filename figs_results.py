"""Draw the result figures from results/summary/*.csv (mean and 95% CI over seeds)."""
import sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
S = sys.argv[1] if len(sys.argv) > 1 else "results/summary"
OUT = sys.argv[2] if len(sys.argv) > 2 else "figs/"
plt.rcParams.update({"font.family": "Liberation Sans", "font.size": 8, "axes.spines.top": False, "axes.spines.right": False,
                     "savefig.dpi": 300, "figure.dpi": 120, "axes.edgecolor": "#444444", "axes.linewidth": 0.8})
INK = "#1b1b1b"
B = pd.read_csv(f"{S}/baseline_summary.csv"); D = pd.read_csv(f"{S}/defences_summary.csv")
DS = [("Taiwan", "Taiwan\nCredit"), ("GMSC", "Give Me\nSome Credit"), ("HomeCredit", "Home\nCredit")]

def get(df, ds, model):
    m = model
    if model == "EBM" and ds == "HomeCredit": m = "EBM_80k"
    r = df[(df.dataset == ds) & (df.model == m)]
    return r.iloc[0] if len(r) else None

# ---------------- Fig 3: attack AUC, four models, three datasets
cols = {"XGBoost": "#2a6fb0", "LightGBM": "#7b5ea7", "EBM": "#e0a030", "LogisticRegression": "#6e6e6e"}
hat = {"XGBoost": "", "LightGBM": "////", "EBM": "....", "LogisticRegression": "xxxx"}
lab = {"XGBoost": "XGBoost", "LightGBM": "LightGBM", "EBM": "EBM", "LogisticRegression": "Logistic regression (control)"}
fig, axs = plt.subplots(1, 2, figsize=(6.2, 3.0), sharey=True)
for ax, att, ttl in ((axs[0], "shadow_xgb_auc", "(a) Shadow-model attack"), (axs[1], "threshold_auc", "(b) Confidence-threshold attack")):
    w = 0.2
    for k, m in enumerate(cols):
        xs = np.arange(3) + (k - 1.5) * w
        mu = [get(B, d, m)[att + "_mean"] for d, _ in DS]; ci = [get(B, d, m)[att + "_ci95"] for d, _ in DS]
        ax.bar(xs, mu, w * 0.92, yerr=ci, color=cols[m], hatch=hat[m], edgecolor="white", lw=0.4, ecolor=INK, error_kw=dict(lw=0.8, capsize=1.5), label=lab[m])
    ax.axhline(0.5, color="#c0392b", ls="--", lw=0.9)
    ax.set_xticks(range(3)); ax.set_xticklabels([t for _, t in DS], fontsize=8)
    ax.set_ylim(0.47, 0.62); ax.set_title(ttl, fontsize=8, loc="left")
axs[0].set_ylabel("Attack AUC-ROC (mean over seeds)")
h, l = axs[0].get_legend_handles_labels(); h.append(Line2D([0], [0], color="#c0392b", ls="--", lw=0.9)); l.append("Chance (0.5)")
fig.legend(h, l, loc="lower center", ncol=3, frameon=False, fontsize=8, bbox_to_anchor=(0.5, -0.07))
fig.tight_layout(rect=(0, 0.1, 1, 1)); fig.savefig(OUT + "fig3_attack_auc.png", bbox_inches="tight"); plt.close(fig)

# ---------------- Fig 4: privacy-utility (defences and controls)
names = {"rounding_k5": "Rounding K=5", "rounding_k10": "Rounding K=10", "noise_0.02": "Noise 0.02", "noise_0.05": "Noise 0.05",
         "regularised": "Regularised XGBoost", "tuned_xgb": "Tuned XGBoost", "dp_lr_eps1": "DP-LR eps=1", "dp_lr_eps5": "DP-LR eps=5", "dp_lr_eps10": "DP-LR eps=10"}
dcol = {"Rounding K=5": "#8fd0b8", "Rounding K=10": "#2fa37a", "Noise 0.02": "#f0b43c", "Noise 0.05": "#e07b17", "Regularised XGBoost": "#2a6fb0",
        "Tuned XGBoost": "#7fb2e0", "DP-LR eps=1": "#e06070", "DP-LR eps=5": "#b01c30", "DP-LR eps=10": "#6d0f1e"}
mk = {"Taiwan": "o", "GMSC": "s", "HomeCredit": "^"}; mkn = {"Taiwan": "Taiwan Credit", "GMSC": "Give Me Some Credit", "HomeCredit": "Home Credit"}
fig, ax = plt.subplots(figsize=(6.2, 4.0))
for ds, _ in DS:
    base_val = get(B, ds, "XGBoost").val_auc_mean
    for k, nm in names.items():
        r = D[(D.dataset == ds) & (D.model == k)].iloc[0]
        ax.errorbar(r.utility_cost_mean, r.shadow_matched_auc_mean, yerr=r.shadow_matched_auc_ci95, fmt=mk[ds], ms=5.2, color=dcol[nm], mec="#222222", mew=0.5, ecolor="#777777", elinewidth=0.6, capsize=0, zorder=3)
    r = get(B, ds, "LogisticRegression")
    ax.errorbar(base_val - r.val_auc_mean, r.shadow_matched_auc_mean, yerr=r.shadow_matched_auc_ci95, fmt="x", ms=5.5, color="#222222", mew=1.0, ecolor="#777777", elinewidth=0.6, capsize=0, zorder=3)
ax.axhline(0.5, color="#c0392b", ls="--", lw=0.9)
ax.set_xlabel("Utility cost (validation AUC of baseline XGBoost minus validation AUC of the model)"); ax.set_ylabel("Shadow-model attack AUC-ROC (matched shadows)")
hs = [Line2D([0], [0], marker=m, ls="", color="#888888", mec="#222222", ms=5.5) for m in mk.values()]
l1 = ax.legend(hs, list(mkn.values()), title="Dataset", loc="upper right", fontsize=8, title_fontsize=8, frameon=False, bbox_to_anchor=(1.0, 0.62)); ax.add_artist(l1)
hd = [Line2D([0], [0], marker="o", ls="", color=c, mec="#222222", ms=5.5) for c in dcol.values()] + [Line2D([0], [0], marker="x", ls="", color="#222222", ms=5.5)]
ax.legend(hd, list(dcol) + ["Logistic regression (non-private)"], title="Defence or control", loc="upper right", fontsize=7.5, title_fontsize=8, frameon=False, bbox_to_anchor=(1.0, 1.0), ncol=2)
fig.tight_layout(); fig.savefig(OUT + "fig4_privacy_utility.png", bbox_inches="tight"); plt.close(fig)

# ---------------- Fig 5: gap vs shadow AUC for the nine dataset-model pairs
fig, ax = plt.subplots(figsize=(5.4, 3.6))
mcol = {"XGBoost": "#2a6fb0", "LightGBM": "#7b5ea7", "EBM": "#e0a030"}
for ds, _ in DS:
    for m in mcol:
        r = get(B, ds, m)
        ax.errorbar(r.gap_mean, r.shadow_xgb_auc_mean, xerr=r.gap_ci95, yerr=r.shadow_xgb_auc_ci95, fmt=mk[ds], ms=5.5, color=mcol[m], mec="#222222", mew=0.5, ecolor="#888888", elinewidth=0.6, zorder=3)
sw = [(n, get(B, "HomeCredit", m)) for n, m in ((8000, "XGBoost_sub20000"), (16000, "XGBoost_sub40000"), (32000, "XGBoost_sub80000"), (64000, "XGBoost_sub160000"), (123004, "XGBoost"))]
sw = [(n, r) for n, r in sw if r is not None]
if len(sw) >= 3:
    ax.plot([r.gap_mean for _, r in sw], [r.shadow_xgb_auc_mean for _, r in sw], color="#2a6fb0", lw=0.8, ls=":", zorder=2)
    for n, r in sw:
        ax.errorbar(r.gap_mean, r.shadow_xgb_auc_mean, yerr=r.shadow_xgb_auc_ci95, fmt="D", ms=4, color="#9ec3e6", mec="#222222", mew=0.5, ecolor="#888888", elinewidth=0.6, zorder=3)
        ax.annotate(f"{n // 1000}k", (r.gap_mean, r.shadow_xgb_auc_mean), textcoords="offset points", xytext=((5, -11) if n == 123004 else (5, 3)), fontsize=7, color="#333333")
ax.axhline(0.5, color="#c0392b", ls="--", lw=0.9)
ax.set_xlabel("Train-validation AUC gap"); ax.set_ylabel("Shadow-model attack AUC-ROC")
h1 = [Line2D([0], [0], marker="o", ls="", color=c, mec="#222222", ms=5.5) for c in mcol.values()]
l1 = ax.legend(h1, list(mcol), title="Model", loc="upper left", fontsize=8, title_fontsize=8, frameon=False); ax.add_artist(l1)
h2 = [Line2D([0], [0], marker=m, ls="", color="#888888", mec="#222222", ms=5.5) for m in mk.values()]
h2 = h2 + [Line2D([0], [0], marker="D", ls=":", color="#2a6fb0", mfc="#9ec3e6", mec="#222222", ms=4)]
ax.legend(h2, list(mkn.values()) + ["Home Credit XGBoost, member-train size (k records)"], title="Dataset", loc="upper left", fontsize=7.5, title_fontsize=8, frameon=False, bbox_to_anchor=(0.0, 0.68))
fig.tight_layout(); fig.savefig(OUT + "fig5_gap_vs_attack.png", bbox_inches="tight"); plt.close(fig)
print("figures written")
