"""Aggregate the per-seed JSON files from run_experiments_v3.py into summary tables (CSV)."""
import glob, json, os, sys
import numpy as np, pandas as pd
from scipy import stats

RES = sys.argv[1] if len(sys.argv) > 1 else "results/v3"
OUT = sys.argv[2] if len(sys.argv) > 2 else "results/summary"
os.makedirs(OUT, exist_ok=True)
runs = []
for f in sorted(glob.glob(os.path.join(RES, "*.json"))):
    R = json.load(open(f)); R["file"] = os.path.basename(f); runs.append(R)

def rows(kind):
    out = []
    for R in runs:
        ds = R["dataset"]; sub = ("_EBM" in R["file"]) or ("_TREES" in R["file"])
        for name, a in R[kind].items():
            d = {"dataset": ds, "seed": R["seed"], "model": name + (("_80k" if "_EBM" in R["file"] else "_sub" + R["file"].split("_TREES")[1].split("_")[0]) if sub else "")}
            d.update(train_auc=a["train_auc"], val_auc=a["val_auc"], gap=a["gap"])
            for att in ("threshold", "shadow_xgb", "shadow_matched"):
                if att in a:
                    for k, v in a[att].items(): d[f"{att}_{k}"] = v
            out.append(d)
    return pd.DataFrame(out)

B, Dd = rows("baseline"), rows("defences")
# utility cost relative to the XGBoost baseline of the same dataset and seed
base_val = B[B.model == "XGBoost"].set_index(["dataset", "seed"]).val_auc
Dd["utility_cost"] = [base_val[(r.dataset, r.seed)] - r.val_auc for r in Dd.itertuples()]
Dd["val_auc_xgb_baseline"] = [base_val[(r.dataset, r.seed)] for r in Dd.itertuples()]
B.to_csv(f"{OUT}/baseline_by_seed.csv", index=False); Dd.to_csv(f"{OUT}/defences_by_seed.csv", index=False)

def summarise(df, keys=("dataset", "model")):
    cols = [c for c in df.columns if c not in keys and c != "seed"]
    g = df.groupby(list(keys), sort=False)
    mean, sd, n = g[cols].mean(), g[cols].std(ddof=1), g.size()
    ci = sd.mul(stats.t.ppf(.975, (n - 1).clip(lower=1)), axis=0).div(np.sqrt(n), axis=0)
    out = mean.add_suffix("_mean").join(sd.add_suffix("_sd")).join(ci.add_suffix("_ci95")); out["n_seeds"] = n
    return out.reset_index()

SB, SD = summarise(B), summarise(Dd)
SB.to_csv(f"{OUT}/baseline_summary.csv", index=False); SD.to_csv(f"{OUT}/defences_summary.csv", index=False)

# driver analysis: gap vs shadow AUC over the nine dataset-model pairs
nine = SB[SB.model.isin(["XGBoost", "LightGBM", "EBM", "EBM_80k"]) & ~((SB.dataset == "HomeCredit") & (SB.model == "EBM"))]  # XGBoost_80k / LightGBM_80k are excluded here on purpose
nine = nine[~((nine.dataset != "HomeCredit") & (nine.model == "EBM_80k"))]
rho, p = stats.spearmanr(nine.gap_mean, nine.shadow_xgb_auc_mean)
rho_t, p_t = stats.spearmanr(nine.gap_mean, nine.threshold_auc_mean)
per_seed = []
for s in sorted(B.seed.unique()):
    b = B[(B.seed == s)]; b = b[b.model.isin(["XGBoost", "LightGBM", "EBM", "EBM_80k"])]
    b = b[~((b.dataset == "HomeCredit") & (b.model == "EBM")) & ~((b.dataset != "HomeCredit") & (b.model == "EBM_80k"))]
    if len(b) == 9: per_seed.append(stats.spearmanr(b.gap, b.shadow_xgb_auc)[0])
drv = {"n_points": len(nine), "spearman_seedmeans": rho, "p": p, "spearman_threshold_seedmeans": rho_t, "p_threshold": p_t,
       "spearman_by_seed": per_seed}
json.dump(drv, open(f"{OUT}/driver.json", "w"), indent=1)
info = pd.DataFrame([{"dataset": R["dataset"] if ("_EBM" not in R["file"] and "_TREES" not in R["file"]) else R["dataset"] + ("_EBM" if "_EBM" in R["file"] else "_TREES"), "seed": R["seed"], **R["info"]} for R in runs])
info.to_csv(f"{OUT}/info.csv", index=False)
print(SB[["dataset", "model", "n_seeds", "val_auc_mean", "gap_mean", "threshold_auc_mean", "shadow_xgb_auc_mean", "shadow_xgb_auc_sd"]].round(4).to_string())
print(SD[["dataset", "model", "utility_cost_mean", "threshold_auc_mean", "shadow_xgb_auc_mean", "shadow_matched_auc_mean"]].round(4).to_string())
print(drv)
