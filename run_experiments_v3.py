"""
Membership inference experiments, version 3 (corrected and extended).

Changes from run_experiments_v2.py
  1. Members are the member-train records only (v2 also counted the 10% member-validation
     records, which the target never saw, as members).
  2. Taiwan Credit is read with header=0 and the ID column is dropped (v2 used header=1, which
     lost one record and kept ID as a feature).
  3. Several seeds (different data splits, shadow pools and model seeds) instead of one.
  4. Extra attack metrics: TPR at 0.1% and 1% FPR in addition to AUC-ROC.
  5. Extra baselines: non-private logistic regression (with and without row clipping to norm 5)
     and a validation-tuned XGBoost (depth and number of trees chosen on member-validation).
  6. Shadow-model attack in two forms: shadows that are always XGBoost ("xgb-shadow", as in v2) and
     "matched" shadows that copy the defended model's training recipe and output post-processing.
  7. Median imputation is fitted on member-train only.

Usage
  python run_experiments_v3.py --data-dir data --out results/v3 --seeds 42 43 44 45 46
  python run_experiments_v3.py --data-dir data --datasets Taiwan --seeds 42 --ebm
"""
import argparse, json, os, time, warnings
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, roc_curve
import sklearn.linear_model as _lm
import xgboost as xgb
import lightgbm as lgb

warnings.filterwarnings("ignore")

# diffprivlib 0.6.6 passes multi_class='ovr' to scikit-learn, which removed that argument in 1.8.
# Instead of editing the installed library, replace its __init__ with an equivalent one that omits the
# argument (binary problems behave the same).
import diffprivlib as dpl  # noqa: E402
from diffprivlib.models.logistic_regression import LogisticRegression as _DPLR  # noqa: E402
from diffprivlib.accountant import BudgetAccountant as _BA  # noqa: E402

def _dp_init(self, *, epsilon=1.0, data_norm=None, tol=1e-4, C=1.0, fit_intercept=True, max_iter=100, verbose=0,
             warm_start=False, n_jobs=None, random_state=None, accountant=None, **unused_args):
    _lm.LogisticRegression.__init__(self, penalty="l2", dual=False, tol=tol, C=C, fit_intercept=fit_intercept,
                                    intercept_scaling=1.0, class_weight=None, random_state=random_state,
                                    solver="lbfgs", max_iter=max_iter, verbose=verbose,
                                    warm_start=warm_start, n_jobs=n_jobs)
    self.epsilon = epsilon; self.data_norm = data_norm; self.classes_ = None
    self.accountant = _BA.load_default(accountant)
_DPLR.__init__ = _dp_init

# newer SciPy versions no longer accept the iprint argument that diffprivlib passes to fmin_l_bfgs_b
import scipy.optimize as _opt  # noqa: E402
_fmin = _opt.fmin_l_bfgs_b
def _fmin_compat(*a, iprint=None, disp=None, **k):
    return _fmin(*a, **k)
_opt.fmin_l_bfgs_b = _fmin_compat

NJOBS = os.cpu_count() or 2


# --------------------------------------------------------------------------- data
def load_taiwan(d):
    df = pd.read_csv(os.path.join(d, "taiwan_credit.csv"))            # header in row 0
    y = df["default.payment.next.month"].astype(int).values
    X = df.drop(columns=["default.payment.next.month", "ID"]).values.astype(float)
    return X, y

def load_gmsc(d):
    df = pd.read_csv(os.path.join(d, "give_me_some_credit.csv"), index_col=0)
    y = df["SeriousDlqin2yrs"].astype(int).values
    X = df.drop(columns=["SeriousDlqin2yrs"]).values.astype(float)
    return X, y

def load_hc(d):
    df = pd.read_csv(os.path.join(d, "application_train.csv"))
    y = df["TARGET"].astype(int).values
    X = df.drop(columns=["TARGET", "SK_ID_CURR"])
    for c in X.select_dtypes(exclude=[np.number]).columns:
        X[c] = pd.factorize(X[c].astype(str))[0]                        # label encoding
    return X.values.astype(float), y

LOADERS = {"Taiwan": load_taiwan, "GMSC": load_gmsc, "HomeCredit": load_hc}


# --------------------------------------------------------------------------- split
def mia_split(n, seed):
    rng = np.random.default_rng(seed)
    idx = rng.permutation(n)
    a, b, c = int(.40 * n), int(.10 * n), int(.25 * n)
    return dict(mt=idx[:a], mv=idx[a:a + b], nm=idx[a + b:a + b + c], sp=idx[a + b + c:])


# --------------------------------------------------------------------------- models
def make_xgb(seed, n_est=200, depth=6, lam=1.0):
    return xgb.XGBClassifier(n_estimators=n_est, max_depth=depth, learning_rate=0.1, subsample=0.8,
                             colsample_bytree=0.8, reg_lambda=lam, eval_metric="auc",
                             random_state=seed, verbosity=0, n_jobs=NJOBS)

def make_lgb(seed):
    return lgb.LGBMClassifier(n_estimators=200, max_depth=6, learning_rate=0.1, subsample=0.8,
                              colsample_bytree=0.8, random_state=seed, verbose=-1, n_jobs=NJOBS)

class XGBFactory:
    def __init__(self, **kw): self.kw = kw
    def __call__(self, X, y, seed):
        m = make_xgb(seed, **self.kw); m.fit(X, y); return m

def clip_rows(X, c):
    nrm = np.linalg.norm(X, axis=1, keepdims=True)
    return X * np.minimum(1.0, c / np.maximum(nrm, 1e-12))

class LRModel:
    """Non-private L2 logistic regression on standardised inputs; optional row clipping at fit time."""
    def __init__(self, seed, clip=None): self.seed, self.clip = seed, clip
    def fit(self, X, y):
        self.sc = StandardScaler().fit(X)
        Xs = self.sc.transform(X)
        if self.clip: Xs = clip_rows(Xs, self.clip)
        self.clf = LogisticRegression(max_iter=1000, random_state=self.seed).fit(Xs, y); return self
    def predict_proba(self, X): return self.clf.predict_proba(self.sc.transform(X))

class DPLRModel:
    """diffprivlib logistic regression (objective perturbation), standardised inputs, data_norm=5."""
    def __init__(self, seed, eps): self.seed, self.eps = seed, eps
    def fit(self, X, y):
        self.sc = StandardScaler().fit(X)
        self.clf = dpl.models.LogisticRegression(epsilon=self.eps, data_norm=5.0, max_iter=200,
                                                 random_state=self.seed).fit(self.sc.transform(X), y); return self
    def predict_proba(self, X): return self.clf.predict_proba(self.sc.transform(X))

class Factory:
    def __init__(self, cls, **kw): self.cls, self.kw = cls, kw
    def __call__(self, X, y, seed): return self.cls(seed, **self.kw).fit(X, y)


# --------------------------------------------------------------------------- output post-processing
def post_round(k):
    def f(p, rng):
        q = p.copy(); q[:, 1] = np.clip(np.round(q[:, 1] * k) / k, 0, 1); q[:, 0] = 1 - q[:, 1]; return q
    return f

def post_noise(scale):
    def f(p, rng):
        q = p.copy(); q[:, 1] = np.clip(q[:, 1] + rng.laplace(0, scale, len(q)), 0, 1); q[:, 0] = 1 - q[:, 1]; return q
    return f

def released(model, X, post, seed):
    p = model.predict_proba(X)
    return post(p, np.random.default_rng(seed)) if post else p


# --------------------------------------------------------------------------- attacks
def feats(p, y):
    p0, p1 = p[:, 0], p[:, 1]
    ent = -(p0 * np.log(p0 + 1e-9) + p1 * np.log(p1 + 1e-9))
    return np.column_stack([p0, p1, np.maximum(p0, p1), ent, p[np.arange(len(y)), y]])

def metrics(s_mem, s_nm):
    y = np.r_[np.ones(len(s_mem)), np.zeros(len(s_nm))]; s = np.r_[s_mem, s_nm]
    fpr, tpr, _ = roc_curve(y, s)
    tpr_at = lambda f: float(tpr[np.searchsorted(fpr, f, side="right") - 1])
    return {"auc": float(roc_auc_score(y, s)), "tpr_fpr0.1": tpr_at(0.001), "tpr_fpr1": tpr_at(0.01)}

def build_meta(factory, Xsp, ysp, seed, post=None, n_shadow=4):
    """Train n_shadow shadow models on random 60% subsets of the shadow pool; fit the meta-classifier."""
    rng = np.random.default_rng(seed + 1000)
    F, M = [], []
    for i in range(n_shadow):
        idx = rng.permutation(len(ysp)); k = int(.6 * len(ysp)); tin, tout = idx[:k], idx[k:]
        sm = factory(Xsp[tin], ysp[tin], seed + 200 + i)
        for ids, lab in ((tin, 1), (tout, 0)):
            F.append(feats(released(sm, Xsp[ids], post, seed + 300 + i), ysp[ids])); M.append(np.full(len(ids), lab))
    return LogisticRegression(max_iter=200, random_state=seed).fit(np.vstack(F), np.concatenate(M))

def attack_all(model, post, D, meta=None, meta_matched=None, seed=0):
    """Return threshold-attack and shadow-attack metrics for a released model."""
    Xm, ym, Xn, yn = D["Xmt"], D["ymt"], D["Xnm"], D["ynm"]
    pm, pn = released(model, Xm, post, seed + 1), released(model, Xn, post, seed + 2)
    out = {"threshold": metrics(pm[np.arange(len(ym)), ym], pn[np.arange(len(yn)), yn])}
    fm, fn = feats(pm, ym), feats(pn, yn)
    if meta is not None:
        out["shadow_xgb"] = metrics(meta.predict_proba(fm)[:, 1], meta.predict_proba(fn)[:, 1])
    if meta_matched is not None:
        out["shadow_matched"] = metrics(meta_matched.predict_proba(fm)[:, 1], meta_matched.predict_proba(fn)[:, 1])
    return out

def val_auc(model, post, D, seed):
    return float(roc_auc_score(D["ymv"], released(model, D["Xmv"], post, seed + 3)[:, 1]))


# --------------------------------------------------------------------------- one dataset, one seed
def prepare(X, y, seed):
    sp = mia_split(len(y), seed)
    imp = SimpleImputer(strategy="median").fit(X[sp["mt"]])           # fitted on member-train only
    Xi = imp.transform(X)
    return dict(Xmt=Xi[sp["mt"]], ymt=y[sp["mt"]], Xmv=Xi[sp["mv"]], ymv=y[sp["mv"]],
                Xnm=Xi[sp["nm"]], ynm=y[sp["nm"]], Xsp=Xi[sp["sp"]], ysp=y[sp["sp"]])

def run_one(X, y, seed, ebm=False, log=print, only_ebm=False, only_trees=False):
    D = prepare(X, y, seed); t0 = time.time(); R = {"seed": seed, "baseline": {}, "defences": {}, "info": {}}
    n_mt = len(D["ymt"])
    Xs = StandardScaler().fit(D["Xmt"]).transform(D["Xmt"])
    R["info"].update(n_member_train=n_mt, n_nonmember=len(D["ynm"]), n_shadow_pool=len(D["ysp"]),
                     n_features=D["Xmt"].shape[1], frac_rows_norm_gt5=float((np.linalg.norm(Xs, axis=1) > 5).mean()))
    def rec(name, model, post, meta, matched, store):
        tr = float(roc_auc_score(D["ymt"], model.predict_proba(D["Xmt"])[:, 1])); va = val_auc(model, post, D, seed)
        store[name] = {"train_auc": tr, "val_auc": va, "gap": tr - va, **attack_all(model, post, D, meta, matched, seed)}
        a = store[name]; log(f"    {name:22s} val={va:.4f} gap={tr-va:.4f} thr={a['threshold']['auc']:.4f} "
                             f"xgbS={a.get('shadow_xgb',{}).get('auc',float('nan')):.4f} "
                             f"matchS={a.get('shadow_matched',{}).get('auc',float('nan')):.4f}  [{time.time()-t0:.0f}s]")
    Xsp, ysp = D["Xsp"], D["ysp"]
    meta_xgb = build_meta(XGBFactory(), Xsp, ysp, seed); log(f"    shadows built [{time.time()-t0:.0f}s]")

    if only_ebm:                                                      # EBM alone (used for the 80,000-record subsample)
        from interpret.glassbox import ExplainableBoostingClassifier
        eb = ExplainableBoostingClassifier(random_state=seed, n_jobs=NJOBS).fit(D["Xmt"], D["ymt"])
        rec("EBM", eb, None, meta_xgb, None, R["baseline"]); R["info"]["seconds"] = time.time() - t0
        return R

    # baselines
    xg = make_xgb(seed); xg.fit(D["Xmt"], D["ymt"]); rec("XGBoost", xg, None, meta_xgb, meta_xgb, R["baseline"])
    lg = make_lgb(seed); lg.fit(D["Xmt"], D["ymt"]); rec("LightGBM", lg, None, meta_xgb, None, R["baseline"])
    if only_trees:                                                    # XGBoost and LightGBM alone on the same subsample as the EBM run
        R["info"]["seconds"] = time.time() - t0
        return R
    lr = LRModel(seed).fit(D["Xmt"], D["ymt"]); meta_lr = build_meta(Factory(LRModel), Xsp, ysp, seed)
    rec("LogisticRegression", lr, None, meta_xgb, meta_lr, R["baseline"])
    lrc = LRModel(seed, clip=5.0).fit(D["Xmt"], D["ymt"]); meta_lrc = build_meta(Factory(LRModel, clip=5.0), Xsp, ysp, seed)
    rec("LogisticRegression_clip5", lrc, None, meta_xgb, meta_lrc, R["baseline"])
    if ebm:
        from interpret.glassbox import ExplainableBoostingClassifier
        eb = ExplainableBoostingClassifier(random_state=seed, n_jobs=NJOBS).fit(D["Xmt"], D["ymt"])
        rec("EBM", eb, None, meta_xgb, None, R["baseline"])

    # defences applied to the XGBoost baseline
    for k in (5, 10):
        post = post_round(k)
        rec(f"rounding_k{k}", xg, post, meta_xgb, build_meta(XGBFactory(), Xsp, ysp, seed, post), R["defences"])
    for s in (0.02, 0.05):
        post = post_noise(s)
        rec(f"noise_{s}", xg, post, meta_xgb, build_meta(XGBFactory(), Xsp, ysp, seed, post), R["defences"])
    reg = XGBFactory(n_est=100, depth=3, lam=10.0)
    rm = reg(D["Xmt"], D["ymt"], seed)
    rec("regularised", rm, None, meta_xgb, build_meta(reg, Xsp, ysp, seed), R["defences"])
    # validation-tuned XGBoost: depth chosen on member-validation, trees by early stopping
    best = None
    for depth in (3, 4, 6):
        m = xgb.XGBClassifier(n_estimators=400, max_depth=depth, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8,
                              eval_metric="auc", early_stopping_rounds=30, random_state=seed, verbosity=0, n_jobs=NJOBS)
        m.fit(D["Xmt"], D["ymt"], eval_set=[(D["Xmv"], D["ymv"])], verbose=False)
        v = m.best_score
        if best is None or v > best[0]: best = (v, depth, m.best_iteration + 1)
    _, bd, bn = best
    tuned = XGBFactory(n_est=bn, depth=bd)
    tm = tuned(D["Xmt"], D["ymt"], seed)
    rec("tuned_xgb", tm, None, meta_xgb, build_meta(tuned, Xsp, ysp, seed), R["defences"])
    R["info"]["tuned_xgb"] = {"depth": bd, "n_estimators": bn}
    for eps in (1.0, 5.0, 10.0):
        f = Factory(DPLRModel, eps=eps); dm = f(D["Xmt"], D["ymt"], seed)
        rec(f"dp_lr_eps{int(eps)}", dm, None, meta_xgb, build_meta(f, Xsp, ysp, seed), R["defences"])
    R["info"]["seconds"] = time.time() - t0
    return R


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data"); ap.add_argument("--out", default="results/v3")
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44, 45, 46])
    ap.add_argument("--datasets", nargs="+", default=list(LOADERS)); ap.add_argument("--ebm", action="store_true")
    ap.add_argument("--ebm-subsample", type=int, default=0, help="run only EBM on a random subsample of this size")
    ap.add_argument("--trees-subsample", type=int, default=0, help="run only XGBoost and LightGBM on the same random subsample (matched comparison for EBM)")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for ds in a.datasets:
        X, y = LOADERS[ds](a.data_dir)
        print(f"\n=== {ds}: n={len(y)} features={X.shape[1]} default_rate={y.mean():.4f} defaults={int(y.sum())}", flush=True)
        for seed in a.seeds:
            tag = f"{ds}_EBM{a.ebm_subsample}" if a.ebm_subsample else (f"{ds}_TREES{a.trees_subsample}" if a.trees_subsample else ds)
            fn = os.path.join(a.out, f"{tag}_seed{seed}.json")
            if os.path.exists(fn): print("  skip", fn); continue
            print(f"  seed {seed}", flush=True)
            if a.ebm_subsample or a.trees_subsample:
                n_sub = a.ebm_subsample or a.trees_subsample
                sub = np.random.default_rng(seed + 1).choice(len(y), n_sub, replace=False)
                R = run_one(X[sub], y[sub], seed, log=lambda s: print(s, flush=True), only_ebm=bool(a.ebm_subsample), only_trees=bool(a.trees_subsample))
            else:
                R = run_one(X, y, seed, ebm=a.ebm, log=lambda s: print(s, flush=True))
            R["dataset"] = ds; R["n"] = len(y); R["default_rate"] = float(y.mean())
            json.dump(R, open(fn, "w"), indent=1)

if __name__ == "__main__":
    main()
