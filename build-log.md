# Build log

What I did at each step, what I decided, and what I learned.

---

## Day 1: Wednesday 14 October 2026: scope and account checks

### Done
- Wrote the v1 scope as 17 user stories with acceptance criteria, assumptions and open questions ([scope.md](scope.md)).
- Decided:
  - DynamoDB for the client lookup.
  - An API key for front-end access.
  - EU cross-region inference is acceptable.
  - 20 past replies instead of 50.
  - The demo stays live until 10 April 2027.
- Checked the account: free plan with $119.41 credits and 179 days left. Current spend is about $1.30 a month, mainly FitProof.
- Created a monthly cost budget, `account-monthly-5usd`. It alerts at 85% and 100% of actual spend, and at 100% of forecast spend.
- Created this repo.

### Learned
- S3 Vectors and Bedrock Knowledge Bases are both available in eu-west-1.
- Some free-plan accounts get Bedrock quotas of zero, so a model call has to be tested before building on it.
- Billing pages are global, so the region selector is hidden there.
- Cost Explorer needs about 24 hours to fill in. The Free Tier page shows the credit balance straight away.
- On the free plan, every service stops when the credits run out, including other live apps on the account. The budget alert is the early warning.

### Next
- Test a Bedrock model (Nova Lite) in Ireland and confirm Titan Text Embeddings V2 is available.
- Test S3 Vectors, Lambda, API Gateway and DynamoDB.
- Apply the tagging convention: `Project=inbox-triage-v1`, `Owner=panchali`, `Env=demo`, `DeleteAfter=2027-04-10`.
