## Agent evaluation
6/7 questions passed all checks.

| id | type | passed | failed checks | tools used |
|---|---|---|---|---|
| q1 | answerable | yes | - | list_papers, load_skill, retrieve_evidence, run_python |
| q2 | answerable | yes | - | collect_papers, list_papers, retrieve_evidence, search_arxiv |
| q3 | compute | yes | - | list_papers, load_skill, retrieve_evidence, run_python |
| q4 | overview | yes | - | corpus_overview, list_papers |
| q5 | figure | yes | - | inspect_figure, list_figures, list_papers, retrieve_evidence, search_arxiv |
| q6 | unanswerable | yes | - | list_papers, load_skill |
| q7 | unanswerable | NO | abstains | collect_papers, list_papers, search_arxiv |

LLM-judge faithfulness (1-5): mean 4.50 over 4 answers.
Citations: 14/27 refer to passages the tools really returned.