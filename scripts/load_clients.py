"""Load the synthetic clients into DynamoDB.

Run in AWS CloudShell (eu-north-1) from the repo folder:
    python3 scripts/load_clients.py

The table must already exist: inbox-triage-v1-clients, partition key `email` (String).
Running the script again overwrites the same 15 items. It doesn't create duplicates.
"""
import json
from pathlib import Path

import boto3

REGION = "eu-north-1"
TABLE = "inbox-triage-v1-clients"
DATA = Path(__file__).resolve().parent.parent / "data" / "clients" / "clients.json"

clients = json.loads(DATA.read_text(encoding="utf-8"))
table = boto3.resource("dynamodb", region_name=REGION).Table(TABLE)

with table.batch_writer() as batch:
    for c in clients:
        batch.put_item(Item=c)
        print(f"  loaded {c['client_id']}  {c['name']}  <{c['email']}>")

count = table.scan(Select="COUNT")["Count"]
print(f"\nDone. {len(clients)} clients in the file, {count} items now in {TABLE}.")
