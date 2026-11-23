# Data

The datasets are not stored in this repository. They are public and must be downloaded by you, then placed in
this folder with the exact file names below.

| File name expected | Source | Rows | Columns | Defaults |
|---|---|---|---|---|
| `taiwan_credit.csv` | UCI "Default of Credit Card Clients" (https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients), also on Kaggle as `uciml/default-of-credit-card-clients-dataset` | 30,000 | 25 (ID, 23 features, `default.payment.next.month`) | 6,636 (22.12%) |
| `give_me_some_credit.csv` | Kaggle competition "Give Me Some Credit", file `cs-training.csv`, renamed (https://www.kaggle.com/c/GiveMeSomeCredit/data) | 150,000 | 12 (index column, `SeriousDlqin2yrs`, 10 features) | 10,026 (6.68%) |
| `application_train.csv` | Kaggle competition "Home Credit Default Risk" (https://www.kaggle.com/c/home-credit-default-risk/data) | 307,511 | 122 (`SK_ID_CURR`, `TARGET`, 120 features) | 24,825 (8.07%) |

Notes
- Taiwan Credit: the header must be in the first row of the CSV. The UCI download is an XLS file whose first row holds
  labels X1 to X23 and whose second row holds the column names; if you use that file, export it to CSV with the second
  row as the header. The script drops the `ID` column and does not use it as a feature.
- Give Me Some Credit: the first column is a row index and is read as the index.
- Home Credit: the script drops `SK_ID_CURR` and `TARGET` from the features and label-encodes text columns.
- Kaggle competition data are governed by the competition rules and Kaggle's terms. A Kaggle account is needed.

## Check your files

```
python scripts/check_data.py data
```

This prints the shape and number of defaults of each file and compares them with the expected values above.

## Checksums of the files used for the reported results (SHA-256)

```
a0f0ab49d6326671d6cd83be5c88dcf18007025fe9a53ecd699119c871176ca1  taiwan_credit.csv
1bd46da486a5708c58c7b01a034fae2a13b327f6f7b62ea7ba4fe3b5824b24ac  give_me_some_credit.csv
52e96b895b1112e1c853f670e58372719c8441c5ed1c57ac2f7fad559d784f5f  application_train.csv
```

If your download has a different checksum but the same number of rows, the same columns and the same number of
defaults, the content is very likely the same and only the line endings or the file format differ. If the counts differ,
the results will not match.
