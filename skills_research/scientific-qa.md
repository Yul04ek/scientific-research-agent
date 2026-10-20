---
name: scientific-qa
description: Load this skill when the user asks a scientific question that should be answered from the collected papers.
---

Follow this workflow. You may skip steps that are clearly not needed.

1. Call `list_papers` to see what the corpus covers. Call `collect_papers` (arXiv syntax, e.g. `all:"conformal prediction" AND all:coverage`) only if the corpus is empty or the user asks you to collect papers; at most once per question. If the question is outside the topic of the corpus, do NOT collect: answer with `INSUFFICIENT EVIDENCE:`, say what the corpus covers, and offer to collect papers on the new topic.
2. Call `retrieve_evidence` with a short query in plain words (no quotes, no OR/AND, no LaTeX or formulas). Use 1-3 different queries if the question has several parts; use `paper_id` to read one paper in depth. Make at most 3 `retrieve_evidence` calls per question: then answer with what you found, or start with `INSUFFICIENT EVIDENCE:`. Never repeat a search that only rephrases the previous one.
3. If the question is about a figure or a table, use `list_figures` and then `inspect_figure`.
4. If a claim can be checked by a calculation or a small simulation, write the code and call `run_python`. Report the numbers you got and compare them with the paper.
5. If the question is about the structure of the field ("what approaches exist?"), call `corpus_overview`.

## Answer format

* Start with the direct answer in one or two sentences.
* Support it with bullet points. End every bullet that uses the literature with its citation tag, copied exactly from the tool result, with the page: `[2301.00001v1 p.4]`. One tag per bracket; for two sources write `[2301.00001v1 p.4] [2405.00002v2 p.7]`. A tag without the page number is not accepted.
* Mark your own computations as "own experiment" and give the code settings (sample size, repetitions, seed).
* Do not cite a paper you did not retrieve in this conversation.

## When the evidence is missing

* If `retrieve_evidence` returns `WEAK_EVIDENCE` or `NO_EVIDENCE`, first try one more query with different plain words (do not collect papers for this). If it stays weak, begin the answer with `INSUFFICIENT EVIDENCE:` and say what the corpus does contain instead.
* Never answer a literature question from your own memory without saying so.
