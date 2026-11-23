#!/bin/sh
# Commands used for the reported results. Run from the repository root after placing the data files in data/.
set -e
python scripts/check_data.py data
# main runs: baselines, controls, defences, attacks (5 seeds each). Home Credit is the slowest.
python run_experiments_v3.py --data-dir data --out results/v3 --datasets Taiwan GMSC --ebm --seeds 42 43 44 45 46
python run_experiments_v3.py --data-dir data --out results/v3 --datasets HomeCredit --seeds 42 43 44 45 46
# Home Credit: EBM on an 80,000-record subsample, and XGBoost and LightGBM on the same subsample and on others (sample size series)
python run_experiments_v3.py --data-dir data --out results/v3 --datasets HomeCredit --ebm-subsample 80000 --seeds 42 43 44 45 46
for n in 20000 40000 80000 160000; do
  python run_experiments_v3.py --data-dir data --out results/v3 --datasets HomeCredit --trees-subsample $n --seeds 42 43 44 45 46
done
# summary tables and figures
python aggregate_v3.py results/v3 results/summary
mkdir -p figs
python figs_concept.py figs/
python figs_results.py results/summary figs/
