---
name: data-cleaning
description: Load this skill when preparing or cleaning a dataset before analysis (missing values, types, outliers).
---

* Always inspect before changing anything: `df.info()`, `df.describe()`, `df.isna().sum()`.
* Missing values: explain the options (drop rows, drop columns, fill with mean/median/mode, or leave as-is) and let the user choose. State what you did and how many rows it affected.
* Data types: check `df.dtypes`. Convert columns to the right type (numbers, dates, categories) and explain why a wrong type causes problems.
* Outliers: detect with a simple, explainable method (e.g. values beyond mean ± 3*std, or the IQR rule). Do NOT remove them automatically — show them and ask the user, since in science an outlier may be a real finding.
* Duplicates: check with `df.duplicated().sum()` before removing.
* Never overwrite the original file. Work on a copy and save cleaned data to a new file in the sandbox.
* After cleaning, report a short before/after summary (rows, columns, missing values).
