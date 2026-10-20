---
name: verify-claims-with-code
description: Load this skill when a claim from a paper can be checked with a simulation or a calculation, or when the user wants numbers, a plot, or data analysis.
---

* Write one complete script and run it with `run_python`. Use numpy, pandas, scipy, scikit-learn; set a random seed.
* Keep it fast: at most about 60 seconds. Use fewer repetitions first, increase only if the result is noisy.
* Print the final numbers (mean, standard error, number of repetitions). Do not print raw arrays.
* Report: what the paper claims (with citation tag), what you simulated (settings), what you got, and whether they agree. If they differ, name possible reasons (assumptions broken, small sample, different definition) and do not hide the difference.
* Label the result "own experiment" so the user never confuses it with a published result.
* Every script is saved by `run_python` as `sandbox/run_NNN.py`. End your answer with the file name(s) of the script(s) you used, so the user can open and rerun them.
