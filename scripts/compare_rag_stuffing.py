"""US-16: compare RAG (top-5 retrieval) with prompt-stuffing (every document in the prompt).

Run after both evaluations, in CloudShell from the repo folder:
    GUARDRAIL_ID=$GID python3 scripts/run_eval.py              # RAG -> eval/results/latest.json
    GUARDRAIL_ID=$GID python3 scripts/run_eval.py --stuffing   # baseline -> eval/results/stuffing.json
    python3 scripts/compare_rag_stuffing.py                    # -> eval/rag-vs-stuffing.md
Same emails, same model, same prompts, guardrail and fact check. Only the source passages differ.
"""
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
R = ROOT / "eval" / "results"


def load(name):
    return {x["id"]: x for x in json.loads((R / name).read_text(encoding="utf-8")) if "error" not in x["result"]}


rag, stuff = load("latest.json"), load("stuffing.json")
ids = sorted(set(rag) & set(stuff))
# Retrieval only matters where passages were used: everything except spam/supplier.
used = [i for i in ids if rag[i]["result"]["retrieved"] or stuff[i]["result"]["retrieved"]]


def summarise(runs, label):
    res = [runs[i]["result"] for i in ids]
    src = [runs[i]["result"] for i in used]
    fc = [r["fact_check"] for r in res if r.get("fact_check")]
    sup = sum(len(f["supported"]) for f in fc)
    uns = sum(len(f["unsupported"]) for f in fc)
    calc = sum(len(f["calculated"]) for f in fc)
    checked = sup + uns + calc
    return {
        "label": label,
        "classification": sum(runs[i]["result"]["classification"]["type"] == runs[i]["expected"]["type"] for i in ids),
        "drafts": sum(1 for r in res if r["draft"]),
        "blocked": [i for i in ids if runs[i]["result"].get("status") == "blocked_by_guardrail"],
        "unsupported": [(i, f) for i in ids if runs[i]["result"].get("fact_check")
                        for f in runs[i]["result"]["fact_check"]["unsupported"]],
        "calculated": [(i, f) for i in ids if runs[i]["result"].get("fact_check")
                       for f in runs[i]["result"]["fact_check"]["calculated"]],
        "grounded": f"{sup}/{checked} ({100 * sup / checked:.0f}%)" if checked else "n/a",
        "in_tokens": statistics.mean(r["usage"]["input_tokens"] for r in src) if src else 0,
        "out_tokens": statistics.mean(r["usage"]["output_tokens"] for r in src) if src else 0,
        "cost": statistics.mean(r["usage"]["cost_usd"] for r in src) if src else 0,
        "cost_total": sum(r["usage"]["cost_usd"] for r in res),
        "latency": statistics.median(r["latency_ms"] for r in src) if src else 0,
    }


a, b = summarise(rag, "RAG (top 5 passages)"), summarise(stuff, "Prompt-stuffing (all 33 documents)")

rows = [
    ("Emails compared", len(ids), len(ids)),
    ("Classification accuracy (unaffected by sources)", f"{a['classification']}/{len(ids)}", f"{b['classification']}/{len(ids)}"),
    ("Drafts produced", a["drafts"], b["drafts"]),
    ("**Facts in drafts found in a source (grounded)**", a["grounded"], b["grounded"]),
    ("Unsupported facts flagged", f"{len(a['unsupported'])} {a['unsupported']}", f"{len(b['unsupported'])} {b['unsupported']}"),
    ("Calculated amounts flagged", f"{len(a['calculated'])} {a['calculated']}", f"{len(b['calculated'])} {b['calculated']}"),
    ("Drafts blocked by guardrail (advice)", f"{len(a['blocked'])} {a['blocked']}", f"{len(b['blocked'])} {b['blocked']}"),
    ("**Avg input tokens per email** (emails that use sources)", f"{a['in_tokens']:,.0f}", f"{b['in_tokens']:,.0f}"),
    ("Avg output tokens per email", f"{a['out_tokens']:,.0f}", f"{b['out_tokens']:,.0f}"),
    ("**Avg cost per email** (emails that use sources)", f"${a['cost']:.5f}", f"${b['cost']:.5f}"),
    ("Total cost of the run (model calls)", f"${a['cost_total']:.4f}", f"${b['cost_total']:.4f}"),
    ("Median latency per email", f"{a['latency'] / 1000:.1f} s", f"{b['latency'] / 1000:.1f} s"),
]
table = "| Measure | RAG | Prompt-stuffing |\n|---|---|---|\n" + "\n".join(f"| {r[0]} | {r[1]} | {r[2]} |" for r in rows)

diffs = []
for i in ids:
    ra, rb = rag[i]["result"], stuff[i]["result"]
    ua = (ra.get("fact_check") or {}).get("unsupported", [])
    ub = (rb.get("fact_check") or {}).get("unsupported", [])
    if ra.get("status") != rb.get("status") or ua != ub:
        diffs.append(f"| {i} | {ra.get('status')} {ua or ''} | {rb.get('status')} {ub or ''} |")

ratio = b["in_tokens"] / a["in_tokens"] if a["in_tokens"] else 0
out = f"""# RAG vs prompt-stuffing (US-16)

The same 40 test emails, the same model (Nova 2 Lite, EU profile), and the same prompts, guardrail and fact check.
- **RAG:** each draft or briefing note gets the top 5 passages retrieved from the Bedrock Knowledge Base (S3 Vectors).
- **Prompt-stuffing:** each draft or briefing note gets all 33 knowledge-base documents (39,190 characters of text) in the prompt.

{table}

Prompt-stuffing sent **{ratio:.1f}× more input tokens** per email that uses sources.

## Emails where the outcome differed

| ID | RAG | Prompt-stuffing |
|---|---|---|
{chr(10).join(diffs) or '| - | - | - |'}

Costs use approximate Nova 2 Lite prices ($0.30 input and $2.50 output per million tokens). RAG's small retrieval and embedding cost is excluded.
"""
(ROOT / "eval" / "rag-vs-stuffing.md").write_text(out, encoding="utf-8")
print(out)
