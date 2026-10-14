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
- Tested Bedrock: Nova 2 Lite replied in the playground in 2.6 seconds, using 97 input and 415 output tokens. So the account has a working model quota.
- **Changed the region from eu-west-1 (Ireland) to eu-north-1 (Stockholm).** The account sits inside an AWS project whose region is fixed to Stockholm. The console redirects there, and Unified Settings and Default Region are blocked. Creating a new project doesn't offer a region choice either.

### Learned
- In Stockholm, S3 Vectors and Titan Text Embeddings V2 are available, and Bedrock Knowledge Bases and Guardrails appear in the console menu. Knowledge Bases with structured data stores aren't available there, but this project doesn't need them.
- Some free-plan accounts get Bedrock quotas of zero, so a model call has to be tested before building on it.
- Nova 2 Lite runs with reasoning switched on by default in the playground. That adds output tokens and latency, so I'll turn it off for classification and extraction.
- Billing pages are global, so the region selector is hidden there.
- AWS "projects" (a newer, limited-release setup) can lock an account to one region. Check the project page under Additional info before planning around a specific region.
- Cost Explorer needs about 24 hours to fill in. The Free Tier page shows the credit balance straight away.
- On the free plan, every service stops when the credits run out, including other live apps on the account. The budget alert is the early warning.

- Step one account checks all passed in eu-north-1. I created and deleted a test resource in each service:
  - Titan Text Embeddings V2: listed as serverless.
  - S3 Vectors: created and deleted a vector bucket.
  - Lambda: ran a hello-world function on Python and arm64.
  - API Gateway: an HTTP API trigger returned "Hello from Lambda!".
  - DynamoDB: a test table reached Active, then I deleted it.
- Tagging convention agreed. Every resource is named with the prefix `inbox-triage-v1-` and carries these tags: `Project=inbox-triage-v1`, `Owner=panchali`, `Env=demo`, `DeleteAfter=2027-04-10`.

### Learned (account checks)
- Claude models aren't in the Stockholm model catalogue, so Nova is the native option here.
- A cost allocation tag can only be activated after a resource carries it, so I'll activate `Project` once the first real resource exists.

### Next
- Draft the synthetic knowledge base: firm documents, 20 past replies and the Revenue.ie page selection.
- Activate `Project` as a cost allocation tag after the first tagged resource exists.
