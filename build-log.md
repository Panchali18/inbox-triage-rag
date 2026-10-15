# Build log

What I built at each step, the decisions I made and why, and what I learned along the way.

---

## Decisions at a glance

| Area | Choice | Why | Alternative I didn't choose |
|---|---|---|---|
| Region | eu-north-1 (Stockholm) | The AWS project is locked to Stockholm. Data still stays in the EU, which is what GDPR cares about. | eu-west-1 (Ireland): blocked by the project settings |
| Vector store | Amazon S3 Vectors | Pay-per-use storage and queries, so it costs pennies at this scale | OpenSearch Serverless: a minimum always-on charge that would use up the free credits in weeks |
| Embeddings | Titan Text Embeddings V2, float, 1024 dimensions | Available in Stockholm and supported by S3 Vectors. The default size gives the best accuracy. | Binary embeddings: cheaper storage, but less precise, and storage cost is already negligible |
| Parsing | Bedrock default parser | Free, and enough for plain-text Markdown | Foundation-model parser: charges per page, and only needed for images and complex layouts |
| Chunking | Default (about 300 tokens) | Most files are short, so they stay whole. The fee guide and terms split into a few chunks. | Hierarchical or semantic chunking: worth testing in v2 if retrieval scores are weak |
| Main model | Amazon Nova 2 Lite | Native in Stockholm, cheap and fast. Claude isn't in the Stockholm catalogue. | A small Claude model via EU cross-region inference: kept as a backup |
| Client lookup | DynamoDB table, called as a tool | Structured facts (who is the client, what's outstanding) need exact lookups, not similarity search. DynamoDB also appears in AI job posts. | A JSON file in S3: simpler but less realistic |
| Front-end access | API Gateway with an API key and throttling | Enough for a demo, with less setup | Cognito login: more realistic, but adds a week-2 dependency |
| Budget | $5 a month alert on the whole account | FitProof costs about $1.30 a month, so $5 gives an early warning | $10: too late a warning on a $119 credit balance |
| Demo lifetime | Live until 10 April 2027 | The LinkedIn post links to a working demo. Idle cost is close to zero. | Delete at the 6 November close date: the demo link would break days after posting |
| Firm name | Nore Valley Accountants (fictional) | First idea, "Brennan & Kerr", was too close to a real firm (RBK) | |
| Revenue content | 9 pages saved as text, with CC BY 4.0 attribution | Revenue's licence allows reuse with credit, but not its logos | Storing the PDFs: they contain the Revenue logo |
| Expenses guidance | Left out | Only available in long technical manuals. Expense questions are advice, so they go to an accountant. | |

---

## Day 1: Wednesday 14 October 2026: scope and account checks

### Done
- Wrote the v1 scope as 17 user stories with acceptance criteria, assumptions and open questions ([scope.md](scope.md)).
- Checked the account: free plan with $119.41 credits and 179 days left. Current spend is about $1.30 a month, mainly FitProof.
- Created a monthly cost budget, `account-monthly-5usd`. It alerts at 85% and 100% of actual spend, and at 100% of forecast spend.
- Tested Bedrock: Nova 2 Lite replied in the playground in 2.6 seconds, using 97 input and 415 output tokens.
- Ran the account checks in eu-north-1. I created a test resource in each service, then deleted it:
  - Titan Text Embeddings V2: listed as serverless.
  - S3 Vectors: created and deleted a vector bucket.
  - Lambda: ran a hello-world function on Python and arm64.
  - API Gateway: an HTTP API trigger returned "Hello from Lambda!".
  - DynamoDB: a test table reached Active, then I deleted it.
- Agreed a tagging convention. Every resource is named with the prefix `inbox-triage-v1-` and carries these tags:
  - `Project = inbox-triage-v1`: find all project resources and separate their costs.
  - `Owner = panchali`: who is responsible.
  - `Env = demo`: keeps demo resources apart from the live FitProof app.
  - `DeleteAfter = 2027-04-10`: the clean-up date, so nothing is forgotten.
- Created this repo.

### Decided
- **Changed the region from Ireland to Stockholm.** The account sits inside an AWS "project" whose region is fixed to Stockholm. The console redirects there, and Unified Settings and Default Region are blocked. Creating a new project doesn't offer a region choice either. Every service the build needs is available in Stockholm, and data stays in the EU.

### Learned
- Test a model call before building on Bedrock. Some free-plan accounts get model quotas of zero.
- Nova 2 Lite has reasoning switched on by default in the playground. That adds output tokens and latency, so I'll turn it off for classification and extraction.
- Billing pages are global, so the region selector is hidden there.
- AWS projects, a newer limited-release setup, can lock an account to one region. Check the project's region before planning around one.
- Cost Explorer needs about 24 hours to fill in. The Free Tier page shows the credit balance straight away.
- On the free plan, every service stops when the credits run out, including other live apps on the account. The budget alert is the early warning.
- Claude models aren't in the Stockholm model catalogue. Nova is the native option there.
- Hosting in another EU region doesn't change GDPR for an Irish firm, because data stays within the EU. A real deployment would still need a data processing agreement, a privacy notice and a DPIA, and should check client contracts for any Ireland-only requirement.

---

## Day 2: Thursday 15 October 2026: synthetic data and the Knowledge Base

### Done: firm documents
- Wrote four documents for the fictional firm in `data/kb/firm/`:
  - services and fees
  - engagement terms
  - onboarding and annual records checklists
  - FAQ
- Designed them so the pipeline can be tested:
  - **Checklist item codes** (such as `ST-BANK`) let the system match a file to a checklist item and tell the client exactly what's still missing.
  - **The no-advice and partner-only identity check rules are written into the firm's own terms.** Drafts can quote the firm's policy when declining advice, as a second layer behind the guardrail.
  - **The FAQ gives no Revenue deadlines.** Deadline questions must be answered from the Revenue pages, which tests retrieval across both sources.
  - **A €120 partner consultation** answers OQ-4: an unknown sender asking for advice is offered a paid consultation, and a partner gets a briefing note.

### Done: past replies
- Wrote 20 synthetic past replies in `data/kb/past-replies/`:
  - 6 prospect quotes and onboarding
  - 8 admin answers
  - 4 document logs and chases
  - 1 Revenue letter acknowledgement
  - 1 advice question redirected to a consultation
- Every fee, deadline and promise in the replies comes from the four firm documents, so the fact check has one consistent source of truth. No reply gives tax advice or states a Revenue deadline.

### Done: Revenue guidance
- Checked Revenue's reuse terms. Its Public Sector Information Licence allows reuse under the CC BY 4.0 standard, on these conditions:
  - credit Revenue with its exact attribution statement
  - use no logos
  - don't imply Revenue endorses the project
  - store no personal information
- Added these to the scope (assumption A4). Also added a rule: if no source answers a question, the draft says so and points to revenue.ie or offers a call. It never guesses. Any Revenue fact in a draft cites its page and save date.
- Saved 9 revenue.ie pages as text in `data/kb/revenue/`. They cover self-assessment deadlines, preliminary tax, registration, VAT thresholds and Corporation Tax. Each file carries the attribution, the source URL and the date saved. I compared each file word by word against the PDF I'd saved.

### Done: client table
- Created 15 fictional clients in `data/clients/clients.json`: 13 sole traders and 2 companies.
  - Names reflect a realistic mix of people in Ireland, about half Irish and half from other backgrounds. I renamed 10 people in the past replies to match, so replies and client records stay consistent.
  - Six clients have outstanding documents, to test the documents step. One is mid-onboarding, to test that the system never says identity is verified.
  - Emails use the reserved `example.com` domain.

### Done: AWS
- Created the S3 bucket `inbox-triage-v1-kb-docs-pd` (private, tagged) and uploaded 33 files: 4 firm documents, 20 past replies and 9 Revenue pages. I removed the Revenue folder README so the knowledge base doesn't treat it as guidance.
- Created the Knowledge Base `inbox-triage-v1-kb` with these settings:
  - data source `inbox-triage-v1-kb-docs`
  - Titan Text Embeddings V2
  - S3 Vectors, quick create
  - default parsing and chunking
  - deletion policy DELETE
- First sync completed.
- **Tested retrieval in the console, and found a data design problem.** Every file started with the same "Synthetic data" banner or Revenue credit line, followed by a header table. The search results were dominated by this repeated boilerplate:
  - "How much does a tax return cost?" did find the right files (the carpenter quote and the fee guide), but the passages shown were mostly banner text.
  - "When is the self-assessment return due?" returned three Revenue passages that all showed only the identical credit line.
- **Fix:** added `scripts/build_kb_upload.py`. It builds a clean `kb-upload/` folder with the text only, and moves the labels into a `.metadata.json` file next to each document. The labels are source type, category, date, and for Revenue pages the URL, credit line and save date. Past replies keep the client's question as text, because it helps match new emails to similar past ones. The GitHub copies in `data/kb/` keep their banners and attribution for human readers.

### Decided
- **Global bucket namespace,** not the newer account-regional namespace, because I couldn't confirm that Bedrock Knowledge Bases support the new option yet.
- **Cost allocation tags aren't available on the free plan.** Cost per email will be calculated from the token counts logged by Lambda (US-14). That's more precise than tag-based billing anyway.

### Learned
- Check that a fictional company name doesn't match a real business before publishing it.
- Synthetic data needs its own consistency check. One reply was dated after the deadline it asked the client to meet, and I had to correct it.
- Synthetic clients should reflect the real customer base, not a stereotype.
- Public sector content isn't automatically free to reuse. Check the licence first. Revenue's licence covers the text but not its logo.
- An AI web-reading tool can return summaries rather than exact text. For a knowledge base, save the source yourself and check the copy word by word.
- The console's "Quick create" text says it creates OpenSearch Serverless, even after S3 Vectors is selected in the dropdown below. Always confirm the vector store on the review page before creating.
- **Boilerplate hurts retrieval.** Text repeated across many documents, such as disclaimers, licence lines and header tables, gets embedded with every chunk. It makes different documents look similar and fills the results with noise. Keep chunk text to real content and put labels in metadata. Metadata also lets you filter searches, for example only Revenue pages for a deadline question.
- "Retrieval only" testing shows raw passages, not answers. It's the right way to check search quality before a model is added on top.
- RAG and lookup do different jobs. RAG finds relevant passages in documents. Lookup returns exact facts about a client. Mixing them up leads to wrong answers about who someone is or what they owe.

- Replaced the bucket contents with the 66 files from `kb-upload/` (33 documents and 33 metadata files) and re-synced.
- **Retrieval tests after the fix (top 5, retrieval only):**

  | Question | Result |
  |---|---|
  | How much does a sole trader tax return cost? | Carpenter quote #1, fee guide #2, landlord quote #4 |
  | When is the self-assessment tax return due? | Revenue "Pay and file system" #2 (31 Oct / 18 Nov). #1 is a related Revenue page. Not top-ranked, but within the top 5 that drafting will use. |
  | Do you need my ROS password? | Past reply to Fiona #1, FAQ in the top 5 |

- **First end-to-end answer** (retrieval with answer generation, using the EU Nova 2 Lite inference profile). Asked "I'm a carpenter just starting out, how much would you charge for my tax return?", it answered from €450, or from €750 with bookkeeping, excluding VAT, and offered the free 20-minute discovery call. Every figure had a citation, and every figure matched the fee guide.

### Learned (testing)
- Retrieval alone shows the evidence. Generation turns it into an answer. Test retrieval first: if the evidence is wrong, the answer will be wrong however good the model is.
- Past replies act as worked examples. Keeping the client's question in each one helps a new email match a similar past email.
- The console answer reads like a chatbot ("Based on the information provided…"). The Lambda prompt will need to shape it into an email from the firm.

- Rewrote the repo README with the problem, design, architecture (built vs planned), repo layout, data and licence notes, GDPR note, cost controls, an AWS clean-up list and limitations. Added a progress table to the scope.

### Next
- Load the client table into DynamoDB.
- Write the 40 synthetic test emails.
