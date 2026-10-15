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

- Created the DynamoDB table `inbox-triage-v1-clients`: partition key `email` (String), on-demand capacity, tagged. Loaded all 15 clients from AWS CloudShell with `scripts/load_clients.py`, which confirmed 15 items in the table.

### Decided (client table)
- **Partition key is the email address,** because the pipeline's first question is "who sent this?" and an email is what it has. One exact read, with no search needed.
- **On-demand capacity** rather than provisioned. We pay per request, which is fractions of a cent at demo volume, and there's nothing to size.
- **Loaded by script from CloudShell,** not typed into the console. The script is in the repo, so the table can be rebuilt identically at any time, and running it again overwrites rather than duplicates.

### Learned (client table)
- CloudShell is a signed-in command line inside the AWS console. It can clone the GitHub repo and run a script with no local setup.
- Keeping data and loader scripts in the repo makes the AWS setup repeatable. It's the first step towards infrastructure as code.

- Wrote 40 labelled test emails in `data/test-emails/test_emails.json`, each with its expected type, urgency, client, advice and injection flags, expected sources and checklist matches. The mix:
  - 7 prospects
  - 9 admin questions, including the injection email
  - 7 advice questions, 3 of them disguised
  - 7 documents emails
  - 6 Revenue or penalty emails
  - 4 spam or supplier emails, including Revenue-themed phishing
- A script cross-checked every test email against the client table and the knowledge base files: correct client IDs, sources that exist, and checklist codes that are really outstanding. It found 0 problems.

### Decided (test set)
- Applied the recommended default for OQ-3 (multi-intent emails): one primary type plus flags. T29 (unclear documents plus an advice question) tests it.
- Built in deliberate tricky pairs: general information against personal advice (T15/T19), a routine Revenue document against penalties (T35), Revenue phishing (T38), and an identity-check trap (T28).

### Learned (test set)
- A test set is only useful if the expected answers are written down before the system exists. Otherwise it's tempting to accept whatever the system does.
- Cross-checking synthetic data with a script catches inconsistencies a human review would miss.

- Built the pipeline in `pipeline/triage.py`. It classifies and extracts with Nova, looks up the sender in DynamoDB, retrieves from the knowledge base, acts by type, and runs a rule-based fact check. It's tested from CloudShell with `scripts/run_one.py` and `scripts/run_eval.py`.
- **Evaluation runs 1 and 2** on all 40 emails (see `eval/run-1-baseline.md` and `eval/run-2-after-fixes.md`):
  - Classification went from 88% to 90%.
  - Urgent recall, advice detection, client lookup and injection catching were all 100%.
  - Unsupported facts went from 1 to 0, and checklist matching from 6/7 to 7/7.
  - Each email cost about $0.0013 and took about 3 seconds.
- **Deployed the API** with one script, `scripts/deploy.sh`. It created:
  - the emails table
  - a least-privilege IAM role
  - the Lambda function
  - a REST API with an API key and a usage plan of 2 requests a second and 300 a day

  CORS preflight is allowed without a key.

### Decided (pipeline)
- **Fact check method (OQ-6): rule-based.** It extracts every €, %, date and "N working days" and looks for each in the retrieved sources. It's free, predictable and explainable. Amounts that can be derived arithmetically are labelled "calculated" for a human to check.
- **Templates where the answer is fixed:** document acknowledgements and the consultation offer are templates. The consultation fee is read from the fee guide with a metadata-filtered search. The AI writes only where the wording genuinely varies.
- **Rules enforced in code, not only in prompts:**
  - advice never gets a client answer
  - an injection flag stops all actions
  - only the documents step updates records, and only from file names
  - approving a draft with unsupported facts needs an edit or an explicit override
- **The EU inference profile, not global,** so processing stays in the EU.

### Learned (pipeline)
- The evaluation found problems a demo would have hidden:
  - a newsletter got a reply drafted
  - a client's files were ignored when they also asked a question
  - a consultation was quoted at €150 instead of €120
  - two prices were added across different billing periods (€104)
- Some "errors" were really label ambiguity. I kept the original labels rather than moving the goalposts after seeing results, and explained each one instead.
- One retrieval metric was measuring the wrong thing: advice emails never get a drafted reply, so whether they retrieve the policy document doesn't matter. I added a second metric for emails that do get a draft, and kept the original alongside it.
- The model copied a specific appointment day from a past reply. Past replies need an explicit "tone and structure only" rule.

- **Tested the live API** with a new email from Siobhán ("can I pay by card?"). It was classified as an admin question, she was recognised as client C001, and the draft quoted card or bank transfer within 14 days, with sources. Cost 0.12 cents, about 2 seconds.
- **Built the first version of the front end in Lovable** from `frontend/lovable-prompt.md`: the queue, a detail panel and approve/edit/reject. The API key was added in Lovable only, not in GitHub.
- Extended the fact check to cover day counts ("14 days") and call lengths ("20-minute"), after noticing "14 days" wasn't being checked.
- **Client version of drafts:** the stored draft keeps `[S1]` source tags for review, and a tag-free version is saved as `final_client_text` on approval. Source tags must never reach a client. (Code pushed; it goes live with the next `update_lambda.sh`.)

### Decided (review experience, after a design discussion)
- **The draft is shown clean, as an email,** with no inline `[S1]` tags. The tags were useful for checking, but they made the draft read like a document rather than an email.
- **Fact-check warnings are exception-only:** silent when every fact is supported, a clear warning when a figure isn't in any firm document. The check stays, because it caught the €150 error, but it doesn't clutter routine reviews.
- **Side panel = client context,** meaning the client card plus this sender's previous emails in the system. There are deliberately no AI-written explanations, to keep it simple.
- **Sources are kept, collapsed, for audit,** so the firm can show where a reply came from if it's ever disputed.
- **Routing:**
  - admin questions and prospects go to Sinéad
  - documents, advice and Revenue letters go to the client's accountant (a partner if the sender is unknown)
  - spam is filed
  - injection attempts and low-confidence emails go to Sinéad for manual triage

  This fixes a gap where everything went to the client's accountant, even invoice questions.
- **Shared inbox to personal mailboxes:** every email lands in the shared inbox, and after triage it's routed to the assignee's mailbox. The demo simulates this with a mailbox selector. Real forwarding is on the v2 list.
- **Success measures:** correct categorisation and routing, timely turnaround (time from arrival to decision), and resolution (items reaching Done).

### Learned (review experience)
- The best review screen matches how the reviewer works, not what the system can show. Inline citations suit a research paper. An email reviewer needs a clean email, context about the sender, and warnings only when something is wrong.
- A traceability feature (source tags) and a presentation choice (show them or not) are separate decisions. Keep the data, and choose the display for the user.
- Routing was under-specified in the original scope. "Assigned accountant" isn't the right owner for admin work. Writing out the routing table exposed it.

- **Implemented US-18 to US-20:** routing with a stated reason, a client card with outstanding items, sender history (`GET /emails?from_email=`), clean drafts (tagged copy kept for audit), source snippets, and routing accuracy in the evaluation.
- **Front end, version 2:** the first Lovable account built the secure design (the key held server-side, with a proxy that only forwards to `/emails` and `/test-emails`), but ran out of free credits before the key could be added. A second account built the same design with the key in browser code (the accepted demo limitation) and is working. The secure version is to be finished when credits reset.
- Added `scripts/reset_demo.sh` (clear emails, restore clients) and `scripts/rotate_api_key.sh` (replace the key, since it has been pasted in chats).

### Found by testing in the app
- **The client card disagreed with the reply.** The card showed items as outstanding that the documents reply said had arrived, because the card was captured before the email was processed. Fixed: the card shows the position after the email.
- **Test emails gave away the answer.** T19 said "Not a client yet" and T33 said "I'm not a client". Real senders don't write that, and it hands the AI the classification the client lookup should establish. Both were rewritten.
- **Routing ignored the advice flag.** An unknown sender asking "do I need to register for VAT?" was classified as a prospect with an advice flag, and routed to Sinéad instead of a partner. Fixed: any advice flag routes to the accountant, or to the partner on duty for unknown senders.
- **The internal briefing note gave advice, with flawed reasoning.** It told the partner that the sender was "not required to register", quoting the €42,500 **services** threshold for someone selling **goods** (€85,000). Fixed: briefing notes quote the guidance and state the sender's facts, but never apply a rule or reach a conclusion. The judgement stays with the accountant.

### Learned (testing in the app)
- An internal note can still carry advice risk. If staff trust it, a wrong conclusion in it is as harmful as one in a client email.
- Test data must sound like real senders. Phrases that label the email ("not a client yet") inflate the scores.
- Looking at real outputs on screen catches problems that aggregate metrics don't. The evaluation passed these emails on type, but the routing and the note were wrong.

### Next
- Update the Lambda, reset the demo, and re-run the evaluation (run 3) with routing accuracy.
- Finish the secure Lovable version (key server-side) and rotate the API key.
- Add the Bedrock Guardrail.
