#!/usr/bin/env bash
# One-time deployment of the inbox triage API. Run in AWS CloudShell from the repo folder:
#     bash scripts/deploy.sh
# Creates: DynamoDB emails table, IAM role, Lambda function, REST API with API key and usage plan.
# To update only the Lambda code later:  bash scripts/update_lambda.sh
set -euo pipefail
export AWS_PAGER=""
REGION=eu-north-1
P=inbox-triage-v1
KB_ID=Z68WKOF2FB
MODEL_ID=eu.amazon.nova-2-lite-v1:0
TAGS_KV="Project=$P,Owner=panchali,Env=demo,DeleteAfter=2027-04-10"
TAGS_LIST="Key=Project,Value=$P Key=Owner,Value=panchali Key=Env,Value=demo Key=DeleteAfter,Value=2027-04-10"
ACCT=$(aws sts get-caller-identity --query Account --output text)
echo "Account $ACCT, region $REGION"

echo "1/6  DynamoDB table $P-emails"
if ! aws dynamodb describe-table --table-name $P-emails --region $REGION >/dev/null 2>&1; then
  aws dynamodb create-table --table-name $P-emails --region $REGION \
    --attribute-definitions AttributeName=email_id,AttributeType=S \
    --key-schema AttributeName=email_id,KeyType=HASH --billing-mode PAY_PER_REQUEST \
    --tags $TAGS_LIST >/dev/null
  aws dynamodb wait table-exists --table-name $P-emails --region $REGION
fi

echo "2/6  IAM role $P-lambda-role"
if ! aws iam get-role --role-name $P-lambda-role >/dev/null 2>&1; then
  aws iam create-role --role-name $P-lambda-role --tags $TAGS_LIST \
    --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}' >/dev/null
  aws iam attach-role-policy --role-name $P-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
  CREATED_ROLE=1
fi
cat > /tmp/$P-policy.json <<EOF
{"Version":"2012-10-17","Statement":[
 {"Sid":"Model","Effect":"Allow","Action":["bedrock:InvokeModel"],
  "Resource":["arn:aws:bedrock:$REGION:$ACCT:inference-profile/$MODEL_ID",
              "arn:aws:bedrock:*::foundation-model/amazon.nova-2-lite-v1:0"]},
 {"Sid":"KnowledgeBase","Effect":"Allow","Action":["bedrock:Retrieve"],
  "Resource":"arn:aws:bedrock:$REGION:$ACCT:knowledge-base/$KB_ID"},
 {"Sid":"Guardrail","Effect":"Allow","Action":["bedrock:ApplyGuardrail"],
  "Resource":"arn:aws:bedrock:$REGION:$ACCT:guardrail/*"},
 {"Sid":"Tables","Effect":"Allow","Action":["dynamodb:GetItem","dynamodb:PutItem","dynamodb:UpdateItem","dynamodb:Scan"],
  "Resource":["arn:aws:dynamodb:$REGION:$ACCT:table/$P-emails","arn:aws:dynamodb:$REGION:$ACCT:table/$P-clients"]}]}
EOF
aws iam put-role-policy --role-name $P-lambda-role --policy-name $P-access --policy-document file:///tmp/$P-policy.json
ROLE_ARN=arn:aws:iam::$ACCT:role/$P-lambda-role
if [ "${CREATED_ROLE:-0}" = 1 ]; then echo "     waiting 15s for the new role to be usable"; sleep 15; fi

echo "3/6  Package and create Lambda $P-api"
bash scripts/package_lambda.sh
if ! aws lambda get-function --function-name $P-api --region $REGION >/dev/null 2>&1; then
  aws lambda create-function --function-name $P-api --region $REGION --runtime python3.12 --architectures arm64 \
    --role $ROLE_ARN --handler handler.handler --zip-file fileb:///tmp/$P-lambda.zip \
    --timeout 60 --memory-size 512 --tags "$TAGS_KV" \
    --environment "Variables={AWS_REGION_NAME=$REGION,KB_ID=$KB_ID,MODEL_ID=$MODEL_ID,CLIENTS_TABLE=$P-clients,EMAILS_TABLE=$P-emails}" >/dev/null
  aws lambda wait function-active-v2 --function-name $P-api --region $REGION
else
  aws lambda update-function-code --function-name $P-api --region $REGION --zip-file fileb:///tmp/$P-lambda.zip >/dev/null
fi
FN_ARN=arn:aws:lambda:$REGION:$ACCT:function:$P-api

echo "4/6  REST API $P-api"
API_ID=$(aws apigateway get-rest-apis --region $REGION --query "items[?name=='$P-api'].id | [0]" --output text)
if [ "$API_ID" = "None" ] || [ -z "$API_ID" ]; then
  API_ID=$(aws apigateway create-rest-api --region $REGION --name $P-api --endpoint-configuration types=REGIONAL \
    --tags "$TAGS_KV" --query id --output text)
  ROOT_ID=$(aws apigateway get-resources --region $REGION --rest-api-id $API_ID --query "items[?path=='/'].id" --output text)
  RES_ID=$(aws apigateway create-resource --region $REGION --rest-api-id $API_ID --parent-id $ROOT_ID \
    --path-part '{proxy+}' --query id --output text)
  URI=arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$FN_ARN/invocations
  # ANY requires the API key; OPTIONS (CORS preflight) does not, because browsers never send keys on preflight.
  aws apigateway put-method --region $REGION --rest-api-id $API_ID --resource-id $RES_ID --http-method ANY \
    --authorization-type NONE --api-key-required >/dev/null
  aws apigateway put-integration --region $REGION --rest-api-id $API_ID --resource-id $RES_ID --http-method ANY \
    --type AWS_PROXY --integration-http-method POST --uri $URI >/dev/null
  aws apigateway put-method --region $REGION --rest-api-id $API_ID --resource-id $RES_ID --http-method OPTIONS \
    --authorization-type NONE --no-api-key-required >/dev/null
  aws apigateway put-integration --region $REGION --rest-api-id $API_ID --resource-id $RES_ID --http-method OPTIONS \
    --type AWS_PROXY --integration-http-method POST --uri $URI >/dev/null
  for T in DEFAULT_4XX DEFAULT_5XX; do
    aws apigateway put-gateway-response --region $REGION --rest-api-id $API_ID --response-type $T \
      --response-parameters '{"gatewayresponse.header.Access-Control-Allow-Origin":"'"'"'*'"'"'","gatewayresponse.header.Access-Control-Allow-Headers":"'"'"'Content-Type,x-api-key'"'"'"}' >/dev/null
  done
  aws lambda add-permission --region $REGION --function-name $P-api --statement-id apigateway-invoke \
    --action lambda:InvokeFunction --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$REGION:$ACCT:$API_ID/*/*/*" >/dev/null
fi
aws apigateway create-deployment --region $REGION --rest-api-id $API_ID --stage-name prod >/dev/null

echo "5/6  Usage plan and API key (2 requests/second, 300 requests/day)"
PLAN_ID=$(aws apigateway get-usage-plans --region $REGION --query "items[?name=='$P-plan'].id | [0]" --output text)
if [ "$PLAN_ID" = "None" ] || [ -z "$PLAN_ID" ]; then
  PLAN_ID=$(aws apigateway create-usage-plan --region $REGION --name $P-plan --tags "$TAGS_KV" \
    --api-stages apiId=$API_ID,stage=prod --throttle burstLimit=5,rateLimit=2 --quota limit=300,period=DAY \
    --query id --output text)
  KEY_ID=$(aws apigateway create-api-key --region $REGION --name $P-key --enabled --tags "$TAGS_KV" --query id --output text)
  aws apigateway create-usage-plan-key --region $REGION --usage-plan-id $PLAN_ID --key-id $KEY_ID --key-type API_KEY >/dev/null
fi
KEY_ID=$(aws apigateway get-api-keys --region $REGION --name-query $P-key --query "items[-1].id" --output text)
KEY_VALUE=$(aws apigateway get-api-key --region $REGION --api-key $KEY_ID --include-value --query value --output text)

echo "6/6  Done"
URL=https://$API_ID.execute-api.$REGION.amazonaws.com/prod
echo
echo "API URL : $URL"
echo "API key : $KEY_VALUE"
echo
echo "Quick test:"
echo "curl -s -H 'x-api-key: $KEY_VALUE' $URL/test-emails | head -c 300; echo"
