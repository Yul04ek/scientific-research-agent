# CLAUDE.md

Context for working on this repository. Keep it short and update it when decisions change.

## What this is

`AI-Agent-Yu` started as a terminal coding assistant (Pydantic AI, capabilities, skills; built on OpenRouter in a Linux terminal).
This repo also contains a **research agent** built on the same structure: it collects arXiv papers, indexes them
(text, tables, figure captions), and answers scientific questions with cited evidence. It runs in Google Colab with a free Gemini key.

Task it answers: a small agentic system for scientific research with automated paper collection and indexing,
an agent that chooses its tools itself (literature search, retrieval, figure inspection, Python), at least one
ML/data-analysis component, an evaluation harness, and robust behaviour when evidence is missing or conflicting.

## Layout

- `coding_assistant/` original capstone code. `main.py`, `capabilities/file_operations.py`, `skills/` are unchanged; the old agent is not part of the research flow.
- `coding_assistant/research_agent.py` research agent: `build_agent()`, `ask()` (retries on 429/5xx and timeouts), `run_agent()`.
- `coding_assistant/capabilities/` tools as capabilities: `literature_search` (search_arxiv, collect_papers), `paper_retrieval` (list_papers, retrieve_evidence), `corpus_analysis` (corpus_overview), `figure_inspection` (list_figures, inspect_figure), `python_analysis` (run_python), `tool_logging`, `skills`, `reasoning_effort`.
- `coding_assistant/research/` plain Python behind the tools: `arxiv_client`, `indexer` (pdfplumber), `embeddings`, `retrieval` (dense + BM25, RRF), `clustering` (the ML component), `corpus` (storage layout), `llm` (model calls with timeout and retry).
- `skills_research/` skills for the research agent (`scientific-qa`, `conflicting-evidence`, `verify-claims-with-code`). The old `skills/` folder is not used by it.
- `eval/` evaluation harness: `build_eval_set.py`, `run_eval.py`, `metrics.py`, `agent_questions.jsonl`, `unanswerable.jsonl`, `results/`.
- `colab_research_agent.ipynb` the user notebook for Colab: asks for a topic, collects papers, calibrates the evidence threshold for that corpus, chat; evaluation is optional (`RUN_EVALUATION = False`). It is saved with the outputs of a test run (topic: boundary element methods). `README.md` user-facing description (the old capstone README is in `docs/README_capstone.md`).
- `data/` (corpus, vectors) and `sandbox/` (scripts written by `run_python`) are generated and git-ignored.

## Environment

Variables (Colab: set from Secrets): `BASE_URL` (Gemini OpenAI-compatible endpoint), `API_KEY`, `MODEL_NAME`,
`EVIDENCE_THRESHOLD` (weak-evidence cut-off), optional `EMBED_BACKEND` (local default), `MAX_MODEL_REQUESTS`, `MODEL_TIMEOUT`,
`FREEZE_CORPUS` (set by the eval so collect_papers is switched off), `CONFIRM_COLLECT=1` (the notebook sets it for the chat: `collect_papers` asks `Allow? [y/N]` before downloading). The notebook calibrates `EVIDENCE_THRESHOLD` per corpus and saves it in `data/threshold.txt`. Never print or commit keys.

Run in Colab: `await run_agent()` or `agent = build_agent(); await ask(agent, "...")`.
Evaluation: `python -m eval.build_eval_set`, `python -m eval.run_eval retrieval`, `python -m eval.run_eval agent --judge [--ids q6,q7]`.
In Colab it is more convenient to run `await run_eval.run_agent_eval(use_judge=True)` inside the notebook (live output).

## Design decisions (and why)

- Gemini needs `OpenAIChatModel` (Chat Completions), not the Responses model used in the original course code.
- Embeddings run locally (`BAAI/bge-small-en-v1.5`), so they use no API quota.
- Retrieval is hybrid (dense + BM25 fused by reciprocal rank), max 2 chunks per paper, each chunk carries its page for citations like `[2301.00001v1 p.4]`.
- Weak evidence is flagged in code (`WEAK_EVIDENCE` / `NO_EVIDENCE`) using a calibrated similarity threshold, not by the model's feeling.
- Abstention marker: answers start with `INSUFFICIENT EVIDENCE:` when the corpus does not answer.
- The agent should collect papers only if the corpus is empty or the user asks. The prompt rule alone was not reliable (the agent collected off-topic papers on its own), so the confirmation is enforced in code (`CONFIRM_COLLECT`). The eval freezes the corpus so every run uses the same papers.
- Chat: type a question and press Enter twice to send; `exit` ends the chat (a cell waiting for input ignores the stop button).
- `run_python` saves every script as `sandbox/run_NNN.py`, never overwrites, and the agent names the file in its answer. It is a subprocess with a timeout, not a real security sandbox.
- Clustering: KMeans on abstract embeddings, k chosen by silhouette, validated against arXiv categories (NMI/ARI), clusters described with TF-IDF words.
- Free-tier limits of Gemini matter: about 500 requests per day and 15 per minute for `gemini-3.1-flash-lite`; 503 "high demand" happens often.

## Status (state at last evaluation)

Numbers below are from the conformal prediction corpus. The live Colab test used a second corpus (12 papers on boundary element methods): calibrated threshold 0.714, hybrid again not better than BM25.

- Corpus: 18 papers on conformal prediction (one is about steel, but as an application of conformal prediction, so it is on topic), 1186 chunks.
- Retrieval, 20 synthetic questions: paper-level hit@6 0.60-0.65, page-level 0.25-0.45 (MRR 0.48-0.57). Differences between dense, BM25 and hybrid are within noise at this sample size.
- Weak-evidence threshold: answerable median similarity 0.83, unanswerable 0.60, AUROC 0.994, best threshold 0.774.
- Agent evaluation, 7 questions: 6/7 pass all checks; citations 27/27 valid. q7 failed only the strict format check (right content, missing `INSUFFICIENT EVIDENCE:` marker). Judge score 5.0 over 4 answers is weak evidence (small sample, same model family).
- Clustering is weak (silhouette about 0.23): narrow topic, few papers. Honest finding, not a bug.

## Known limitations / TODO

- Similarity is not an answer: the threshold measures closeness of topic. On a near-topic question with no real answer (BEM vs FEM comparison) the top chunks passed the threshold, and 3 of 6 were reference lists. Idea: skip reference lists when indexing; check "does this passage answer the question?".
- Tables (real tables missed, figure parts taken as tables), figure captions (first line only, lost spaces) and equations (garbled) are extracted imperfectly with pdfplumber. Ideas: join caption lines, `x_tolerance` 1.5, layout-aware parser or vision model.
- The calibration threshold depends on the corpus (0.774 vs 0.714); AUROC 1.0 on easy off-topic questions is an easy case.

- `ask()` restarts the whole question after a 503, so tools run again (repeated side effects). Retry only the model request.
- Add a looser abstention check next to the strict one and report both.
- No relevance filter when collecting: arXiv returns some off-topic papers.
- The research agent has no skill-creation tool (kept from the capstone only in `skills/`); stated imperfection.
- Possible next step: port the harness to `pydantic-evals`.
- Clustering experiment: baseline vs title doubled vs PCA-5 vs k in 2-5, compared by NMI, silhouette (in the original space) and stability.

## Conventions

- Code is topic-independent: changing the topic means a new corpus and new questions in `eval/agent_questions.jsonl`.
- Comments are short, plain English. Keep the code simple and readable.
- Run the offline checks of any change before pushing; real model behaviour can only be checked in Colab.
