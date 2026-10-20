# Makes the retrieval test set from the corpus itself: for random passages the model
# writes a question that the passage answers. run_eval.py then checks if retrieval
# finds the passage again.   Run: python -m eval.build_eval_set

import json
import os
import random

from openai import OpenAI

from coding_assistant.research import corpus
from coding_assistant.research.llm import chat
from coding_assistant.utils import get_env

N_QUESTIONS = int(os.getenv("N_EVAL_QUESTIONS", "40"))
PROMPT = (
    "Below is a passage from a scientific paper. Write ONE specific question that this passage answers and that a "
    "researcher might ask. The question must be understandable without the passage: do not say 'the passage', "
    "'the paper' or 'the authors'. Use terms from the field, not copied sentences. Reply with the question only.\n\n"
    "Passage:\n{text}"
)


def main() -> None:
    random.seed(0)
    chunks = [c for c in corpus.load_chunks() if c["kind"] == "text" and len(c["text"].split()) >= 80]
    if not chunks:
        raise SystemExit("No suitable chunks. Collect papers first.")
    sample = random.sample(chunks, min(N_QUESTIONS, len(chunks)))
    client = OpenAI(base_url=get_env("BASE_URL"), api_key=get_env("API_KEY"))
    rows = []
    for chunk in sample:
        reply = chat(
            client,
            model=get_env("MODEL_NAME"),
            messages=[{"role": "user", "content": PROMPT.format(text=chunk["text"][:1800])}],
        )
        question = (reply.choices[0].message.content or "").strip().strip('"')
        if question:
            rows.append({"question": question, "paper_id": chunk["paper_id"], "page": chunk["page"], "chunk_id": chunk["chunk_id"]})
    out = corpus.data_dir().parent / "eval" / "retrieval_set.jsonl"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    print(f"Wrote {len(rows)} questions to {out}")


if __name__ == "__main__":
    main()
