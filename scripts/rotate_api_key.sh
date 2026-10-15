#!/usr/bin/env bash
# Replace the API key: create a new key on the same usage plan, then delete the old one(s).
# Run in CloudShell from the repo folder:  bash scripts/rotate_api_key.sh
# Afterwards, update the key wherever it's stored (the Lovable server-side secret).
set -euo pipefail
export AWS_PAGER=""
REGION=eu-north-1
P=inbox-triage-v1
TAGS_KV="Project=$P,Owner=panchali,Env=demo,DeleteAfter=2027-04-10"
PLAN_ID=$(aws apigateway get-usage-plans --region $REGION --query "items[?name=='$P-plan'].id | [0]" --output text)
OLD_IDS=$(aws apigateway get-api-keys --region $REGION --name-query $P-key --query "items[].id" --output text)
NAME=$P-key-$(date +%Y%m%d%H%M)
NEW_ID=$(aws apigateway create-api-key --region $REGION --name $NAME --enabled --tags "$TAGS_KV" --query id --output text)
aws apigateway create-usage-plan-key --region $REGION --usage-plan-id $PLAN_ID --key-id $NEW_ID --key-type API_KEY >/dev/null
for ID in $OLD_IDS; do
  aws apigateway delete-api-key --region $REGION --api-key $ID
  echo "Deleted old key $ID"
done
VALUE=$(aws apigateway get-api-key --region $REGION --api-key $NEW_ID --include-value --query value --output text)
echo
echo "New API key: $VALUE"
echo "Paste it only into Lovable's secure secret form. It can take up to a minute to start working."
