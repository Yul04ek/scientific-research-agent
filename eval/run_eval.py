# Evaluation.
#   python -m eval.run_eval retrieval        retrieval scores + threshold check (no agent calls)
#   python -m eval.run_eval agent [--judge] [--ids q6,q7]  agent behaviour end to end (uses the model)
# Parts: 1) is the source passage found in the top 6?  2) which similarity threshold
# separates answerable from unanswerable questions?  3) did the agent use the right
# tools, give real citations, and say INSUFFICIENT EVIDENCE when it should?

import argparse
import asyncio
import json
import os
import re
from pathlib import Path

from coding_assistant.research import corpus
from coding_assistant.research.llm import chat
from coding_assistant.research.retrieval import Index
from eval.metrics import best_threshold, citation_report, first_hit_rank, retrieval_scores

HERE = Path(__file__).parent
RESULTS = HERE / "results"


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


# ----------------------------------------------------------------- part 1 + 2
def run_retrieval() -> str:
    questions = read_jsonl(HERE / "retrieval_set.jsonl")
    if not questions:
        raise SystemExit("eval/retrieval_set.jsonl missing: run  python -m eval.build_eval_set  first.")
    index = Index.load()
    lines = ["## Retrieval quality", f"{len(questions)} synthetic questions, {len(index)} chunks, k=6, max 2 chunks per paper.\n"]
    lines.append("| mode | level | hit@1 | hit@3 | hit@6 | MRR |")
    lines.append("|---|---|---|---|---|---|")
    results = {}
    for mode in ("dense", "bm25", "hybrid"):
        for level in ("paper", "page"):
            ranks = []
            for q in questions:
                hits = index.search(q["question"], k=6, mode=mode)
                found = [(h.chunk["paper_id"], h.chunk["page"]) for h in hits]
                ranks.append(first_hit_rank(found, (q["paper_id"], q["page"]), level))
            s = retrieval_scores(ranks)
            results[f"{mode}/{level}"] = s
            lines.append(f"| {mode} | {level} | {s['hit@1']} | {s['hit@3']} | {s['hit@6']} | {s['MRR']} |")

    # Calibration of the weak-evidence threshold
    unanswerable = read_jsonl(HERE / "unanswerable.jsonl")
    best_answerable = [index.search(q["question"], k=1, mode="dense")[0].dense for q in questions]
    best_unanswerable = [h[0].dense for h in (index.search(q["question"], k=1, mode="dense") for q in unanswerable) if h]
    calibration = best_threshold(best_answerable, best_unanswerable)
    lines.append("\n## Weak-evidence threshold")
    if calibration:
        import numpy as np

        lines.append(
            f"Best dense similarity: answerable median {np.median(best_answerable):.2f}, "
            f"unanswerable median {np.median(best_unanswerable):.2f} ({len(unanswerable)} off-topic questions).\n"
            f"AUROC {calibration['auroc']}; best threshold **{calibration['threshold']}** "
            f"(balanced accuracy {calibration['balanced_accuracy']}). "
            f"Set it with `EVIDENCE_THRESHOLD={calibration['threshold']}`."
        )
    text = "\n".join(lines)
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "retrieval.json").write_text(json.dumps({"scores": results, "calibration": calibration}, indent=2))
    (RESULTS / "retrieval.md").write_text(text, encoding="utf-8")
    return text


# --------------------------------------------------------------------- part 3
def tools_and_evidence(messages: list) -> tuple[list[str], set[str], str]:
    """From the run's message history: tool names called, citation tags that tools really returned, evidence text."""
    called, tags, evidence = [], set(), []
    for message in messages:
        for part in getattr(message, "parts", []):
            kind = getattr(part, "part_kind", "")
            if kind == "tool-call":
                called.append(part.tool_name)
            elif kind == "tool-return":
                content = str(part.content)
                tags.update(f"[{m.group(1)} p.{m.group(2)}]" if m.group(2) else f"[{m.group(1)} abstract]"
                            for m in re.finditer(r"\[([A-Za-z0-9./_-]+?) (?:p\.(\d+)|abstract)\]", content))
                if part.tool_name in ("retrieve_evidence", "inspect_figure"):
                    evidence.append(content)
    return called, tags, "\n".join(evidence)


def check_item(item: dict, answer: str, called: list[str], valid_tags: set[str]) -> dict:
    cites = citation_report(answer, valid_tags)
    checks = {}
    if item.get("expected_tools"):
        checks["tools"] = all(t in called for t in item["expected_tools"])
    if item["type"] == "unanswerable":
        checks["abstains"] = item.get("expected_marker", "INSUFFICIENT EVIDENCE").lower() in answer.lower()
    else:
        checks["no_false_abstention"] = "insufficient evidence" not in answer.lower()
        if item["type"] in ("answerable", "compute"):
            checks["citations_valid"] = cites["n_citations"] > 0 and cites["n_valid"] == cites["n_citations"]
    if item.get("must_include_any"):
        checks["keywords"] = any(k.lower() in answer.lower() for k in item["must_include_any"])
    return {"checks": checks, "citations": cites, "passed": all(checks.values())}


def judge_faithfulness(question: str, answer: str, evidence: str) -> dict:
    """LLM judge: are all claims in the answer supported by the retrieved evidence? (1-5)"""
    from openai import OpenAI

    from coding_assistant.utils import get_env

    client = OpenAI(base_url=get_env("BASE_URL"), api_key=get_env("API_KEY"))
    prompt = (
        "You grade an answer for faithfulness to evidence. Reply with JSON only: "
        '{"score": 1-5, "unsupported_claims": ["..."]}. 5 = every claim is supported by the evidence, '
        "1 = mostly unsupported. Claims marked 'own experiment' are computations and are not judged.\n\n"
        f"Question: {question}\n\nEvidence:\n{evidence[:9000]}\n\nAnswer:\n{answer}"
    )
    reply = chat(client, model=get_env("MODEL_NAME"), messages=[{"role": "user", "content": prompt}])
    raw = (reply.choices[0].message.content or "").strip().removeprefix("```json").removesuffix("```").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"score": None, "unsupported_claims": [f"judge reply not parseable: {raw[:80]}"]}


async def run_agent_eval(use_judge: bool, only: list[str] | None = None, allow_collect: bool = False) -> str:
    """Ask every question of agent_questions.jsonl (or only the ids in `only`).
    * The corpus is frozen while this runs (FREEZE_CORPUS), unless allow_collect is set.
    * A question that fails (e.g. the model stays overloaded) is recorded as failed, the run goes on.
    * Results are saved after every question; with `only`, they are merged into the earlier results."""
    from coding_assistant.research_agent import ask, build_agent

    freeze_before = os.environ.get("FREEZE_CORPUS")
    if not allow_collect:
        os.environ["FREEZE_CORPUS"] = "1"
    RESULTS.mkdir(exist_ok=True)
    json_path = RESULTS / "agent.json"
    all_items = read_jsonl(HERE / "agent_questions.jsonl")
    items = [i for i in all_items if not only or i["id"] in only]
    saved = {}
    if only and json_path.exists():
        saved = {r["id"]: r for r in json.loads(json_path.read_text(encoding="utf-8"))}

    try:
        agent = build_agent()
        for item in items:
            try:
                result = await ask(agent, item["question"])
                called, tags, evidence = tools_and_evidence(result.all_messages())
                row = {"id": item["id"], "type": item["type"], "tools_called": called, "answer": result.output}
                row.update(check_item(item, result.output, called, tags))
                if use_judge and evidence and item["type"] != "unanswerable":
                    try:
                        row["judge"] = judge_faithfulness(item["question"], result.output, evidence)
                    except Exception as error:  # noqa: BLE001 - a failed judge must not lose the answer
                        row["judge"] = {"score": None, "unsupported_claims": [f"judge failed: {type(error).__name__}"]}
            except Exception as error:  # noqa: BLE001
                row = {
                    "id": item["id"], "type": item["type"], "tools_called": [],
                    "answer": f"ERROR: {type(error).__name__}: {str(error)[:200]}",
                    "checks": {"completed": False}, "citations": {"n_citations": 0, "n_valid": 0}, "passed": False,
                }
            saved[item["id"]] = row
            json_path.write_text(json.dumps([saved[i["id"]] for i in all_items if i["id"] in saved], ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"{item['id']} {item['type']:<12} passed={row['passed']} tools={sorted(set(row['tools_called']))}")
    finally:
        if freeze_before is None:
            os.environ.pop("FREEZE_CORPUS", None)
        else:
            os.environ["FREEZE_CORPUS"] = freeze_before

    rows = [saved[i["id"]] for i in all_items if i["id"] in saved]
    passed = sum(r["passed"] for r in rows)
    lines = ["## Agent evaluation", f"{passed}/{len(rows)} questions passed all checks.\n", "| id | type | passed | failed checks | tools used |", "|---|---|---|---|---|"]
    for r in rows:
        failed = [k for k, v in r["checks"].items() if not v] or ["-"]
        lines.append(f"| {r['id']} | {r['type']} | {'yes' if r['passed'] else 'NO'} | {', '.join(failed)} | {', '.join(sorted(set(r['tools_called'])))} |")
    judged = [r["judge"]["score"] for r in rows if r.get("judge", {}).get("score")]
    if judged:
        lines.append(f"\nLLM-judge faithfulness (1-5): mean {sum(judged) / len(judged):.2f} over {len(judged)} answers.")
    cit = [r["citations"] for r in rows if r["citations"]["n_citations"]]
    if cit:
        lines.append(f"Citations: {sum(c['n_valid'] for c in cit)}/{sum(c['n_citations'] for c in cit)} refer to passages the tools really returned.")
    text = "\n".join(lines)
    (RESULTS / "agent.md").write_text(text, encoding="utf-8")
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("part", choices=["retrieval", "agent"])
    parser.add_argument("--judge", action="store_true", help="add an LLM faithfulness judge (extra model calls)")
    parser.add_argument("--ids", default="", help="only these questions, e.g. q6,q7 (merged into the earlier results)")
    parser.add_argument("--allow-collect", action="store_true", help="let the agent add papers during the run (corpus changes!)")
    args = parser.parse_args()
    if args.part == "retrieval":
        print(run_retrieval())
    else:
        print(asyncio.run(run_agent_eval(args.judge, [i for i in args.ids.split(',') if i] or None, args.allow_collect)))


if __name__ == "__main__":
    main()
