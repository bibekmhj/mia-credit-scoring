# Dataset Download Instructions

The datasets used in this study are not included in this repository. They are publicly available
and must be downloaded separately. Place each file in this `data/` folder with the exact filename
shown below before running the experiments.

---

## Dataset 1 - Taiwan Credit (UCI Default of Credit Card Clients)

**Filename expected:** `taiwan_credit.csv`

**Source:** UCI Machine Learning Repository
https://archive.ics.uci.edu/ml/datasets/default+of+credit+card+clients

**Alternative (Kaggle):**
https://www.kaggle.com/datasets/uciml/default-of-credit-card-clients-dataset

**Citation:**
Yeh IC, Lien CH. The comparisons of data mining techniques for the predictive accuracy of
probability of default of credit card clients. Expert Systems with Applications.
2009;36(2):2473-2480. doi:10.1016/j.eswa.2007.12.020

**Notes:**
- n = 29,999 credit card clients in Taiwan
- Target column: `default.payment.next.month` (1 = default, 0 = no default)
- Default rate: approximately 22%
- The UCI download is an XLS file. Export it to CSV before placing it in data/.
- The Kaggle version is already a CSV.
- The first row of the Kaggle CSV is a header row with column indices. The script uses
  `header=1` when loading this file, which handles that correctly.

**License:** Publicly available for research and educational use.

---

## Dataset 2 - Give Me Some Credit (Kaggle)

**Filename expected:** `give_me_some_credit.csv`

**Source:** Kaggle competition
https://www.kaggle.com/c/GiveMeSomeCredit/data

**Notes:**
- Download `cs-training.csv` from the competition data page and rename it to
  `give_me_some_credit.csv`.
- n = 150,000 borrowers
- Target column: `SeriousDlqin2yrs` (1 = delinquency, 0 = no delinquency)
- Default rate: approximately 6.7%
- A Kaggle account is required to download competition data.

**License:** Competition dataset. Use is governed by Kaggle's competition rules.
For research and non-commercial use, check Kaggle's current terms at
https://www.kaggle.com/terms before use.

---

## Dataset 3 - Home Credit Default Risk (Kaggle)

**Filename expected:** `application_train.csv`

**Source:** Kaggle competition
https://www.kaggle.com/c/home-credit-default-risk/data

**Notes:**
- Download `application_train.csv` from the competition data page. The filename can be
  kept as is.
- n = 307,511 loan applicants
- Target column: `TARGET` (1 = default, 0 = repaid)
- Default rate: approximately 8.1%
- This is the largest dataset used in the study. The file is approximately 166 MB.
- A Kaggle account is required. The Kaggle CLI (`pip install kaggle`) makes downloading easier:
  `kaggle competitions download -c home-credit-default-risk -f application_train.csv`

**License:** Competition dataset. Use is governed by Kaggle's competition rules.
For research and non-commercial use, check Kaggle's current terms at
https://www.kaggle.com/terms before use.

---

## Dataset that was excluded

**German Credit (UCI)**

The Kaggle upload of this dataset (uciml/german-credit) does not include the target class
column. Only nine feature columns are present with no credit risk label. This dataset was
therefore excluded from the study. A future replication could obtain the full dataset with
the target column directly from the UCI repository at
https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data

---

## Verifying your downloads

After placing all files, run:

```
python -c "
import pandas as pd
print('TaiwanCredit:     ', pd.read_csv('data/taiwan_credit.csv', header=1).shape)
print('GiveMeSomeCredit: ', pd.read_csv('data/give_me_some_credit.csv', index_col=0).shape)
print('HomeCredit:       ', pd.read_csv('data/application_train.csv').shape)
"
```

Expected output (approximate):

```
TaiwanCredit:      (29999, 25)
GiveMeSomeCredit:  (150000, 11)
HomeCredit:        (307511, 122)
```

---

## Data privacy note

All three datasets are publicly released for research purposes. No proprietary bank data,
internal customer records, or nonpublic personal information (NPI) was used in this study.
The datasets contain anonymized or competition-use financial records and are suitable for
academic research under the terms linked above.
