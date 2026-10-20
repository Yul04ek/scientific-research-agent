---
name: statistical-tests
description: Load this skill when the user wants to test a hypothesis, compare groups, or check correlations (t-test, ANOVA, chi-square, correlation).
---

* Use `scipy.stats` for tests. Import as `from scipy import stats`.
* Before testing, ask or check: how many groups are being compared, and is the data continuous or categorical? This determines the right test.
* Common test selection:
- Two groups, continuous data: `stats.ttest_ind()` (independent) or `stats.ttest_rel()` (paired).
- Three or more groups, continuous data: `stats.f_oneway()` (one-way ANOVA).
- Two categorical variables: `stats.chi2_contingency()`.
- Relationship between two continuous variables: `stats.pearsonr()` (linear) or `stats.spearmanr()` (non-linear/ranked).
* Always state the null hypothesis in plain language before running the test (e.g. "no difference between group means").
* Check assumptions before testing: normality (`stats.shapiro()`) and equal variance (`stats.levene()`) for t-tests/ANOVA. If assumptions are violated, suggest the non-parametric alternative (e.g. `stats.mannwhitneyu()` instead of `ttest_ind`).
* Report the result in plain language: the statistic, the p-value, and what it means (e.g. "p = 0.03, which is below 0.05, so we reject the null hypothesis — there is a statistically significant difference").
* Never claim causation from a correlation or test result — remind the user this shows association, not cause.
* Use a significance threshold of 0.05 unless the user specifies otherwise, and state this assumption explicitly.


