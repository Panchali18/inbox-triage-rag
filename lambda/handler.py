"""AWS Lambda handler for the inbox triage API (API Gateway REST, Lambda proxy integration).

Routes:
  GET    /emails                  list the queue (urgent first, then newest)
  POST   /emails                  submit a new email -> run the pipeline -> store and return the record
  GET    /emails/{id}             one record
  POST   /emails/{id}/decision    approve | edit | reject a draft (human review)
  GET    /test-emails             the 40 synthetic test emails, for the demo's "load example" picker
  OPTIONS *                       CORS preflight

Nothing is ever sent by email. An approved draft only changes status.
"""
import json
import os
import time
import uuid
from decimal import Decimal
from pathlib import Path

import boto3

from pipeline.triage import client_version, process_email

REGION = os.environ.get("AWS_REGION_NAME", "eu-north-1")
EMAILS_TABLE = os.environ.get("EMAILS_TABLE", "inbox-triage-v1-emails")
_emails = boto3.resource("dynamodb", region_name=REGION).Table(EMAILS_TABLE)
TEST_EMAILS = Path(__file__).resolve().parent / "data" / "test-emails" / "test_emails.json"

CORS = {"Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,x-api-key",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS"}
STATUS_ORDER = {"urgent_for_accountant": 0, "needs_human_triage": 1, "blocked_by_guardrail": 1,
                "for_accountant": 2, "awaiting_review": 3}


def _resp(code, body):
    return {"statusCode": code, "headers": {**CORS, "Content-Type": "application/json"},
            "body": json.dumps(body, ensure_ascii=False, default=_dec)}


def _dec(o):
    if isinstance(o, Decimal):
        return int(o) if o == int(o) else float(o)
    raise TypeError


def _to_ddb(obj):
    return json.loads(json.dumps(obj, default=str), parse_float=Decimal)


def _log(event, **kw):
    print(json.dumps({"event": event, **kw}, default=str))  # CloudWatch structured log, no email bodies


def handler(event, context):
    method = event.get("httpMethod", "GET")
    path = (event.get("path") or "/").rstrip("/") or "/"
    parts = [p for p in path.split("/") if p]
    if method == "OPTIONS":
        return {"statusCode": 204, "headers": CORS, "body": ""}
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _resp(400, {"error": "Body must be JSON"})

    try:
        if parts == ["test-emails"] and method == "GET":
            emails = json.loads(TEST_EMAILS.read_text(encoding="utf-8"))
            return _resp(200, [{k: e[k] for k in ("id", "from_email", "from_name", "subject", "body", "attachments")}
                               for e in emails])

        if parts == ["emails"] and method == "GET":
            items, kwargs = [], {}
            while True:
                page = _emails.scan(**kwargs)
                items += page["Items"]
                if "LastEvaluatedKey" not in page:
                    break
                kwargs["ExclusiveStartKey"] = page["LastEvaluatedKey"]
            items.sort(key=lambda r: (STATUS_ORDER.get(r.get("status"), 9), -(r.get("submitted_epoch") or 0)))
            return _resp(200, items)

        if parts == ["emails"] and method == "POST":
            if not body.get("from_email") or not (body.get("body") or body.get("subject")):
                return _resp(400, {"error": "from_email and body (or subject) are required"})
            email = {"id": str(uuid.uuid4()), "from_email": body["from_email"].strip().lower(),
                     "from_name": body.get("from_name", ""), "subject": body.get("subject", ""),
                     "body": body.get("body", ""), "attachments": body.get("attachments") or [],
                     "received_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
            rec = process_email(email, dry_run=False)
            rec["submitted_epoch"] = int(time.time())
            rec["history"] = [{"at": email["received_at"], "event": "triaged", "status": rec["status"]}]
            _emails.put_item(Item=_to_ddb(rec))
            c = rec["classification"]
            _log("triaged", email_id=rec["email_id"], type=c["type"], confidence=c.get("confidence"),
                 urgency=rec["urgency"], flags=rec["flags"], status=rec["status"], usage=rec["usage"],
                 latency_ms=rec["latency_ms"], retrieved=[p["source"] for p in rec["retrieved"]])
            return _resp(201, rec)

        if len(parts) == 2 and parts[0] == "emails" and method == "GET":
            item = _emails.get_item(Key={"email_id": parts[1]}).get("Item")
            return _resp(200, item) if item else _resp(404, {"error": "not found"})

        if len(parts) == 3 and parts[0] == "emails" and parts[2] == "decision" and method == "POST":
            item = _emails.get_item(Key={"email_id": parts[1]}).get("Item")
            if not item:
                return _resp(404, {"error": "not found"})
            decision = body.get("decision")
            if decision not in ("approve", "edit", "reject"):
                return _resp(400, {"error": "decision must be approve, edit or reject"})
            unsupported = ((item.get("fact_check") or {}).get("unsupported")) or []
            if decision == "approve" and unsupported and not body.get("override"):
                return _resp(409, {"error": "Draft has unsupported facts. Edit it, or approve with override=true.",
                                   "unsupported": unsupported})
            if decision == "reject" and not body.get("reason"):
                return _resp(400, {"error": "A reason is required to reject"})
            now = time.strftime("%Y-%m-%dT%H:%M:%S")
            status = {"approve": "approved (not sent - demo)", "edit": "approved (not sent - demo)",
                      "reject": "rejected"}[decision]
            update = {":s": status, ":h": [{"at": now, "event": decision, "status": status,
                                             "reason": body.get("reason"), "override": bool(body.get("override"))}]}
            expr = "SET #s = :s, history = list_append(if_not_exists(history, :empty), :h)"
            update[":empty"] = []
            final = item.get("draft")
            if decision == "edit":
                final = body.get("edited_draft", item.get("draft"))
                expr += ", draft = :d, edited = :t"
                update[":d"], update[":t"] = final, True
            if decision in ("approve", "edit"):
                expr += ", final_client_text = :f"   # what would be sent: no source tags
                update[":f"] = client_version(final)
            _emails.update_item(Key={"email_id": parts[1]}, UpdateExpression=expr,
                                ExpressionAttributeNames={"#s": "status"}, ExpressionAttributeValues=_to_ddb(update))
            _log("decision", email_id=parts[1], decision=decision, override=bool(body.get("override")))
            return _resp(200, _emails.get_item(Key={"email_id": parts[1]})["Item"])

        return _resp(404, {"error": f"No route for {method} {path}"})
    except Exception as ex:  # noqa: BLE001
        _log("error", error=repr(ex), path=path, method=method)
        return _resp(500, {"error": "Internal error", "detail": repr(ex)})
