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

---

## Day 2: Thursday 15 October 2026: synthetic knowledge base

### Done
- Named the fictional firm **Nore Valley Accountants** (Kilkenny). I chose it over my first idea, "Brennan & Kerr", because a search found a real Irish firm with a similar name (RBK, Russell Brennan Keane). All staff names are fictional too.
- Wrote four firm documents in `data/kb/firm/`: services and fees, engagement terms, onboarding and records checklists, and the FAQ.
- Designed the documents so they can be tested:
  - Checklist item codes (such as `ST-BANK`) let the system tell clients exactly what's missing.
  - The no-advice and partner-only ID check rules are written into the firm's own terms, so drafts can quote the policy, not just rely on the guardrail.
  - The FAQ gives no Revenue deadlines, so deadline questions must be answered from the Revenue pages. This tests retrieval across both sources.
  - The €120 partner consultation answers OQ-4: an unknown sender asking for advice is offered a paid consultation, and a partner gets a briefing note.

- Wrote 20 synthetic past replies in `data/kb/past-replies/`:
  - 6 prospect quotes and onboarding
  - 8 admin answers
  - 4 document logs and chases
  - 1 Revenue letter acknowledgement
  - 1 advice question redirected to a consultation
- Every fee, deadline and promise in the replies comes from the four firm documents, so the fact check has a consistent source of truth. No reply gives tax advice or states a Revenue deadline.

- Checked Revenue's reuse terms. The Public Sector Information Licence allows reuse under the CC BY 4.0 standard, on these conditions:
  - Credit Revenue with the exact attribution statement.
  - Use no logos.
  - Don't imply Revenue endorses the project.
  - Store no personal information.

  I added these to the scope (assumption A4), along with a rule: if no source answers a question, the draft says so and never guesses.
- Saved 9 revenue.ie pages as text in `data/kb/revenue/`. They cover self-assessment deadlines, preliminary tax, registration, VAT thresholds and Corporation Tax. Each file carries the attribution, the source URL and the date saved. I compared each file word by word with the PDF I'd saved.
- Left out allowable expenses on purpose, because Revenue covers them only in long technical manuals and expense questions go to an accountant.

### Learned
- Check that a fictional company name doesn't match a real business before publishing it.
- Synthetic data needs its own consistency check. One reply was dated after the deadline it asked the client to meet, and I had to correct it.
- Public sector content isn't automatically free to reuse. Check the licence first. Revenue's licence covers the text but not its logo, so I store the text only, not the PDFs.
- An AI web-reading tool can return summaries rather than exact text. For a knowledge base, save the source yourself and check the copy word by word.

### Next
- Create the client lookup data (about 12 fictional clients) for DynamoDB.
- Create the S3 bucket and Knowledge Base, and upload the documents. Don't upload the README files.
- Activate `Project` as a cost allocation tag after the first tagged resource exists.
