---
name: reproducibility
description: Load this skill when the user wants their analysis or experiment to be reproducible by others.
---

* Set a random seed whenever randomness is involved (e.g. `random.seed(42)`, `np.random.seed(42)`), so results are identical on re-run.
* Record package versions the code depends on. Suggest a `requirements.txt` listing each library and its version.
* Avoid hard-coded absolute paths (like `/home/user/...`). Use relative paths so the code runs on another machine.
* Keep raw data untouched. Read the original, write results to separate files — never overwrite inputs.
* Make the run order explicit: a script should run top to bottom without manual steps, or document the order clearly.
* Prefer explicit parameters at the top of the script over "magic numbers" buried in the code, so others can see and change them.
* Briefly explain to the user *why* each step matters for reproducibility — many scientists have not met these ideas before.
