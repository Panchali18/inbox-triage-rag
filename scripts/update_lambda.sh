#!/usr/bin/env bash
# Push new pipeline/handler code to the existing Lambda. Run in CloudShell after `git pull`:
#     bash scripts/update_lambda.sh
# Optional: pass environment changes, e.g.  GUARDRAIL_ID=abc123 bash scripts/update_lambda.sh
set -euo pipefail
export AWS_PAGER=""
REGION=eu-north-1
bash scripts/package_lambda.sh
aws lambda update-function-code --function-name inbox-triage-v1-api --region $REGION \
  --zip-file fileb:///tmp/inbox-triage-v1-lambda.zip >/dev/null
aws lambda wait function-updated-v2 --function-name inbox-triage-v1-api --region $REGION
if [ -n "${GUARDRAIL_ID:-}" ]; then
  VARS=$(aws lambda get-function-configuration --function-name inbox-triage-v1-api --region $REGION \
    --query Environment.Variables --output json)
  NEW=$(python3 -c "import json,sys;v=json.loads(sys.argv[1]);v['GUARDRAIL_ID']=sys.argv[2];v['GUARDRAIL_VERSION']=sys.argv[3];print(json.dumps({'Variables':v}))" \
    "$VARS" "$GUARDRAIL_ID" "${GUARDRAIL_VERSION:-DRAFT}")
  aws lambda update-function-configuration --function-name inbox-triage-v1-api --region $REGION --environment "$NEW" >/dev/null
  aws lambda wait function-updated-v2 --function-name inbox-triage-v1-api --region $REGION
  echo "     guardrail $GUARDRAIL_ID set"
fi
echo "Lambda updated."
