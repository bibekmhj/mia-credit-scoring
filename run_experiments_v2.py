"""
Membership Inference Attack (MIA) Experiment Pipeline - v2
Research paper: "Membership Inference Attacks on Credit Scoring Models"

Datasets used (all real public data):
  Taiwan Credit Card Default (UCI, 30,000 records) - kaggle uciml upload
  Give Me Some Credit (Kaggle competition, 150,000 records)
  Home Credit Default Risk (Kaggle competition, 307,511 records)
  [German Credit: Kaggle upload lacked target column; excluded from experiments]

Random seeds are fixed for reproducibility. All results are empirical measurements.
"""

import os, warnings, json, time
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
import xgboost as xgb
import lightgbm as lgb
from interpret.glassbox import ExplainableBoostingClassifier
import diffprivlib as dpl

warnings.filterwarnings("ignore")

DATA_DIR    = "/home/claude/mia_experiment/data"
RESULTS_DIR = "/home/claude/mia_experiment/results"
os.makedirs(RESULTS_DIR, exist_ok=True)

RANDOM_SEED = 42

# ──────────────────────────────────────────────────────────────────────
# 1. DATA LOADERS
# ──────────────────────────────────────────────────────────────────────

def load_taiwan_credit():
    df = pd.read_csv(os.path.join(DATA_DIR, "taiwan_credit.csv"), header=1)
    target_col = "default.payment.next.month" if "default.payment.next.month" in df.columns else df.columns[-1]
    y = df[target_col].astype(int).values
    drop_cols = [target_col] + (["ID"] if "ID" in df.columns else [])
    X = df.drop(columns=drop_cols).values.astype(float)
    X = SimpleImputer(strategy="median").fit_transform(X)
    return X, y, "TaiwanCredit", {"n": len(y), "default_rate": y.mean(), "n_features": X.shape[1]}


def load_give_me_some_credit():
    df = pd.read_csv(os.path.join(DATA_DIR, "give_me_some_credit.csv"), index_col=0)
    df = df.dropna(subset=["SeriousDlqin2yrs"])
    y = df["SeriousDlqin2yrs"].astype(int).values
    X = df.drop(columns=["SeriousDlqin2yrs"]).values.astype(float)
    X = SimpleImputer(strategy="median").fit_transform(X)
    return X, y, "GiveMeSomeCredit", {"n": len(y), "default_rate": y.mean(), "n_features": X.shape[1]}


def load_home_credit(max_rows=None):
    df = pd.read_csv(os.path.join(DATA_DIR, "application_train.csv"))
    if max_rows:
        df = df.sample(n=max_rows, random_state=RANDOM_SEED)
    y = df["TARGET"].astype(int).values
    drop_cols = [c for c in ["TARGET", "SK_ID_CURR"] if c in df.columns]
    X = df.drop(columns=drop_cols)
    for c in X.select_dtypes(include=["object"]).columns:
        X[c] = LabelEncoder().fit_transform(X[c].astype(str))
    X = SimpleImputer(strategy="median").fit_transform(X.values.astype(float))
    return X, y, "HomeCredit", {"n": len(y), "default_rate": y.mean(), "n_features": X.shape[1]}


# ──────────────────────────────────────────────────────────────────────
# 2. MIA SPLIT
# ──────────────────────────────────────────────────────────────────────

def mia_split(X, y, seed=RANDOM_SEED):
    rng = np.random.default_rng(seed)
    n = len(y)
    idx = rng.permutation(n)
    n_mt = int(0.40 * n)   # member train
    n_mv = int(0.10 * n)   # member val (also members for MIA eval)
    n_nm = int(0.25 * n)   # non-members
    # remaining 25% -> shadow pool
    mt, mv, nm = idx[:n_mt], idx[n_mt:n_mt+n_mv], idx[n_mt+n_mv:n_mt+n_mv+n_nm]
    sp = idx[n_mt+n_mv+n_nm:]
    return dict(
        X_mt=X[mt], y_mt=y[mt],
        X_mv=X[mv], y_mv=y[mv],
        X_nm=X[nm], y_nm=y[nm],
        X_sp=X[sp], y_sp=y[sp],
        # Members for attack eval = mt + mv
        X_mem=np.vstack([X[mt], X[mv]]),
        y_mem=np.concatenate([y[mt], y[mv]]),
    )


# ──────────────────────────────────────────────────────────────────────
# 3. MODEL FACTORY
# ──────────────────────────────────────────────────────────────────────

def make_xgb(n_est=200, depth=6, reg_lambda=1.0, seed=RANDOM_SEED):
    return xgb.XGBClassifier(n_estimators=n_est, max_depth=depth,
        learning_rate=0.1, subsample=0.8, colsample_bytree=0.8,
        reg_lambda=reg_lambda, eval_metric="auc",
        random_state=seed, verbosity=0)

def make_lgb(seed=RANDOM_SEED):
    return lgb.LGBMClassifier(n_estimators=200, max_depth=6,
        learning_rate=0.1, subsample=0.8, colsample_bytree=0.8,
        random_state=seed, verbose=-1)

def make_ebm(seed=RANDOM_SEED):
    return ExplainableBoostingClassifier(random_state=seed, n_jobs=-1)


def fit_model(model, splits, is_ebm=False):
    """Train on member-train partition; report train+val AUC."""
    Xtr, ytr = splits["X_mt"], splits["y_mt"]
    Xvl, yvl = splits["X_mv"], splits["y_mv"]
    model.fit(Xtr, ytr)
    tr_auc = roc_auc_score(ytr, model.predict_proba(Xtr)[:, 1])
    vl_auc = roc_auc_score(yvl, model.predict_proba(Xvl)[:, 1])
    return model, tr_auc, vl_auc


# ──────────────────────────────────────────────────────────────────────
# 4. ATTACKS
# ──────────────────────────────────────────────────────────────────────

def _conf_score(model, X, y):
    """Confidence of the model for the true class of each record."""
    p = model.predict_proba(X)
    return p[np.arange(len(y)), y]


def attack_threshold(model, splits):
    """
    Confidence-threshold attack.
    Attack score = P(true class | x). Higher for members (memorized).
    """
    mem_s  = _conf_score(model, splits["X_mem"], splits["y_mem"])
    nmem_s = _conf_score(model, splits["X_nm"],  splits["y_nm"])
    y_att  = np.concatenate([np.ones(len(mem_s)), np.zeros(len(nmem_s))])
    s_att  = np.concatenate([mem_s, nmem_s])
    return roc_auc_score(y_att, s_att)


def attack_shadow(target_model, splits, n_shadow=4, seed=RANDOM_SEED):
    """
    Shadow-model attack.
    Train n_shadow shadow models on disjoint subsets of the shadow pool.
    Features for meta-classifier: [p0, p1, max_p, entropy, correct_confidence]
    """
    rng = np.random.default_rng(seed)
    X_sp, y_sp = splits["X_sp"], splits["y_sp"]
    n_sp = len(X_sp)

    def extract_features(model, X, y):
        p = model.predict_proba(X)          # shape (n, 2)
        p0, p1 = p[:, 0], p[:, 1]
        max_p  = np.maximum(p0, p1)
        eps    = 1e-9
        ent    = -(p0 * np.log(p0 + eps) + p1 * np.log(p1 + eps))
        conf   = p[np.arange(len(y)), y]   # confidence for true class
        return np.column_stack([p0, p1, max_p, ent, conf])

    X_meta, y_meta = [], []

    for i in range(n_shadow):
        idx = rng.permutation(n_sp)
        n_in = int(0.60 * n_sp)
        in_i, out_i = idx[:n_in], idx[n_in:]
        sm = make_xgb(seed=seed + 200 + i)
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


def run_attacks(model, splits, label):
    t_auc = attack_threshold(model, splits)
    s_auc = attack_shadow(model, splits)
    s_str = f"{s_auc:.4f}" if s_auc is not None else "N/A"
    print(f"      [{label}]  threshold_AUC={t_auc:.4f}  shadow_AUC={s_str}")
    return {"threshold_auc": round(t_auc, 5), "shadow_auc": round(s_auc, 5) if s_auc else None}


# ──────────────────────────────────────────────────────────────────────
# 5. DEFENSES
# ──────────────────────────────────────────────────────────────────────

class RoundedModel:
    def __init__(self, base, k=10):
        self.base, self.k = base, k
    def predict_proba(self, X):
        p = self.base.predict_proba(X).copy()
        p[:, 1] = np.clip(np.round(p[:, 1] * self.k) / self.k, 0, 1)
        p[:, 0] = 1 - p[:, 1]
        return p

class PerturbedModel:
    def __init__(self, base, scale=0.05, seed=RANDOM_SEED):
        self.base, self.scale = base, scale
        self.rng = np.random.default_rng(seed)
    def predict_proba(self, X):
        p = self.base.predict_proba(X).copy()
        p[:, 1] = np.clip(p[:, 1] + self.rng.laplace(0, self.scale, len(p)), 0, 1)
        p[:, 0] = 1 - p[:, 1]
        return p


def train_dp_lr(splits, epsilon):
    """DP Logistic Regression via diffprivlib 0.6.6."""
    scaler = StandardScaler()
    Xs = scaler.fit_transform(splits["X_mt"])
    clf = dpl.models.LogisticRegression(
        epsilon=epsilon, data_norm=5.0, max_iter=200, random_state=RANDOM_SEED
    )
    clf.fit(Xs, splits["y_mt"])

    class ScaledDP:
        def __init__(self, sc, cl): self.sc, self.cl = sc, cl
        def predict_proba(self, X): return self.cl.predict_proba(self.sc.transform(X))

    wrapped = ScaledDP(scaler, clf)
    vl_auc = roc_auc_score(splits["y_mv"], wrapped.predict_proba(splits["X_mv"])[:, 1])
    return wrapped, vl_auc


def train_reg_xgb(splits, reg_lambda=10.0, max_depth=3):
    m = make_xgb(n_est=100, depth=max_depth, reg_lambda=reg_lambda)
    m.fit(splits["X_mt"], splits["y_mt"])
    vl_auc = roc_auc_score(splits["y_mv"], m.predict_proba(splits["X_mv"])[:, 1])
    return m, vl_auc


# ──────────────────────────────────────────────────────────────────────
# 6. MAIN
# ──────────────────────────────────────────────────────────────────────

def run_dataset(X, y, name, meta, skip_ebm=False):
    print(f"\n{'='*62}")
    print(f"Dataset: {name}  n={meta['n']}  features={meta['n_features']}  default_rate={meta['default_rate']:.3f}")
    print(f"{'='*62}")
    splits = mia_split(X, y)
    res = {"name": name, "meta": meta, "baseline": {}, "defenses": {}}

    models_to_run = {"XGBoost": make_xgb(), "LightGBM": make_lgb()}
    if not skip_ebm:
        models_to_run["EBM"] = make_ebm()

    best_model, best_name = None, None

    for mname, m in models_to_run.items():
        print(f"\n  Training {mname}...")
        t0 = time.time()
        try:
            trained, tr_auc, vl_auc = fit_model(m, splits)
            gap = tr_auc - vl_auc
            print(f"    train_AUC={tr_auc:.4f}  val_AUC={vl_auc:.4f}  gap={gap:.4f}  ({time.time()-t0:.1f}s)")
            atk = run_attacks(trained, splits, mname)
            res["baseline"][mname] = {
                "train_auc": round(tr_auc, 5),
                "val_auc": round(vl_auc, 5),
                "auc_gap": round(gap, 5),
                **atk,
            }
            if best_model is None:
                best_model, best_name = trained, mname
        except Exception as e:
            print(f"    ERROR: {e}")
            res["baseline"][mname] = {"error": str(e)}

    if best_model is None:
        print("  No baseline model succeeded - skipping defenses.")
        return res

    base_vl_auc = res["baseline"][best_name]["val_auc"]
    print(f"\n  Defenses (base model: {best_name}, val_AUC={base_vl_auc:.4f})...")

    # D1: Rounding
    for k in [5, 10]:
        key = f"rounding_k{k}"
        try:
            dm = RoundedModel(best_model, k=k)
            vl = roc_auc_score(splits["y_mv"], dm.predict_proba(splits["X_mv"])[:, 1])
            atk = run_attacks(dm, splits, f"Round-K{k}")
            res["defenses"][key] = {"model_val_auc": round(vl, 5), "auc_cost": round(base_vl_auc - vl, 5), **atk}
        except Exception as e:
            res["defenses"][key] = {"error": str(e)}

    # D2: Output perturbation
    for scale in [0.02, 0.05]:
        key = f"perturbation_{scale}"
        try:
            dm = PerturbedModel(best_model, scale=scale)
            vl = roc_auc_score(splits["y_mv"], dm.predict_proba(splits["X_mv"])[:, 1])
            atk = run_attacks(dm, splits, f"Perturb-{scale}")
            res["defenses"][key] = {"model_val_auc": round(vl, 5), "auc_cost": round(base_vl_auc - vl, 5), **atk}
        except Exception as e:
            res["defenses"][key] = {"error": str(e)}

    # D3: Regularization
    try:
        rm, vl = train_reg_xgb(splits)
        atk = run_attacks(rm, splits, "RegXGB")
        res["defenses"]["regularization"] = {
            "model_val_auc": round(vl, 5),
            "auc_cost": round(base_vl_auc - vl, 5),
            **atk
        }
    except Exception as e:
        res["defenses"]["regularization"] = {"error": str(e)}

    # D4: DP Logistic Regression at epsilon = 1, 5, 10
    for eps in [1.0, 5.0, 10.0]:
        key = f"dp_lr_eps{int(eps)}"
        try:
            dm, vl = train_dp_lr(splits, eps)
            atk = run_attacks(dm, splits, f"DP-LR-e{eps}")
            res["defenses"][key] = {
                "epsilon": eps,
                "model_val_auc": round(vl, 5),
                "auc_cost": round(base_vl_auc - vl, 5),
                **atk
            }
        except Exception as e:
            res["defenses"][key] = {"error": str(e)}

    return res


def main():
    all_results = {}

    # Taiwan Credit (30K) - full, include EBM
    X, y, name, meta = load_taiwan_credit()
    all_results[name] = run_dataset(X, y, name, meta, skip_ebm=False)

    # Give Me Some Credit (150K) - full, include EBM
    X, y, name, meta = load_give_me_some_credit()
    all_results[name] = run_dataset(X, y, name, meta, skip_ebm=False)

    # Home Credit (307K) - subsample 80K for EBM tractability, keep XGB/LGB on full
    print("\nLoading Home Credit (full 307K for XGB/LGB, 80K subsample for EBM)...")
    X_full, y_full, name, meta = load_home_credit()
    # Run XGB and LGB on full dataset (split to 40% = 123K train)
    splits_full = mia_split(X_full, y_full)
    res_hc = {"name": name, "meta": meta, "baseline": {}, "defenses": {}}
    best_model, best_name, base_vl = None, None, None

    for mname, m in [("XGBoost", make_xgb()), ("LightGBM", make_lgb())]:
        print(f"\n  Training {mname} on full Home Credit ({meta['n']} records)...")
        t0 = time.time()
        try:
            trained, tr_auc, vl_auc = fit_model(m, splits_full)
            gap = tr_auc - vl_auc
            print(f"    train_AUC={tr_auc:.4f}  val_AUC={vl_auc:.4f}  gap={gap:.4f}  ({time.time()-t0:.1f}s)")
            atk = run_attacks(trained, splits_full, mname)
            res_hc["baseline"][mname] = {
                "train_auc": round(tr_auc, 5),
                "val_auc": round(vl_auc, 5),
                "auc_gap": round(gap, 5),
                **atk,
            }
            if best_model is None:
                best_model, best_name, base_vl = trained, mname, vl_auc
        except Exception as e:
            print(f"    ERROR: {e}")
            res_hc["baseline"][mname] = {"error": str(e)}

    # EBM on 80K subsample
    rng = np.random.default_rng(RANDOM_SEED + 1)
    sub_idx = rng.choice(len(y_full), 80000, replace=False)
    X_sub, y_sub = X_full[sub_idx], y_full[sub_idx]
    splits_sub = mia_split(X_sub, y_sub)
    print(f"\n  Training EBM on 80K subsample of Home Credit...")
    t0 = time.time()
    try:
        ebm = make_ebm()
        trained_ebm, tr_auc, vl_auc = fit_model(ebm, splits_sub)
        gap = tr_auc - vl_auc
        print(f"    train_AUC={tr_auc:.4f}  val_AUC={vl_auc:.4f}  gap={gap:.4f}  ({time.time()-t0:.1f}s)")
        atk = run_attacks(trained_ebm, splits_sub, "EBM-80K")
        res_hc["baseline"]["EBM_subsample_80K"] = {
            "train_auc": round(tr_auc, 5),
            "val_auc": round(vl_auc, 5),
            "auc_gap": round(gap, 5),
            "note": "EBM trained on 80K subsample",
            **atk,
        }
    except Exception as e:
        print(f"    ERROR EBM: {e}")
        res_hc["baseline"]["EBM_subsample_80K"] = {"error": str(e)}

    # Defenses on best full-data model
    if best_model is not None:
        print(f"\n  Defenses on {best_name} (val_AUC={base_vl:.4f})...")
        for k in [5, 10]:
            key = f"rounding_k{k}"
            try:
                dm = RoundedModel(best_model, k=k)
                vl = roc_auc_score(splits_full["y_mv"], dm.predict_proba(splits_full["X_mv"])[:, 1])
                atk = run_attacks(dm, splits_full, f"Round-K{k}")
                res_hc["defenses"][key] = {"model_val_auc": round(vl, 5), "auc_cost": round(base_vl - vl, 5), **atk}
            except Exception as e:
                res_hc["defenses"][key] = {"error": str(e)}

        for scale in [0.02, 0.05]:
            key = f"perturbation_{scale}"
            try:
                dm = PerturbedModel(best_model, scale=scale)
                vl = roc_auc_score(splits_full["y_mv"], dm.predict_proba(splits_full["X_mv"])[:, 1])
                atk = run_attacks(dm, splits_full, f"Perturb-{scale}")
                res_hc["defenses"][key] = {"model_val_auc": round(vl, 5), "auc_cost": round(base_vl - vl, 5), **atk}
            except Exception as e:
                res_hc["defenses"][key] = {"error": str(e)}

        try:
            rm, vl = train_reg_xgb(splits_full)
            atk = run_attacks(rm, splits_full, "RegXGB")
            res_hc["defenses"]["regularization"] = {
                "model_val_auc": round(vl, 5), "auc_cost": round(base_vl - vl, 5), **atk}
        except Exception as e:
            res_hc["defenses"]["regularization"] = {"error": str(e)}

        for eps in [1.0, 5.0, 10.0]:
            key = f"dp_lr_eps{int(eps)}"
            try:
                dm, vl = train_dp_lr(splits_full, eps)
                atk = run_attacks(dm, splits_full, f"DP-LR-e{eps}")
                res_hc["defenses"][key] = {
                    "epsilon": eps, "model_val_auc": round(vl, 5),
                    "auc_cost": round(base_vl - vl, 5), **atk}
            except Exception as e:
                res_hc["defenses"][key] = {"error": str(e)}

    all_results[name] = res_hc

    # Save
    out = os.path.join(RESULTS_DIR, "mia_results_v2.json")
    with open(out, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n\nAll results saved: {out}")
    return all_results


if __name__ == "__main__":
    t_total = time.time()
    results = main()
    print(f"\nTotal elapsed: {(time.time()-t_total)/60:.1f} min")
