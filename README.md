# Scientific Research Agent

A small agentic system for scientific research. It collects arXiv papers on a topic,
indexes them (text, tables, figure captions) and answers questions with cited evidence.
The agent chooses its tools itself: literature search, retrieval, figure inspection and
Python. When the papers do not answer a question, it says so instead of guessing.

## Quick start (Google Colab, free)

You need a Gemini API key. It is free and takes about two minutes. You do not need to enter any payment details.

1. Create a key at https://aistudio.google.com/apikey
2. Open the notebook in Colab:
   [Open in Colab](https://colab.research.google.com/github/Yul04ek/scientific-research-agent/blob/main/colab_research_agent.ipynb)
3. In Colab, open the key icon (Secrets) in the left sidebar, add a secret named
   `GEMINI_API_KEY`, paste your key and switch on "Notebook access".
4. Choose *Runtime → Run all*. The notebook asks for your research topic, shows the arXiv matches and
   waits for your confirmation. Then it downloads and indexes the papers (about 10 minutes for 12 papers),
   calibrates the evidence threshold for your corpus and starts the chat.
5. In the chat, type a question and press Enter twice. Type `exit` to stop. The evaluation part of the
   notebook does not run unless you set `RUN_EVALUATION = True`.
6. For calculations the agent writes a Python script into the folder `sandbox/` (`run_001.py`, ...). Open a file in
   the file browser to see what was computed. The files stay until the Colab session ends.
6. Sometimes the agent decides that the papers already in the corpus do not answer your question. It then asks
   `Allow? [y/N]` before it downloads additional papers. Downloading costs time and model requests, and it changes
   your corpus, so nothing is downloaded without your `y`. Answer `n` and the agent answers from the papers it has
   and says what is missing.

Example question: *"What does the corpus say about the coverage guarantee of split conformal prediction?"*

The free Gemini tier has daily and per-minute limits. If you see a 429 or 503 error,
the agent waits and retries automatically.

### Run locally (terminal)

    pip install -r requirements-research.txt
    export BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
    export API_KEY=<your Gemini key>
    export MODEL_NAME=gemini-3.1-flash-lite
    python -m coding_assistant.research_agent

### Evaluation results
Two runs, both on the free Gemini tier.

* **Boundary element methods (12 papers). Stored in this repository:** result files in `eval/results/`, questions in
  `eval/agent_questions_bem.jsonl`, a readable report with all answers in `eval/results/agent_report_bem.md`.
  6 of 7 agent questions passed all automatic checks. The failure is q7 (a question the corpus cannot answer):
  the content was right, but the marker `INSUFFICIENT EVIDENCE:` was missing. All 14 citations that carry a page
  were returned by a tool. The 13 citations in q4 (corpus overview) give only a paper id; the check counts them as
  invalid because of that format, although they are papers of the corpus. The LLM judge gave 5, 3, 5, 5 (mean 4.5
  over four answers); for q2 it listed statements that are general knowledge and not in the cited paper.
  Retrieval on 20 synthetic questions: paper-level hit@6 1.0 (dense and hybrid), page-level 0.8 (dense) and 0.9
  (hybrid); calibrated threshold 0.744.
* **Conformal prediction (about 18 papers). An earlier run, files not kept:** 6 of 7 passed, citations 27 of 27,
  as I recorded it at that time. It is not reproducible from this repository until it is run again.

To repeat an evaluation, run the notebook with the same topic and set `RUN_EVALUATION = True` in Part 2. The questions
in `eval/agent_questions.jsonl` are written for conformal prediction; for the boundary element run, copy
`eval/agent_questions_bem.jsonl` over that file first. For another topic, write new questions (see "Known limits").

## Architecture

```
question
   │
   ▼
Agent (Gemini via OpenAIChatModel)  ── instructions + skills (skills_research/*.md)
   │  chooses tools itself, in any order, as often as needed
   ├─ LiteratureSearch   search_arxiv, collect_papers   → arXiv API, PDF download, indexing
   ├─ PaperRetrieval     list_papers, retrieve_evidence → hybrid search (dense + BM25), citation tags
   ├─ CorpusAnalysis     corpus_overview                → KMeans topic clusters (ML component)
   ├─ FigureInspection   list_figures, inspect_figure   → page image + Gemini vision
   ├─ PythonAnalysis     run_python                     → subprocess with timeout; check claims by simulation
   └─ ToolLogging        hook that prints every tool call
```

Data (`data/`): PDFs, `meta.json`, `chunks.jsonl`, `embeddings.npy`, `figures.json`.

## Design choices

* **Chunks keep their page**, so every claim can be cited as `[paper_id p.N]`. The evaluation checks that each cited tag
  was really returned by a tool in that run, so invented citations are detected.
* **Hybrid retrieval**: dense cosine (bge-small, local) + BM25, fused by Reciprocal Rank Fusion. Dense finds paraphrases,
  BM25 finds exact method names and symbols.
* **At most 2 chunks per paper** in the top-k, so that disagreeing papers can both be seen.
* **Tables** are extracted as Markdown chunks with pdfplumber, chosen as a quick start: no GPU or external service,
  and it gives text, tables, word coordinates and page images. **Figures**: captions are searchable text; the page
  image is rendered only when the agent decides to look (`inspect_figure`), because many figures are vector graphics.
  Both parts have known problems, see "Known limitations" below.
* **Missing evidence**: the retrieval tool prints `WEAK_EVIDENCE` / `NO_EVIDENCE` when the best similarity is below a
  threshold that is calibrated on questions the corpus cannot answer; the skill tells the agent to start the answer with
  `INSUFFICIENT EVIDENCE:`. **Conflicting evidence**: the `conflicting-evidence` skill requires two queries, comparison of
  conditions, and a `CONFLICT:` section; the agent can test a claim itself with `run_python`.
* **ML component**: unsupervised clustering of abstract embeddings (KMeans, k chosen by silhouette). Validation uses labels
  that were not used in fitting: the arXiv categories (NMI / ARI). Same idea as clustering penguins and comparing with species.
* **Free-tier friendly**: local embeddings, no extra classification call per message, automatic wait-and-retry on HTTP 429.

## Known limitations

These were found by manual checks against the original PDFs. The corpus is small (about 18 papers on conformal
prediction) and most checks used one paper, so they show problems, not their frequency.

* **Tables: designed but not debugged.** In one paper that I checked by hand (arXiv 2401.13744, https://arxiv.org/abs/2401.13744), two real tables (Table 1 on p. 5, Table 4 on p. 8) were
  not extracted. Parts of figures (a boxed screenshot, bar chart labels) were stored as tables instead. Another
  detection mode did not help on p. 8. Answers that depend on table numbers are not reliable. Possible next steps: a
  layout-aware parser (e.g. Docling, GROBID) or a vision model on page images, as already used for figures. I did not
  compare these options.
* **Figure captions** are found with a regular expression. Only the first line of a caption is stored, some captions
  lose their spaces (text extraction tolerance; a smaller tolerance fixed it in one test), and some figures are not
  detected at all. Reading a figure with `inspect_figure` worked in one manual check (axis labels read correctly),
  which is a single example, not a systematic test.
* **Hybrid retrieval**: the advantage is not demonstrated. The test questions are generated anew in every run. On the
  conformal prediction corpus and in one earlier boundary element run hybrid was not better than BM25 alone; in the
  stored boundary element run it was better at page level (0.9 against 0.75 for BM25). With 20 questions one
  question is 0.05, so these differences are within noise.
* **Evaluation**: 6 of 7 agent questions passed the strict automatic checks in both runs (see "Evaluation results").
  The question set is small and written by me, the citation check only tests that a cited passage was returned by a
  tool (not that it supports the claim), and the LLM judge is a weak signal.
* **Clustering** is weak (silhouette about 0.23 on 18 papers).
* **Similarity is not an answer.** The evidence threshold measures how close a passage is to the question, not
  whether it answers it. On a question about a comparison that the papers do not make, the retrieved passages
  were close in topic (some were reference lists), so no warning was raised and the agent had to say in its own words
  that the comparison is missing.
* **Prompt rules are not guarantees.** The agent was told not to collect papers on its own, and it did anyway.
  Therefore the notebook asks the person in code (`Allow? [y/N]`) before any download.
* **The chat cannot be stopped with the stop button** while it waits for input: type `exit`, or restart the session.
* Synthetic questions are easier than real ones (they share words with their passage), so retrieval scores are optimistic.
* The agent question set is small (7 questions); it shows behaviour, not statistics. Edit `eval/agent_questions.jsonl` for your topic.
* `run_python` runs code in a subprocess with a timeout, not in a security sandbox. Use it only on your own machine/Colab.
* PDF parsing is limited to the first 40 pages and may garble two-column layouts and equations.

## Evaluation

```bash
python -m eval.build_eval_set      # model writes one question per sampled passage (needs the corpus)
python -m eval.run_eval retrieval  # hit@k, MRR for dense / bm25 / hybrid, and threshold calibration
python -m eval.run_eval agent      # end-to-end behaviour on eval/agent_questions.jsonl  (add --judge for an LLM faithfulness score)
```

Results are written to `eval/results/`. The agent checks are deterministic where possible: expected tools were called,
citations are real, abstention happens on unanswerable questions and not on answerable ones, expected keywords appear.

## Background

The structure of the code (the `coding_assistant/` package, capabilities and skills) comes from
my earlier project AI-Agent-Yu, a terminal coding assistant:  https://github.com/Yul04ek/AI-Agent-Yu.git .

The research agent uses its own skills in `skills_research/`. The skills of the original
terminal coding assistant stay in `skills/` and are not connected: that agent ran in a
terminal on OpenRouter, so I kept the two separate for now. Some of them could be useful here.