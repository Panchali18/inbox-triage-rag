"""Run the pipeline on one or more test emails and print the result.

Run in AWS CloudShell from the repo folder:
    python3 scripts/run_one.py T01
    python3 scripts/run_one.py T16 T28 T40
Read-only: never writes to DynamoDB.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pipeline.triage import process_email  # noqa: E402

emails = {e["id"]: e for e in json.loads((ROOT / "data/test-emails/test_emails.json").read_text(encoding="utf-8"))}

for tid in sys.argv[1:] or ["T01"]:
    e = emails[tid]
    r = process_email(e, dry_run=True)
    c = r["classification"]
    print("=" * 78)
    print(f"{tid}  {e['from_name']}: {e['subject']}")
    print(f"  type      : {c['type']}  (expected {e['expected']['type']})  confidence {c.get('confidence')}")
    print(f"  urgency   : {r['urgency']}  (expected {e['expected']['urgency']})")
    print(f"  client    : {(r['client'] or {}).get('client_id')}  (expected {e['expected']['client_id']})")
    print(f"  flags     : {r['flags']}")
    print(f"  action    : {r['action']}  -> status {r['status']}")
    print(f"  routed to : {r['assigned_to']}  ({r.get('routing_reason')})")
    print(f"  retrieved : {[p['source'] for p in r['retrieved']]}")
    if r["checklist"]:
        print(f"  checklist : {r['checklist']}")
    if r["briefing_note"]:
        print("\n  --- briefing note ---\n" + r["briefing_note"])
    if r["draft"]:
        print("\n  --- draft ---\n" + r["draft"])
    if r["fact_check"]:
        print(f"\n  fact check: {r['fact_check']}")
    print(f"\n  usage     : {r['usage']}  latency {r['latency_ms']} ms")
