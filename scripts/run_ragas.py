"""US-15 AC4: RAGAS scores for the AI-written draft replies in the latest evaluation run.

Run in AWS CloudShell from the repo folder, after scripts/run_eval.py:
    pip install --user -q "ragas==0.2.15" "langchain-google-genai==2.1.5"
    read -s GOOGLE_API_KEY && export GOOGLE_API_KEY      # type the key; it isn't shown or saved
    python3 scripts/run_ragas.py

Judge model: Gemini (free tier), acceptable because every email and document is synthetic (scope assumption A7).
Metrics:
  - Faithfulness: the share of claims in the reply that the retrieved passages support (1.0 = every claim supported).
  - Context relevance: how relevant the retrieved passages are to the sender's email (0 to 1).
Writes eval/ragas.md and eval/results/ragas.json.
"""
import json
import math
import os
import statistics
import sys
import time
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from ragas import EvaluationDataset, RunConfig, evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import ContextRelevance, Faithfulness

ROOT = Path(__file__).resolve().parent.parent
JUDGE = os.environ.get("RAGAS_MODEL", "gemini-2.5-flash")

if not os.environ.get("GOOGLE_API_KEY"):
    sys.exit("Set GOOGLE_API_KEY first:  read -s GOOGLE_API_KEY && export GOOGLE_API_KEY")

results = json.loads((ROOT / "eval/results/latest.json").read_text(encoding="utf-8"))
rows = []
for x in results:
    r = x["result"]
    if "error" in r or r.get("action") != "draft reply" or not r.get("draft"):
        continue                                   # only AI-written replies (templates are fixed text)
    contexts = [p.get("text") for p in r.get("retrieved") or [] if p.get("text")]
    if not contexts:
        sys.exit("latest.json has no full passages. Re-run scripts/run_eval.py with the current code first.")
    rows.append({"id": x["id"], "user_input": f"Subject: {r.get('subject')}\n\n{r.get('body')}",
                 "response": r["draft"], "retrieved_contexts": contexts})

print(f"Scoring {len(rows)} AI-written drafts with {JUDGE}. The free tier is slow; expect 10-15 minutes.")
dataset = EvaluationDataset.from_list([{k: v for k, v in row.items() if k != "id"} for row in rows])
judge = LangchainLLMWrapper(ChatGoogleGenerativeAI(model=JUDGE, temperature=0))
t0 = time.time()
scores = evaluate(dataset, metrics=[Faithfulness(), ContextRelevance()], llm=judge,
                  run_config=RunConfig(max_workers=1, max_retries=10, max_wait=90, timeout=240),
                  show_progress=True).to_pandas()

per_email = []
for row, (_, s) in zip(rows, scores.iterrows()):
    per_email.append({"id": row["id"], "faithfulness": s.get("faithfulness"),
                      "context_relevance": s.get("nv_context_relevance", s.get("context_relevance"))})


def avg(key):
    vals = [e[key] for e in per_email if e[key] is not None and not math.isnan(e[key])]
    return (statistics.mean(vals), len(vals)) if vals else (float("nan"), 0)


fmt = lambda v: "-" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{v:.2f}"
f_avg, f_n = avg("faithfulness")
c_avg, c_n = avg("context_relevance")
low = [e["id"] for e in per_email if e["faithfulness"] is not None and not math.isnan(e["faithfulness"])
       and e["faithfulness"] < 0.8]
table = "\n".join(f"| {e['id']} | {fmt(e['faithfulness'])} | {fmt(e['context_relevance'])} |" for e in per_email)
report = f"""# RAGAS scores (US-15, AC4)

Judge: `{JUDGE}` (Gemini free tier; all data is synthetic). RAGAS 0.2.15. Drafts scored: {len(rows)} AI-written replies
from the latest evaluation run (templates are excluded, because they're fixed text). Run time {(time.time() - t0) / 60:.0f} minutes.

| Metric | Average | Drafts scored | What it measures |
|---|---|---|---|
| **Faithfulness** | **{fmt(f_avg)}** | {f_n} | Share of the reply's claims supported by the retrieved passages (1.00 = all supported) |
| **Context relevance** | **{fmt(c_avg)}** | {c_n} | How relevant the retrieved passages are to the sender's email (0 to 1) |

Drafts with faithfulness below 0.80: {", ".join(low) or "none"}.

## Per email

| ID | Faithfulness | Context relevance |
|---|---|---|
{table}

## How to read this

- RAGAS uses an AI judge, so the scores are estimates, and they can vary slightly between runs.
- Faithfulness counts general statements too (for example "we can help with your return"). A claim with no source,
  even a harmless one, lowers the score. Read low-scoring drafts before drawing conclusions.
- These scores complement the rule-based fact check, which checks every euro amount, percentage and date exactly.
"""
(ROOT / "eval" / "ragas.md").write_text(report, encoding="utf-8")
(ROOT / "eval" / "results" / "ragas.json").write_text(json.dumps(per_email, indent=2, default=str), encoding="utf-8")
print("\n" + report)
