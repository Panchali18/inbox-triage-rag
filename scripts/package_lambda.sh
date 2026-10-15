#!/usr/bin/env bash
# Build /tmp/inbox-triage-v1-lambda.zip: handler + pipeline + test emails (boto3 is already in the Lambda runtime).
set -euo pipefail
B=/tmp/inbox-triage-v1-build
rm -rf $B /tmp/inbox-triage-v1-lambda.zip && mkdir -p $B/data/test-emails
cp lambda/handler.py $B/
cp -r pipeline $B/
cp data/test-emails/test_emails.json $B/data/test-emails/
find $B -name "__pycache__" -prune -exec rm -rf {} +
(cd $B && zip -qr /tmp/inbox-triage-v1-lambda.zip .)
echo "     packaged $(du -h /tmp/inbox-triage-v1-lambda.zip | cut -f1)"
