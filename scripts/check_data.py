"""Check that the three input files have the expected shape and number of defaults, and print their SHA-256."""
import hashlib, os, sys
import pandas as pd

d = sys.argv[1] if len(sys.argv) > 1 else "data"
EXPECT = {
    "taiwan_credit.csv": (30000, 25, "default.payment.next.month", 6636, None),
    "give_me_some_credit.csv": (150000, 12, "SeriousDlqin2yrs", 10026, 0),
    "application_train.csv": (307511, 122, "TARGET", 24825, None),
}
ok = True
for fn, (n, k, tcol, nd, idx) in EXPECT.items():
    path = os.path.join(d, fn)
    if not os.path.exists(path):
        print(f"MISSING  {fn}"); ok = False; continue
    df = pd.read_csv(path, index_col=idx)
    got = (len(df), df.shape[1] + (1 if idx is not None else 0), int(df[tcol].sum()))
    good = got == (n, k, nd)
    ok &= good
    sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
    print(f"{'OK     ' if good else 'DIFFERS'}  {fn}: rows={got[0]} cols={got[1]} defaults={got[2]} (expected {n}, {k}, {nd})  sha256={sha}")
sys.exit(0 if ok else 1)
