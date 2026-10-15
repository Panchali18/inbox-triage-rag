#!/usr/bin/env bash
# Reset the demo: delete every triaged email and restore the 15 clients' checklists.
# Run in CloudShell from the repo folder:  bash scripts/reset_demo.sh
set -euo pipefail
export AWS_PAGER=""
REGION=eu-north-1
TABLE=inbox-triage-v1-emails
IDS=$(aws dynamodb scan --table-name $TABLE --region $REGION --projection-expression email_id \
      --query "Items[].email_id.S" --output text)
N=0
for ID in $IDS; do
  aws dynamodb delete-item --table-name $TABLE --region $REGION --key "{\"email_id\":{\"S\":\"$ID\"}}"
  N=$((N+1))
done
echo "Deleted $N emails from $TABLE"
python3 scripts/load_clients.py | tail -1
