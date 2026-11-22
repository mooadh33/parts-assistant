"""Step 10: benchmark models on eval/questions.jsonl -> eval/results.md
Usage: python -m eval.run_benchmark claude-sonnet-4-5 claude-haiku-4-5 gpt-4o gpt-4o-mini
Quality = keyword hit-rate (objective, cheap). Optional: add an LLM-as-judge pass + manual spot checks and report both.
Models without an API key run in mock mode: the numbers are then NOT meaningful (a warning is printed)."""
import json
import os
import statistics
import sys
from pathlib import Path
from app import llm, rag, security

QS = [json.loads(l) for l in Path(__file__).with_name("questions.jsonl").read_text().splitlines()]


def run_one(model, item):
    q = item["q"]
    if security.looks_like_injection(q):
        return "blockiert", 0.0, 0
    route, _ = rag.route(q)
    if route == "sql":
        res, sql, cols, rows = rag.ask_sql(q, model)
        return " ".join(str(c) for r in rows for c in r), res.cost_usd, res.latency_ms
    res, _ = rag.ask_rag(q, model)
    return res.text, res.cost_usd, res.latency_ms


def main(models):
    rows = []
    for m in models:
        key_ok = (m.startswith("claude") and os.getenv("ANTHROPIC_API_KEY")) or (m.startswith("gpt") and os.getenv("OPENAI_API_KEY"))
        if not key_ok:
            print(f"WARNING: no API key for {m} -> mock mode, numbers not meaningful")
        hits, costs, lats = [], [], []
        for it in QS:
            try:
                txt, c, l = run_one(m, it)
            except ValueError:
                txt, c, l = "", 0.0, 0
            ok = all(k.lower() in txt.lower() for k in it["keywords"])
            hits.append(ok); costs.append(c); lats.append(l)
        rows.append((m, 100 * sum(hits) / len(hits), statistics.median(lats), 100 * sum(costs), "real" if key_ok else "MOCK"))
    out = ["| Model | Accuracy % | Median latency ms | Cost / 100 q (USD) | Mode |", "|---|---|---|---|---|"]
    out += [f"| {m} | {a:.0f} | {l:.0f} | {c:.4f} | {mode} |" for m, a, l, c, mode in rows]
    Path(__file__).with_name("results.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1:] or ["claude-sonnet-4-5", "claude-haiku-4-5"])
