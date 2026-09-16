# Diffprivlib 0.6.6 Compatibility Patch for scikit-learn 1.5 and Later

## Problem

When running the differential privacy experiments with diffprivlib 0.6.6 and
scikit-learn 1.5 or later, you will see this error:

```
TypeError: LogisticRegression.__init__() got an unexpected keyword argument 'multi_class'
```

This error is not in our code. It is inside diffprivlib's own source file.
diffprivlib 0.6.6 was written when scikit-learn still accepted a `multi_class` parameter
in its LogisticRegression class. scikit-learn 1.5 deprecated this parameter and
scikit-learn 1.8 removed it entirely.

## Location of the problem

Open the diffprivlib source file at this path (adjust for your Python environment):

```
/usr/local/lib/python3.11/dist-packages/diffprivlib/models/logistic_regression.py
```

Go to the line that calls `super().__init__(...)`. On diffprivlib 0.6.6 it looks like:

```python
super().__init__(
    penalty=penalty, dual=False, tol=tol, C=1.0, fit_intercept=fit_intercept,
    intercept_scaling=1, class_weight=class_weight, random_state=random_state,
    solver=solver, max_iter=max_iter, multi_class='ovr', verbose=verbose,
    warm_start=warm_start, n_jobs=n_jobs
)
```

## Fix

Remove `multi_class='ovr',` from that line. The corrected call looks like:

```python
super().__init__(
    penalty=penalty, dual=False, tol=tol, C=1.0, fit_intercept=fit_intercept,
    intercept_scaling=1, class_weight=class_weight, random_state=random_state,
    solver=solver, max_iter=max_iter, verbose=verbose,
    warm_start=warm_start, n_jobs=n_jobs
)
```

Save the file and re-run the experiments.

## Finding the exact line number

Run this in Python to print the source and find the line:

```python
import inspect
import diffprivlib.models.logistic_regression as m
print(inspect.getsource(m))
```

Search for `multi_class` in the output. There will be one occurrence in the
`super().__init__()` call. That is the line to edit.

## Why not upgrade diffprivlib?

As of September 2026, diffprivlib 0.6.6 is the latest stable release and no newer
version has been published that resolves this incompatibility. Check
https://github.com/IBM/differential-privacy-library for updates before applying
this patch, in case a compatible release has since been published.

## Impact on results

Removing `multi_class='ovr'` does not change the mathematical behavior of the model
for binary classification tasks. scikit-learn's LogisticRegression defaults to a
binary one-vs-rest approach for two-class problems when `multi_class` is not specified.
All three credit datasets in this study are binary classification problems.

## Verification

After applying the patch, run:

```
python run_dp_only.py
```

You should see output like:

```
epsilon=1.0 ... val_AUC=0.6752  threshold=0.5002  shadow=0.5002
epsilon=5.0 ... val_AUC=0.7198  threshold=0.5001  shadow=0.4979
epsilon=10.0 ... val_AUC=0.7240  threshold=0.5000  shadow=0.4970
```

Shadow AUC values near 0.500 confirm that DP-LR is effectively blocking the
shadow-model attack.
