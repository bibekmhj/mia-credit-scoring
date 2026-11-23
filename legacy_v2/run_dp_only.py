"""
Run only the DP-LR defense experiments and patch mia_results_v2.json.
Uses the same splits/preprocessing as run_experiments_v2.py.
"""

import json, time, os, warnings
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score
import diffprivlib as dpl

warnings.filterwarnings("ignore")

DATA_DIR    = "/home/claude/mia_experiment/data"
RESULTS_DIR = "/home/claude/mia_experiment/results"
RANDOM_SEED = 42

# ── Same loaders ──────────────────────────────────────────────────────

def load_taiwan_credit():
    df = pd.read_csv(os.path.join(DATA_DIR, "taiwan_credit.csv"), header=1)
    target_col = "default.payment.next.month" if "default.payment.next.month" in df.columns else df.columns[-1]
    y = df[target_col].astype(int).values
    drop_cols = [target_col] + (["ID"] if "ID" in df.columns else [])
    X = df.drop(columns=drop_cols).values.astype(float)
    X = SimpleImputer(strategy="median").fit_transform(X)
    return X, y

def load_give_me_some_credit():
    df = pd.read_csv(os.path.join(DATA_DIR, "give_me_some_credit.csv"), index_col=0)
    df = df.dropna(subset=["SeriousDlqin2yrs"])
    y = df["SeriousDlqin2yrs"].astype(int).values
    X = df.drop(columns=["SeriousDlqin2yrs"]).values.astype(float)
    X = SimpleImputer(strategy="median").fit_transform(X)
    return X, y

def load_home_credit():
    df = pd.read_csv(os.path.join(DATA_DIR, "application_train.csv"))
    y = df["TARGET"].astype(int).values
    drop_cols = [c for c in ["TARGET", "SK_ID_CURR"] if c in df.columns]
    X = df.drop(columns=drop_cols)
    for c in X.select_dtypes(include=["object"]).columns:
        X[c] = LabelEncoder().fit_transform(X[c].astype(str))
    X = SimpleImputer(strategy="median").fit_transform(X.values.astype(float))
    return X, y

# ── Same MIA split ────────────────────────────────────────────────────

def mia_split(X, y, seed=RANDOM_SEED):
    rng = np.random.default_rng(seed)
    n = len(y)
    idx = rng.permutation(n)
    n_mt = int(0.40 * n)
    n_mv = int(0.10 * n)
    n_nm = int(0.25 * n)
    mt, mv, nm = idx[:n_mt], idx[n_mt:n_mt+n_mv], idx[n_mt+n_mv:n_mt+n_mv+n_nm]
    sp = idx[n_mt+n_mv+n_nm:]
    return dict(
        X_mt=X[mt], y_mt=y[mt],
        X_mv=X[mv], y_mv=y[mv],
        X_nm=X[nm], y_nm=y[nm],
        X_sp=X[sp], y_sp=y[sp],
        X_mem=np.vstack([X[mt], X[mv]]),
        y_mem=np.concatenate([y[mt], y[mv]]),
    )

# ── Attacks ───────────────────────────────────────────────────────────

def _conf_score(model, X, y):
    p = model.predict_proba(X)
    return p[np.arange(len(y)), y]

def attack_threshold(model, splits):
    mem_s  = _conf_score(model, splits["X_mem"], splits["y_mem"])
    nmem_s = _conf_score(model, splits["X_nm"],  splits["y_nm"])
    y_att  = np.concatenate([np.ones(len(mem_s)), np.zeros(len(nmem_s))])
    s_att  = np.concatenate([mem_s, nmem_s])
    return roc_auc_score(y_att, s_att)

def attack_shadow(target_model, splits, n_shadow=4, seed=RANDOM_SEED):
    import xgboost as xgb
    from sklearn.linear_model import LogisticRegression

    rng = np.random.default_rng(seed)
    X_sp, y_sp = splits["X_sp"], splits["y_sp"]
    n_sp = len(X_sp)

    def extract_features(model, X, y):
        p = model.predict_proba(X)
        p0, p1 = p[:, 0], p[:, 1]
        max_p  = np.maximum(p0, p1)
        eps    = 1e-9
        ent    = -(p0 * np.log(p0 + eps) + p1 * np.log(p1 + eps))
        conf   = p[np.arange(len(y)), y]
        return np.column_stack([p0, p1, max_p, ent, conf])

    X_meta, y_meta = [], []
    for i in range(n_shadow):
        idx = rng.permutation(n_sp)
        n_in = int(0.60 * n_sp)
        in_i, out_i = idx[:n_in], idx[n_in:]
        sm = xgb.XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1,
                                subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0,
                                eval_metric="auc", random_state=seed+200+i, verbosity=0)
        try:
            sm.fit(X_sp[in_i], y_sp[in_i])
        except Exception:
            continue
        feats_in  = extract_features(sm, X_sp[in_i],  y_sp[in_i])
        feats_out = extract_features(sm, X_sp[out_i], y_sp[out_i])
        X_meta.append(feats_in);  y_meta.extend([1] * len(feats_in))
        X_meta.append(feats_out); y_meta.extend([0] * len(feats_out))

    if not X_meta:
        return None

    X_meta = np.vstack(X_meta)
    y_meta = np.array(y_meta)
    meta = LogisticRegression(max_iter=200, random_state=seed)
    meta.fit(X_meta, y_meta)

    feats_mem  = extract_features(target_model, splits["X_mem"], splits["y_mem"])
    feats_nmem = extract_features(target_model, splits["X_nm"],  splits["y_nm"])
    X_att = np.vstack([feats_mem, feats_nmem])
    y_att = np.concatenate([np.ones(len(feats_mem)), np.zeros(len(feats_nmem))])
    att_scores = meta.predict_proba(X_att)[:, 1]
    return roc_auc_score(y_att, att_scores)

# ── DP-LR ─────────────────────────────────────────────────────────────

class ScaledDP:
    def __init__(self, sc, cl): self.sc, self.cl = sc, cl
    def predict_proba(self, X): return self.cl.predict_proba(self.sc.transform(X))

def train_dp_lr(splits, epsilon):
    scaler = StandardScaler()
    Xs = scaler.fit_transform(splits["X_mt"])
    # diffprivlib 0.6.6 - no multi_class parameter
    clf = dpl.models.LogisticRegression(
        epsilon=epsilon, data_norm=5.0, max_iter=200, random_state=RANDOM_SEED
    )
    clf.fit(Xs, splits["y_mt"])
    wrapped = ScaledDP(scaler, clf)
    vl_auc = roc_auc_score(splits["y_mv"], wrapped.predict_proba(splits["X_mv"])[:, 1])
    return wrapped, vl_auc

# ── Verify diffprivlib API ────────────────────────────────────────────

print(f"diffprivlib version: {dpl.__version__}")
try:
    import inspect
    sig = inspect.signature(dpl.models.LogisticRegression.__init__)
    print(f"LogisticRegression params: {list(sig.parameters.keys())}")
except Exception as e:
    print(f"Could not inspect: {e}")

# ── Dataset configs ───────────────────────────────────────────────────

datasets = [
    ("TaiwanCredit",       load_taiwan_credit,     False),
    ("GiveMeSomeCredit",   load_give_me_some_credit, False),
    ("HomeCredit",         load_home_credit,         False),
]

# Load existing results
results_path = os.path.join(RESULTS_DIR, "mia_results_v2.json")
with open(results_path) as f:
    all_results = json.load(f)

t_total = time.time()

for ds_name, loader, _ in datasets:
    print(f"\n{'='*60}")
    print(f"DP-LR experiments for {ds_name}")
    print(f"{'='*60}")
    t0 = time.time()
    X, y = loader()
    splits = mia_split(X, y)
    base_vl = all_results[ds_name]["baseline"]["XGBoost"]["val_auc"]

    for eps in [1.0, 5.0, 10.0]:
        key = f"dp_lr_eps{int(eps)}"
        print(f"  epsilon={eps} ...", end=" ", flush=True)
        t1 = time.time()
        try:
            dm, vl = train_dp_lr(splits, eps)
            t_auc = attack_threshold(dm, splits)
            s_auc = attack_shadow(dm, splits)
            s_str = f"{s_auc:.4f}" if s_auc is not None else "N/A"
            print(f"val_AUC={vl:.4f}  threshold={t_auc:.4f}  shadow={s_str}  ({time.time()-t1:.1f}s)")
            all_results[ds_name]["defenses"][key] = {
                "epsilon": eps,
                "model_val_auc": round(vl, 5),
                "auc_cost": round(base_vl - vl, 5),
                "threshold_auc": round(t_auc, 5),
                "shadow_auc": round(s_auc, 5) if s_auc is not None else None,
            }
        except Exception as e:
            print(f"ERROR: {e}")
            all_results[ds_name]["defenses"][key] = {"error": str(e)}

    print(f"  {ds_name} done in {(time.time()-t0)/60:.1f} min")

# Save patched results
with open(results_path, "w") as f:
    json.dump(all_results, f, indent=2, default=str)

print(f"\nResults saved to {results_path}")
print(f"Total elapsed: {(time.time()-t_total)/60:.1f} min")
