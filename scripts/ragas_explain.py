"""Show how RAGAS faithfulness is worked out, statement by statement, for a few emails.

Runs each email twice:
  1. "documents only": RAGAS sees just the retrieved documents (the first, flawed setup)
  2. "full context":   it also sees the sender's email, the client record and the firm's details (the fix)

Run in AWS CloudShell from the repo folder, after scripts/run_eval.py has produced eval/results/latest.json:
    pip install -q "ragas==0.2.15" "langchain-aws==0.2.30"
    python3 scripts/ragas_explain.py T01 T11
Writes eval/results/ragas-explain.md. Read-only: changes nothing in the app.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

from langchain_aws import ChatBedrockConverse
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import Faithfulness

ROOT = Path(__file__).resolve().parent.parent
JUDGE = os.environ.get("RAGAS_MODEL", "eu.amazon.nova-pro-v1:0")
REGION = os.environ.get("AWS_REGION_NAME", "eu-north-1")
ids = sys.argv[1:] or ["T01", "T11"]

results = {x["id"]: x["result"] for x in json.loads((ROOT / "eval/results/latest.json").read_text(encoding="utf-8"))}
metric = Faithfulness(llm=LangchainLLMWrapper(ChatBedrockConverse(model=JUDGE, region_name=REGION, temperature=0,
                                                                  max_tokens=4000)))


def contexts(r, full):
    docs = [p.get("text") for p in r.get("retrieved") or [] if p.get("text")]
    if not full:
        return docs
    c = r.get("client")
    record = ("Client record: " + json.dumps({k: c.get(k) for k in ("name", "client_type", "business_name", "services",
              "assigned_accountant", "partner", "onboarding_status", "outstanding")}, ensure_ascii=False)
              if c else "The sender is not in the client table (unknown sender / prospect).")
    firm = "Firm: Nore Valley Accountants, Kilkenny. Practice manager: Sinéad Kehoe (signs replies)."
    sender = f"The sender's email. From: {r.get('from_name')}. Subject: {r.get('subject')}. {r.get('body')}"
    return docs + [record, firm, sender]


async def explain(email_id, full):
    r = results[email_id]
    row = {"user_input": f"Subject: {r.get('subject')}\n\n{r.get('body')}", "response": r["draft"],
           "retrieved_contexts": contexts(r, full)}
    statements = (await metric._create_statements(row, None)).statements
    verdicts = (await metric._create_verdicts(row, statements, None)).statements
    supported = sum(1 for v in verdicts if v.verdict)
    return verdicts, supported, len(verdicts)


async def main():
    out = [f"# How the faithfulness score is worked out\n\nChecker model: `{JUDGE}`. "
           "Score = supported statements ÷ all statements.\n"]
    for email_id in ids:
        r = results.get(email_id)
        if not r or not r.get("draft") or not any(p.get("text") for p in r.get("retrieved") or []):
            print(f"{email_id}: no AI-written draft with sources in latest.json, skipped")
            continue
        print("=" * 78 + f"\n{email_id}  {r.get('from_name')}: {r.get('subject')}\n\nTHE REPLY BEING CHECKED:\n{r['draft']}\n")
        out.append(f"\n## {email_id}: {r.get('from_name')}, \"{r.get('subject')}\"\n\n```\n{r['draft']}\n```\n")
        for full, label in ((False, "DOCUMENTS ONLY (first setup)"), (True, "FULL CONTEXT (the fix)")):
            verdicts, ok, n = await explain(email_id, full)
            score = f"{ok}/{n} = {ok / n:.2f}" if n else "no statements"
            print(f"--- {label}: score {score}")
            out.append(f"\n### {label}: {score}\n\n| | Statement | Reason |\n|---|---|---|")
            for v in verdicts:
                mark = "✓" if v.verdict else "✗"
                print(f"  {mark} {v.statement}\n      why: {v.reason}")
                out.append(f"| {mark} | {v.statement} | {v.reason} |")
            print()
    (ROOT / "eval" / "results" / "ragas-explain.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("Saved to eval/results/ragas-explain.md")


asyncio.run(main())
