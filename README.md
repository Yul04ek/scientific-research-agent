# AI Agent Yu: research mode

A small agentic system that collects arXiv papers on a topic, indexes them (text, tables, figure captions),
and answers questions with cited evidence. It reuses the structure of the coding assistant: the same
`coding_assistant/` package, the same `AbstractCapability` + `FunctionToolset` pattern, and the same Markdown skills.

## Run it (Colab)

Open `colab_research_agent.ipynb` and run the cells from top to bottom. You need a Gemini API key in
Colab Secrets under the name `GEMINI_API_KEY` (Notebook access on).

Terminal alternative:

```bash
pip install -r requirements-research.txt
export BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
export API_KEY=...            # Gemini key
export MODEL_NAME=gemini-3.8-flash   # use the model id shown in Google AI Studio
python -m coding_assistant.research_agent
```

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
   ├─ ReasoningEffort    manual @low / @high            (auto-classifier is off by default)
   └─ ToolLogging        hook that prints every tool call
```

Data (`data/`): PDFs, `meta.json`, `chunks.jsonl`, `embeddings.npy`, `figures.json`.

## Design choices

* **Chunks keep their page**, so every claim can be cited as `[paper_id p.N]`. The evaluation checks that each cited tag
  was really returned by a tool in that run, so invented citations are detected.
* **Hybrid retrieval**: dense cosine (bge-small, local) + BM25, fused by Reciprocal Rank Fusion. Dense finds paraphrases,
  BM25 finds exact method names and symbols.
* **At most 2 chunks per paper** in the top-k, so that disagreeing papers can both be seen.
* **Tables** are extracted separately as Markdown chunks. **Figures**: captions are searchable text; the page image is
  rendered only when the agent decides to look (`inspect_figure`), because many figures are vector graphics.
* **Missing evidence**: the retrieval tool prints `WEAK_EVIDENCE` / `NO_EVIDENCE` when the best similarity is below a
  threshold that is calibrated on questions the corpus cannot answer; the skill tells the agent to start the answer with
  `INSUFFICIENT EVIDENCE:`. **Conflicting evidence**: the `conflicting-evidence` skill requires two queries, comparison of
  conditions, and a `CONFLICT:` section; the agent can test a claim itself with `run_python`.
* **ML component**: unsupervised clustering of abstract embeddings (KMeans, k chosen by silhouette). Validation uses labels
  that were not used in fitting: the arXiv categories (NMI / ARI). Same idea as clustering penguins and comparing with species.
* **Free-tier friendly**: local embeddings, no extra classification call per message, automatic wait-and-retry on HTTP 429.

## Evaluation

```bash
python -m eval.build_eval_set      # model writes one question per sampled passage (needs the corpus)
python -m eval.run_eval retrieval  # hit@k, MRR for dense / bm25 / hybrid, and threshold calibration
python -m eval.run_eval agent      # end-to-end behaviour on eval/agent_questions.jsonl  (add --judge for an LLM faithfulness score)
```

Results are written to `eval/results/`. The agent checks are deterministic where possible: expected tools were called,
citations are real, abstention happens on unanswerable questions and not on answerable ones, expected keywords appear.

## Known limits

* Synthetic questions are easier than real ones (they share words with their passage), so retrieval scores are optimistic.
* The agent question set is small (7 questions); it shows behaviour, not statistics. Edit `eval/agent_questions.jsonl` for your topic.
* `run_python` runs code in a subprocess with a timeout, not in a security sandbox. Use it only on your own machine/Colab.
* PDF parsing is limited to the first 40 pages and may garble two-column layouts and equations.
