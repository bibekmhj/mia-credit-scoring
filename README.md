# Membership Inference Attacks on Credit Scoring Models

Empirical evaluation of membership inference attack (MIA) vulnerability and defense effectiveness
for gradient boosting credit scoring models on three public datasets.

This code accompanies the research paper:

**Membership Inference Attacks on Credit Scoring Models: Empirical Risk Analysis and
Differential Privacy Defenses Under U.S. Banking Privacy Requirements**

Bibek Maharjan, Software Engineer, Financial Services Industry
Submitted to Computers and Security (Elsevier)

---

## What this study does

A membership inference attack is a procedure in which an adversary with query-only access to a
machine learning model's prediction API attempts to determine whether a specific record was part
of the model's training set. This study measures how vulnerable gradient boosting credit scoring
models are to such attacks, and how effectively various defenses reduce that vulnerability.

**Datasets:** Three public credit scoring datasets (total n = 487,510 records)
- UCI Default of Credit Card Clients (Taiwan Credit, n = 29,999)
- Kaggle Give Me Some Credit (n = 150,000)
- Home Credit Default Risk (n = 307,511)

**Models evaluated:**
- XGBoost
- LightGBM
- Explainable Boosting Machine (EBM)

**Attacks evaluated:**
- Confidence-threshold attack
- Shadow-model attack (4 shadow models, logistic regression meta-classifier)

**Defenses evaluated:**
- Confidence rounding (K = 5 and K = 10 bins)
- Laplace output perturbation (scale = 0.02 and 0.05)
- Stronger regularization (reg_lambda = 10, max_depth = 3)
- Differentially private logistic regression (epsilon = 1, 5, 10)

**Primary metric:** Attack AUC-ROC (0.5 = random, higher = more vulnerable)

---

## Key results

| Dataset | Model | Shadow AUC (baseline) | Shadow AUC (regularized) |
|---------|-------|-----------------------|--------------------------|
| TaiwanCredit | XGBoost | 0.5699 | 0.5032 |
| TaiwanCredit | LightGBM | 0.5553 | - |
| TaiwanCredit | EBM | 0.5030 | - |
| GiveMeSomeCredit | XGBoost | 0.5133 | 0.5022 |
| HomeCredit | XGBoost | 0.5070 | 0.5009 |

The train-validation AUC gap is the strongest predictor of attack success
(Spearman rho = 0.733, p = 0.025).

Full results are in `results/mia_results_v2.json`.

---

## Repository structure

```
mia-credit-scoring/
  README.md                   - this file
  requirements.txt            - Python dependencies
  .gitignore
  run_experiments_v2.py       - main experiment script (all models and defenses)
  run_dp_only.py              - differential privacy experiments only
  driver_analysis.py          - OLS regression and Spearman correlation analysis
  build_paper.js              - Word manuscript builder (Node.js)
  package.json                - Node.js dependencies for manuscript builder
  results/
    mia_results_v2.json       - all experimental results (JSON)
  data/
    README_DATA.md            - instructions for downloading the three datasets
  docs/
    DIFFPRIVLIB_PATCH.md      - documents the diffprivlib 0.6.6 compatibility patch
```

Datasets are NOT included in this repository. See `data/README_DATA.md` for download instructions.
The results JSON is included so the analysis and manuscript can be reproduced without re-running
the full experiments (which take several hours on a standard machine).

---

## Requirements

Python 3.11 or later is recommended. See `requirements.txt` for all Python dependencies.

Node.js 18 or later is required only if you want to rebuild the Word manuscript (`build_paper.js`).

Key libraries:
- xgboost >= 2.0
- lightgbm >= 4.0
- interpret-community (for EBM)
- diffprivlib == 0.6.6 (see patch note below)
- scikit-learn >= 1.3
- pandas, numpy, scipy

---

## Quickstart

### 1. Install Python dependencies

```
pip install -r requirements.txt
```

### 2. Download datasets

Follow the instructions in `data/README_DATA.md`. Place the CSV files in the `data/` folder
with the exact filenames listed there.

### 3. Run the main experiments

```
python run_experiments_v2.py
```

This runs all baseline models (XGBoost, LightGBM, EBM), all non-DP defenses, and both attacks
on all three datasets. Results are written to `results/mia_results_v2.json`. Runtime is
approximately 2-4 hours on a standard CPU machine.

### 4. Run the differential privacy experiments

```
python run_dp_only.py
```

This trains differentially private logistic regression (epsilon = 1, 5, 10) on each dataset
and patches the results file in place. Runtime is approximately 20-40 minutes.

### 5. Run the driver analysis

```
python driver_analysis.py
```

This prints the OLS regression table, Spearman correlation, and clean versions of Tables 2-4
from the paper.

### 6. Rebuild the Word manuscript (optional)

```
npm install
node build_paper.js
```

This produces `manuscript_v1.docx`. Requires Node.js and the four figure PNG files in `/tmp/`.
See the figure generation section in `run_experiments_v2.py` for the matplotlib commands,
or regenerate figures separately before running the manuscript builder.

---

## Diffprivlib compatibility note

diffprivlib 0.6.6 passes `multi_class='ovr'` internally when initializing its logistic regression,
but scikit-learn 1.5+ removed that parameter. If you encounter:

```
LogisticRegression.__init__() got an unexpected keyword argument 'multi_class'
```

apply the patch described in `docs/DIFFPRIVLIB_PATCH.md`.

---

## Reproducibility

All experiments use `random_state=42` and `numpy.random.default_rng(42)` for reproducibility.
The MIA data split is deterministic given the seed: 40% member-train, 10% member-val,
25% non-member (evaluation), 25% shadow pool.

Hardware used: standard CPU (no GPU required). Python 3.11, Ubuntu Linux.

---

## License

Code in this repository is released under the MIT License.

The datasets are subject to their own terms. See `data/README_DATA.md` for details.
No consumer financial records or proprietary bank data were used in this study.

---

## Citation

If you use this code, please cite the paper once it is published. A citation entry will be
added here after acceptance.

---

## Contact

Bibek Maharjan - bbkmhj06@gmail.com
