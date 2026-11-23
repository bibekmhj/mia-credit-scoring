# diffprivlib compatibility note

diffprivlib 0.6.6 does not run unchanged with the library versions pinned in `requirements.txt`.
Two things are handled inside `run_experiments_v3.py`, so you do not need to edit any installed package:

1. diffprivlib passes `multi_class='ovr'` to scikit-learn's `LogisticRegression`. scikit-learn 1.8 removed that
   argument. The script replaces the `__init__` of `diffprivlib.models.LogisticRegression` with an equivalent
   one that leaves the argument out. For a binary problem the model is the same.
2. diffprivlib passes `iprint` to `scipy.optimize.fmin_l_bfgs_b`, which newer SciPy no longer accepts. The script
   wraps the function and drops that argument.

scikit-learn is pinned to 1.8.0 because version 1.9 changes further internals that diffprivlib 0.6.6 relies on.

If you change library versions and the differential privacy runs fail on import or fit, this is the place to look.
The old manual patch described in earlier versions of this repository is no longer needed.
