"""
Driver analysis: OLS regression of shadow_AUC on model / dataset characteristics.
Uses actual results from mia_results_v2.json.
"""

import json
import numpy as np
import pandas as pd
from scipy import stats

RESULTS_PATH = "/home/claude/mia_experiment/results/mia_results_v2.json"

with open(RESULTS_PATH) as f:
    data = json.load(f)

# ── Build observation table ───────────────────────────────────────────────────
# Each row = one (dataset, model) pair (baseline models only, non-DP)
rows = []
for ds_name, ds in data.items():
    meta = ds["meta"]
    n       = meta["n"]
    dr      = meta["default_rate"]
    n_feat  = meta["n_features"]
    for mname, m in ds["baseline"].items():
        if "error" in m or m.get("shadow_auc") is None:
            continue
        rows.append({
            "dataset":     ds_name,
            "model":       mname,
            "n":           n,
            "default_rate": dr,
            "n_features":  n_feat,
            "train_auc":   m["train_auc"],
            "val_auc":     m["val_auc"],
            "auc_gap":     m["auc_gap"],
            "threshold_auc": m["threshold_auc"],
            "shadow_auc":  m["shadow_auc"],
        })

df = pd.DataFrame(rows)
df["log_n"]       = np.log(df["n"])
df["log_features"] = np.log(df["n_features"])

print("Observation table:")
print(df[["dataset","model","auc_gap","default_rate","log_n","log_features","shadow_auc"]].to_string(index=False))
print(f"\nN observations: {len(df)}")

# ── OLS: shadow_AUC ~ auc_gap + default_rate + log_n + log_features ──────────
from numpy.linalg import lstsq

y = df["shadow_auc"].values
X_vars = df[["auc_gap", "default_rate", "log_n", "log_features"]].values
X_aug  = np.column_stack([np.ones(len(y)), X_vars])

coef, residuals, rank, sv = lstsq(X_aug, y, rcond=None)
y_hat = X_aug @ coef
ss_res = np.sum((y - y_hat) ** 2)
ss_tot = np.sum((y - y.mean()) ** 2)
r2 = 1 - ss_res / ss_tot

# t-statistics (n small, so treat cautiously)
n_obs, k = len(y), X_aug.shape[1]
dof = n_obs - k
mse = ss_res / dof if dof > 0 else np.nan
var_coef = mse * np.linalg.inv(X_aug.T @ X_aug).diagonal() if dof > 0 else np.full(k, np.nan)
se = np.sqrt(np.abs(var_coef))
t_stats = coef / (se + 1e-12)
p_vals  = [2 * stats.t.sf(abs(t), dof) for t in t_stats]

names = ["Intercept", "auc_gap", "default_rate", "log_n", "log_features"]
print(f"\nOLS: shadow_AUC ~ auc_gap + default_rate + log(n) + log(n_features)")
print(f"R^2 = {r2:.4f}   n={n_obs}   dof={dof}")
print(f"\n{'Variable':<15} {'Coef':>9} {'SE':>9} {'t':>7} {'p':>8}")
print("-" * 52)
for nm, c, s, t, p in zip(names, coef, se, t_stats, p_vals):
    print(f"{nm:<15} {c:>9.5f} {s:>9.5f} {t:>7.2f} {p:>8.4f}")

# ── Spearman correlation: auc_gap vs shadow_auc ───────────────────────────────
rho, p_rho = stats.spearmanr(df["auc_gap"], df["shadow_auc"])
print(f"\nSpearman(auc_gap, shadow_auc): rho={rho:.4f}  p={p_rho:.4f}")

# ── Defense comparison summary table ─────────────────────────────────────────
print("\n\n" + "="*70)
print("DEFENSE COMPARISON - shadow_AUC vs val_AUC cost")
print("="*70)

defense_rows = []
for ds_name, ds in data.items():
    base_xgb = ds["baseline"].get("XGBoost", {})
    base_shadow = base_xgb.get("shadow_auc", None)
    base_val    = base_xgb.get("val_auc", None)
    if base_shadow is None:
        continue
    # baseline row
    defense_rows.append({
        "dataset": ds_name, "defense": "XGBoost (baseline)",
        "val_auc": base_val, "auc_cost": 0.0, "shadow_auc": base_shadow
    })
    for dname, d in ds["defenses"].items():
        if "error" in d or d.get("shadow_auc") is None:
            continue
        defense_rows.append({
            "dataset":    ds_name,
            "defense":    dname,
            "val_auc":    d.get("model_val_auc"),
            "auc_cost":   d.get("auc_cost"),
            "shadow_auc": d["shadow_auc"],
        })

ddf = pd.DataFrame(defense_rows)
print(ddf.to_string(index=False))

# ── Print clean tables for paper ─────────────────────────────────────────────
print("\n\n" + "="*70)
print("TABLE 3: BASELINE MODEL RESULTS")
print("="*70)
print(f"{'Dataset':<22} {'Model':<12} {'Train AUC':>10} {'Val AUC':>9} {'Gap':>7}")
print("-"*64)
for _, r in df.iterrows():
    print(f"{r['dataset']:<22} {r['model']:<12} {r['train_auc']:>10.4f} {r['val_auc']:>9.4f} {r['auc_gap']:>7.4f}")

print("\n\n" + "="*70)
print("TABLE 4: ATTACK RESULTS (BASELINE MODELS)")
print("="*70)
print(f"{'Dataset':<22} {'Model':<12} {'Threshold AUC':>14} {'Shadow AUC':>11}")
print("-"*62)
for _, r in df.iterrows():
    print(f"{r['dataset']:<22} {r['model']:<12} {r['threshold_auc']:>14.4f} {r['shadow_auc']:>11.4f}")

print("\n\n" + "="*70)
print("TABLE 5: DEFENSE RESULTS (APPLIED TO XGBoost BASELINE)")
print("="*70)
print(f"{'Dataset':<22} {'Defense':<25} {'Val AUC':>8} {'AUC Cost':>9} {'Shadow AUC':>11}")
print("-"*79)
for _, r in ddf.iterrows():
    vc = r['auc_cost'] if r['auc_cost'] is not None else float('nan')
    vv = r['val_auc'] if r['val_auc'] is not None else float('nan')
    sa = r['shadow_auc'] if r['shadow_auc'] is not None else float('nan')
    print(f"{r['dataset']:<22} {r['defense']:<25} {vv:>8.4f} {vc:>9.4f} {sa:>11.4f}")

print("\n\nAll analysis complete.")
