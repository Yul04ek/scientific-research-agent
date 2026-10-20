---
name: conflicting-evidence
description: Load this skill when papers might disagree, when results differ between sources, or when the user asks whether a claim is true or settled.
---

* Search at least two different queries, and look at passages from at least two different papers before you conclude.
* Compare under the same conditions: dataset, assumptions, sample size, metric, year. Differences in conditions often explain a disagreement; say so.
* If sources disagree, begin that part of the answer with `CONFLICT:` and give each side with its citation tags. Do not average them and do not silently pick one.
* If you can test the claim yourself with `run_python`, do it and report whether your result supports side A, side B, or neither.
* State how confident you are and why (number of papers, how similar their settings are, whether a paper is only an abstract).
* A claim found in only one paper is "reported by one paper", not "established".
* If the corpus has too little to judge, say `INSUFFICIENT EVIDENCE:` rather than guessing.
