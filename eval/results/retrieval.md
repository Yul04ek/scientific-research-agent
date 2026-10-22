## Retrieval quality
20 synthetic questions, 730 chunks, k=6, max 2 chunks per paper.

| mode | level | hit@1 | hit@3 | hit@6 | MRR |
|---|---|---|---|---|---|
| dense | paper | 0.85 | 0.95 | 1.0 | 0.9 |
| dense | page | 0.55 | 0.8 | 0.8 | 0.658 |
| bm25 | paper | 0.75 | 0.95 | 0.95 | 0.842 |
| bm25 | page | 0.55 | 0.75 | 0.75 | 0.642 |
| hybrid | paper | 0.8 | 1.0 | 1.0 | 0.883 |
| hybrid | page | 0.65 | 0.9 | 0.9 | 0.758 |

## Weak-evidence threshold
Best dense similarity: answerable median 0.82, unanswerable median 0.58 (8 off-topic questions).
AUROC 1.0; best threshold **0.744** (balanced accuracy 1.0). Set it with `EVIDENCE_THRESHOLD=0.744`.