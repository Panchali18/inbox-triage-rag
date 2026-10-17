"""US-15 AC4: RAGAS scores for the AI-written draft replies in the latest evaluation run.

Run in AWS CloudShell from the repo folder, after scripts/run_eval.py:
    pip install -q "ragas==0.2.15" "langchain-google-genai==2.1.5"
    python3 scripts/run_ragas.py      # asks for the Gemini key; typing is hidden and the key isn't saved

Judge model: Gemini (free tier), acceptable because every email and document is synthetic (scope assumption A7).
Metrics:
  - Faithfulness: the share of claims in the reply that the retrieved passages support (1.0 = every claim supported).
  - Context relevance: how relevant the retrieved passages are to the sender's email (0 to 1).
Writes eval/ragas.md and eval/results/ragas.json.
"""
import getpass
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
JUDGE = os.environ.get("RAGAS_MODEL", "gemini-3.8-flash")   # gemini-2.5-flash is closed to new API keys

if not os.environ.get("GOOGLE_API_KEY"):
    key = getpass.getpass("Paste your Gemini API key and press Enter (nothing will show while you paste): ").strip()
    if not key:
        sys.exit("No key entered. Run the script again.")
    os.environ["GOOGLE_API_KEY"] = key          # for this run only; never written to disk

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

PARTIAL = ROOT / "eval" / "results" / "ragas-partial.json"   # saved after every email, so a cut-off run can resume
done = {e["id"]: e for e in json.loads(PARTIAL.read_text(encoding="utf-8"))} if PARTIAL.exists() else {}
todo = [row for row in rows if row["id"] not in done]
print(f"Scoring {len(rows)} AI-written drafts with {JUDGE} ({len(done)} already done, {len(todo)} to go). "
      f"The free tier is slow; about a minute per email.")
judge = LangchainLLMWrapper(ChatGoogleGenerativeAI(model=JUDGE, temperature=0))
t0 = time.time()
num = lambda v: None if v is None or (isinstance(v, float) and math.isnan(v)) else float(v)
for i, row in enumerate(todo, 1):
    ds = EvaluationDataset.from_list([{k: v for k, v in row.items() if k != "id"}])
    s = evaluate(ds, metrics=[Faithfulness(), ContextRelevance()], llm=judge,
                 run_config=RunConfig(max_workers=1, max_retries=10, max_wait=90, timeout=240),
                 show_progress=False).to_pandas().iloc[0]
    done[row["id"]] = {"id": row["id"], "faithfulness": num(s.get("faithfulness")),
                       "context_relevance": num(s.get("nv_context_relevance", s.get("context_relevance")))}
    PARTIAL.parent.mkdir(parents=True, exist_ok=True)
    PARTIAL.write_text(json.dumps(list(done.values()), indent=2), encoding="utf-8")
    e = done[row["id"]]
    print(f"  {i}/{len(todo)}  {row['id']}  faithfulness {e['faithfulness']}  context relevance {e['context_relevance']}")

per_email = [done[row["id"]] for row in rows]


def avg(key):
    vals = [e[key] for e in per_email if e[key] is not None]
    return (statistics.mean(vals), len(vals)) if vals else (float("nan"), 0)


fmt = lambda v: "-" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{v:.2f}"
f_avg, f_n = avg("faithfulness")
c_avg, c_n = avg("context_relevance")
low = [e["id"] for e in per_email if e["faithfulness"] is not None and e["faithfulness"] < 0.8]
table = "\n".join(f"| {e['id']} | {fmt(e['faithfulness'])} | {fmt(e['context_relevance'])} |" for e in per_email)
report = f"""# RAGAS scores (US-15, AC4)

Judge: `{JUDGE}` (Gemini free tier; all data is synthetic). RAGAS 0.2.15. Drafts scored: {len(rows)} AI-written replies
from the latest evaluation run (templates are excluded, because they're fixed text). Last session's run time {(time.time() - t0) / 60:.0f} minutes.

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
PARTIAL.unlink()      # complete: the next run starts fresh
print("\n" + report)
