# Membership Inference Attacks on Gradient Boosting Credit Scoring Models

Code, per-seed results and summary tables for the manuscript

**Membership Inference Attacks on Gradient Boosting Credit Scoring Models: A Multi-Split Evaluation of Attacks, Defences and Controls on Three Public Datasets**

Bibek Maharjan, Home & Auto Lending Technology, JPMorgan Chase & Co., Wilmington, DE, USA (bibekmhj7426@gmail.com)

Status: manuscript prepared for submission to Discover Artificial Intelligence (Springer Nature). This is version 3 of the code and results.
It replaces version 2, whose design had known problems (see "What changed from version 2").

[![DOI](https://zenodo.org/badge/1372404733.svg)](https://doi.org/10.5281/zenodo.22783058)

## What this repository does

A membership inference attack tries to decide, from a model's predicted probabilities, whether a record was in the model's training set.
The code measures this risk for XGBoost, LightGBM and Explainable Boosting Machine (EBM) credit models on three public datasets, and tests
simple defences against non-private controls.

- Datasets: Taiwan Credit (UCI, 30,000 records), Give Me Some Credit (150,000), Home Credit Default Risk (307,511). See `data/README_DATA.md`.
- Attacks: confidence-threshold attack (score = probability of the true class) and shadow-model attack (4 shadow models, logistic regression
  on [p0, p1, max, entropy, p[y]]). Reported as AUC-ROC and as true positive rate at 0.1 percent and 1 percent false positive rate.
- Design: each dataset is split 40 percent member-train, 10 percent member-validation, 25 percent non-member, 25 percent shadow pool.
  Members are the member-train records only. Everything is repeated for five seeds (42 to 46) and summarised as mean, SD and 95 percent t interval.
- Defences on XGBoost: rounding (K = 5, 10), Laplace noise (0.02, 0.05), regularisation, validation-tuned XGBoost (control), and differentially
  private logistic regression (diffprivlib, epsilon = 1, 5, 10). Controls: non-private logistic regression, with and without row clipping to norm 5.
  Defended models are attacked with matched shadow models that copy the defended recipe.
- Sample size series: XGBoost and LightGBM on random subsamples of Home Credit (20,000 to 160,000 records). EBM on Home Credit uses an
  80,000-record subsample, with XGBoost and LightGBM run on the same subsample for a fair comparison.

## Main results (mean +/- 95 percent interval over five seeds)

| Dataset | Model | Train-validation gap | Threshold attack AUC | Shadow attack AUC |
|---|---|---|---|---|
| Taiwan Credit | XGBoost | 0.195 | 0.567 +/- 0.010 | 0.586 +/- 0.008 |
| Taiwan Credit | LightGBM | 0.173 | 0.554 +/- 0.009 | 0.569 +/- 0.009 |
| Taiwan Credit | EBM | 0.028 | 0.506 +/- 0.006 | 0.506 +/- 0.006 |
| Give Me Some Credit | XGBoost | 0.071 | 0.504 +/- 0.001 | 0.514 +/- 0.002 |
| Give Me Some Credit | LightGBM | 0.062 | 0.504 +/- 0.001 | 0.510 +/- 0.002 |
| Give Me Some Credit | EBM | 0.010 | 0.499 +/- 0.001 | 0.503 +/- 0.002 |
| Home Credit | XGBoost | 0.131 | 0.513 +/- 0.001 | 0.509 +/- 0.002 |
| Home Credit | LightGBM | 0.105 | 0.510 +/- 0.001 | 0.506 +/- 0.002 |
| Home Credit | EBM (80,000 subsample) | 0.090 | 0.508 +/- 0.002 | 0.507 +/- 0.003 |

Home Credit, XGBoost, different numbers of records:

| Records used | Member-train | Gap | Shadow attack AUC |
|---|---|---|---|
| 20,000 | 8,000 | 0.311 | 0.607 +/- 0.011 |
| 40,000 | 16,000 | 0.275 | 0.573 +/- 0.005 |
| 80,000 | 32,000 | 0.248 | 0.545 +/- 0.001 |
| 160,000 | 64,000 | 0.188 | 0.521 +/- 0.002 |
| 307,511 | 123,004 | 0.131 | 0.509 +/- 0.002 |

The full tables, including the defences, the controls and the true positive rates at low false positive rates, are in `results/summary/`.

## Repository structure

```
README.md
LICENSE
requirements.txt                 pinned versions used for the reported results
run_experiments_v3.py            experiments (attacks, defences, controls)
aggregate_v3.py                  per-seed JSON -> summary CSV tables and driver analysis
figs_results.py                  result figures from the summary tables
figs_concept.py                  two conceptual diagrams (threat model, workflow)
run_all.sh                       the commands used, in order
scripts/check_data.py            checks the three data files (shape, defaults, SHA-256)
data/README_DATA.md              where to get the data, expected counts, checksums
docs/DIFFPRIVLIB_NOTE.md         compatibility note for diffprivlib 0.6.6
results/v3/                      one JSON file per dataset and seed
results/summary/                 summary CSV tables and driver.json
legacy_v2/                       version 2 scripts and results, kept for the record, superseded
```

## How to reproduce

```
pip install -r requirements.txt
# put the three data files in data/ (see data/README_DATA.md), then
python scripts/check_data.py data
bash run_all.sh
```

Run times on a 2-core machine with 7 GB RAM, per seed: about 1 minute for Taiwan Credit or Give Me Some Credit (more with EBM), about 2 minutes for the
Home Credit main run, 4 to 10 minutes for EBM on the 80,000-record Home Credit subsample, and 1 to 5 minutes for each XGBoost and LightGBM subsample run.
`run_all.sh` lists each command, so you can run the parts separately.
Each run skips result files that already exist, so an interrupted run can be resumed.

## What changed from version 2

Version 2 (kept in `legacy_v2/`) had these problems, all corrected in version 3:
1. Member-validation records, which the target never saw, were counted as members. Members are now the member-train records only.
2. The Taiwan Credit file was read with the wrong header row, which dropped one record and kept the ID column as a feature.
3. Results came from one split and one seed. Version 3 uses five seeds with confidence intervals.
4. The shadow models were always XGBoost, even for defended models. Version 3 adds matched shadow models.
5. The regularised XGBoost used 100 trees without documentation, and there was no tuned or linear control. Both are added and documented.
6. Only AUC-ROC was reported. Version 3 adds the true positive rate at low false positive rates.

Numbers in version 2 results and in earlier drafts of the manuscript should not be used.

## Differential privacy caveats

The differentially private logistic regression uses diffprivlib (objective perturbation) with inputs standardised by a scaler that is fitted on the
training data without noise, and rows clipped to norm 5. The stated epsilon therefore applies to the fitting step given the scaling and not to the
whole pipeline. See `docs/DIFFPRIVLIB_NOTE.md` for the two compatibility changes made in code.

## Licence and data

Code: MIT licence (see `LICENSE`). The datasets are not redistributed. Kaggle data are governed by the competition rules. No proprietary bank data
or employer data were used.

## Citation

If you use this code or the results, please cite the manuscript when it is published, and the archived code record
https://doi.org/10.5281/zenodo.22783058 (check that the record shows version 3).
