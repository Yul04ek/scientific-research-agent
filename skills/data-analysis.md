---
name: data-analysis
description: Load this skill when analyzing tabular data (CSV, Excel) with pandas.
---

* Use pandas for tabular data. Read files with `pd.read_csv()` or `pd.read_excel()`.
* Before analyzing, always inspect the data first: `df.head()`, `df.info()`, `df.describe()`.
* Check for missing values with `df.isna().sum()` and explain how you handle them.
* Prefer clear, named intermediate variables over long one-line chains, so a non-programmer can follow each step.
* Add a short comment above each block explaining *what* it does in plain language.
* When summarizing results, describe findings in words (e.g. "the average is X"), not just raw output.
* Do not assume column names — read them from the data and confirm with the user if ambiguous.
