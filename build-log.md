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
| Chunking | Default (about 300 tokens) | Most files are short, so they stay whole. The fee guide and terms split into a few chunks. | Hierarchical or semantic chunking: a possible future feature if retrieval scores are weak |
| Main model | Amazon Nova 2 Lite | Native in Stockholm, cheap and fast. Claude isn't in the Stockholm catalogue. | A small Claude model via EU cross-region inference: kept as a backup |
| Client lookup | DynamoDB table, called as a tool | Structured facts (who is the client, what's outstanding) need exact lookups, not similarity search. DynamoDB also appears in AI job posts. | A JSON file in S3: simpler but less realistic |
| Front-end access | API Gateway with an API key and throttling | Enough for a demo, with less setup | Cognito login: more realistic, but adds a week-2 dependency |
| Budget | $5 a month alert on the whole account | FitProof costs about $1.30 a month, so $5 gives an early warning | $10: too late a warning on a $119 credit balance |
| Demo lifetime | Live until 10 April 2027 | The LinkedIn post links to a working demo. Idle cost is close to zero. | Delete when the build closes: the demo link would break days after posting |
| Firm name | Nore Valley Accountants (fictional) | First idea, "Brennan & Kerr", was too close to a real firm (RBK) | |
| Revenue content | 9 pages saved as text, with CC BY 4.0 attribution | Revenue's licence allows reuse with credit, but not its logos | Storing the PDFs: they contain the Revenue logo |
| Expenses guidance | Left out | Only available in long technical manuals. Expense questions are advice, so they go to an accountant. | |
| Knowledge base text | Clean text, with labels in `.metadata.json` files | Repeated banners and header tables weakened search results (found in testing) | Banners inside each document |
| Main model access | EU cross-region inference profile (`eu.amazon.nova-2-lite-v1:0`) | Processing stays in EU regions | The "global" profile, which could route anywhere |
| Fact check | Rule-based: every €, %, date (with year), day count and call length looked up in the sources and the sender's own email | Free, predictable, explainable. It caught €150 vs €120 and a wrong year. | A second AI call to judge facts: costs more, and can itself be wrong |
| Fixed replies | Templates (documents received, consultation offer) | Wording that never changes can't be invented | AI-written every time |
| Advice rule | Enforced in code: advice never gets a client answer, only a briefing note or a consultation offer | Prompts alone were ignored in testing | Relying on the prompt |
| Guardrail | Bedrock Guardrail on the **output draft only**: denied topic "personal tax advice", PII masking | A second, independent layer. Screening the incoming email would block the advice questions we need to route. | Guardrail on the input, or no guardrail |
| Routing | A deterministic table: admin and prospects to the practice manager, documents, advice and Revenue letters to the client's accountant (a partner if unknown), spam filed, injection and low-confidence emails to manual triage | Predictable, explainable, testable (100% in the evaluation) | Letting the AI choose the assignee |
| Review screen | Clean draft, client card and history beside it, warnings only when something's wrong, sources collapsed | Matches how a reviewer works with email | Inline `[S1]` citation tags in the draft |
| Throttling | Adaptive retries with backoff on every Bedrock call | New accounts have low model quotas. One evaluation email failed before this. | Failing on the first throttle |
| Deployment | Scripts run in CloudShell (`deploy.sh`, `update_lambda.sh`, `reset_demo.sh`, `rotate_api_key.sh`) | Repeatable, and documented in the repo | Clicking through the console |
| RAG vs prompt-stuffing | Keep RAG | Tested: 97% vs 89% of facts grounded, 2.4× cheaper, same speed, and it scales past what fits in a prompt | All documents in every prompt |
| Front end | Lovable (React) calling the API through a server-side proxy (secure version), or directly with a rate-limited key (demo version) | Lovable is in AI job posts. The server-side version keeps the key out of the browser. | Streamlit (excluded in the brief) |

---

## Day 1: Wednesday 14 October 2026: scope and account checks

### Done
- Wrote the scope as 17 user stories with acceptance criteria, assumptions and open questions ([scope.md](scope.md)).
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
- **Shared inbox to personal mailboxes:** every email lands in the shared inbox, and after triage it's routed to the assignee's mailbox. The demo simulates this with a mailbox selector. Real forwarding is listed as a possible future feature.
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

- **Evaluation run 3** (`eval/run-3-routing.md`): routing accuracy 100% and classification 92%. One email failed because Bedrock throttled the request. Fixed with adaptive retries and backoff, plus slower pacing in the evaluation script.
- **Fact check:** figures the sender stated (such as "turnover around €600k") no longer count as unsupported.
- **Bedrock Guardrail created and connected** (`inbox-triage-v1-guardrail`):
  - **Denied topic "Personal tax advice"** on output.
  - **PII masking:** card numbers, IBANs, passwords, and a custom Irish PPSN regex.
  - **Applied with ApplyGuardrail to the finished draft only,** not to the incoming email or to fixed templates.
- **First guardrail test (T05, Mateus):** blocked. The model had written "you will need to register for Income Tax", again, despite the prompt rule.
- **Evaluation runs 4 and 5** (`eval/run-4-5-guardrail.md`). Run 4 blocked 4 drafts (T01, T05, T11, T15). Reading them showed:
  - **T05:** correct, personal advice.
  - **T11:** useful, the deadline was given with the **wrong year**, 2025 instead of 2026.
  - **T15:** borderline but fair, a general rule applied to "you".
  - **T01:** a clean quote, a **false positive**.

  After tuning the guardrail's definition and sample phrases, adding a third-person attribution rule for Revenue facts, and adding year checking to the fact check, run 5 blocked only **T05 and T15**. It also kept routing, urgent and advice at 100%, and reached 100% retrieval for drafted replies.

### Decided (guardrail)
- **Screen the output, not the input.** Screening incoming emails would block exactly the advice questions we need to route to accountants.
- **Block advice, mask PII.** A blocked draft is kept for audit and never shown as a draft. A masked draft is kept with placeholders.
- **Accept a small over-block rate.** One borderline block in 22 drafts means one manual reply, which is a far smaller cost than advice reaching a client.

### Learned (guardrail)
- **Prompts are instructions, not guarantees.** The model broke the "no advice" rule twice and the "no price arithmetic" rule three times. Enforcement has to sit outside the prompt: in code, in the fact check and in the guardrail.
- **Measure a guardrail's false positives, not just its catches.** The first version blocked a perfect quote. Reading every blocked draft was the only way to tell good blocks from bad ones.
- **Sample phrases shape the topic.** One example that sounded like normal business language ("as a sole trader you must register…") pulled ordinary quotes into the blocked topic.
- **Blocks can reveal other bugs.** The T11 block exposed a wrong year that the fact check had missed, because it compared dates without years.
- **Throttling is a real production concern,** even at demo scale. New accounts have low model quotas, so retries with backoff are needed from day one.

### Human review in the app (US-13)
- **Approve:** Tariq's consultation offer was approved. It moved to Done, the history recorded the decision, and "Avg time to decision" showed 2.4 minutes.
- **Edit, then approve:** Mateus's draft contained personal advice ("you will need to register for taxes"). The paragraph was deleted in the app and the draft saved with "Save edit & approve". The history shows `edit → approved`, so the human correction is auditable. This happened before the guardrail existed, and was the case that motivated it.
- **Reject:** "Confirm reject" stays disabled until a reason is typed, as US-13 requires.
- **A judgement left to the human:** Siobhán's "still waiting" draft said "your query is with Ciarán". Ciarán is her accountant per the client record, so it's plausible, but nobody knows what her earlier email was about. That's left for the reviewer to check rather than adding another prompt rule.

### Small items noted for later (not yet done)
- The Lovable checklist shows codes (`ST-EXP`) instead of names. The API already returns `matched_names` and `still_outstanding_names`.
- The advice banner says "no answer is drafted for the client", but unknown senders do get a consultation offer. Better wording: "Advice question: no tax advice is given; the client is offered a consultation or the accountant replies."
- Drafts to senders who write in simple English (T05) use fairly formal language. A "match the sender's language level" rule would be kinder.
- T06 (company payroll quote): the model keeps combining prices, flagged amber every time. It's a candidate for a template quote.

### Parked (Thursday 15 October 2026, 13:50)
Work paused until the weekend. Everything is on GitHub. AWS resources stay running: they're pay-per-use and cost almost nothing when idle.

---

## Day 3: Saturday 17 October 2026: RAG comparison, secure front end, better replies, evaluation

### Done
**1. RAG vs prompt-stuffing (US-16).** Ran the evaluation twice on the same 40 emails: the top 5 retrieved passages, then all 33 documents in the prompt ([`eval/rag-vs-stuffing.md`](eval/rag-vs-stuffing.md)).
- RAG 97% of draft facts grounded vs 89%; 0 unsupported facts vs 2; 2 guardrail blocks vs 3; 2,150 vs 8,625 input tokens per email; $0.0014 vs $0.0033 per email; both 2.6 seconds.
- The RAG run matched run 5 (classification 37/40, blocks on T05 and T15 only), so the live pipeline is stable.

**2. Secure front end.** The API key was rotated (`rotate_api_key.sh`, old key deleted) and stored as an encrypted server-side secret in Lovable. The app calls the API through a server proxy, so the key is no longer in browser code. The old key-in-browser app (second Lovable account) stopped working when its key was deleted, as intended. Checklists show document names, and the advice banner has the new wording.

**3. No search for documents emails.** Wojciech's documents email showed a "Sources used (5)" box, although the reply came from a template and his checklist. Documents emails now skip retrieval, unless they also contain an advice question (the briefing note needs the guidance then). Adaeze's documents email confirmed it: "Sources used (0)".

**4. Replies that speak as the firm.** Liam's quote said "As outlined in our fee guide…" and "this would be the relevant fee for your situation", promising €450 before anyone had seen his records.
- Prompt rules: speak as the firm, never mention internal material, open with "Hi <name>", end with "Kind regards,", match the sender's language level.
- A rule-based **wording check** (`wording_check`, flag `wording`) flags internal references, price judgements, prices the model wrote itself, and rules applied to the sender ("your 2025 tax return", "you must register").

**5. Prices written by code (US-22).** The model chooses which fee-guide rows answer the question in a separate small call; code inserts those rows word for word under "Here are our prices:", plus "All fees exclude VAT." The draft model is told to write no prices. This replaces the planned payroll-quote template with a fix for every quote.

**6. Suggested attachments and links (US-21).** Shareable sources the draft uses are suggested. Firm documents (fee guide, FAQ, terms of engagement) appear as unticked attachments with a "View" link to a branded PDF (`scripts/build_client_pdfs.py`, `docs/client-documents/`). Revenue pages are public, so they're added to the email as links above the signature. Past replies and the internal onboarding checklist are never suggested. The approval records the ticked attachments (`final_attachments`).

**7. Every prospect gets the next step.** If a prospect draft doesn't mention the discovery call, code adds the fee guide's wording before the sign-off.

**8. Smaller items.** The client card shows service names ("Form 11 tax return") instead of codes. OQ-1 and OQ-2 marked decided. The list of possible future features completed.

**9. Evaluation run 6** ([`eval/run-6-better-replies.md`](eval/run-6-better-replies.md)): no regressions. Routing, urgent items, advice detection, lookup, checklists and injection all at 100%; 0 advice answered to a client. **No combined prices for the first time** (T06 was flagged in every earlier run). 6/6 prospect replies offer the discovery call. Suggestions on 8 drafts, including the Revenue link on T11. Two wording warnings (T07, T11), and T11's "18 November 2026" flagged by the fact check (later found to be in Revenue's page without the year; see day 4). About $0.0013 per email, median 3.2 seconds.

**10. RAGAS, first run** ([`eval/ragas-run-1.md`](eval/ragas-run-1.md)), judged by Amazon Nova Pro: faithfulness 0.71 on average, context relevance 1.00 for every email. Correct price quotes scored low (T01 0.38), and simple admin replies scored 0.00 (T14) and 0.20 (T13). (I first read T11's 1.00 as missing an "invented date"; day 4 showed the date is in Revenue's page, so that reading was wrong.) The likely cause is that the judge saw only the retrieved passages, not the client record or the sender's email that the drafting model also used. Re-run with the full context in step 13.

**11. Safe standard reply when a prospect's draft is blocked.** Mateus (T05) is blocked by the guardrail in every run, because the model tells him "you will need to register for Income Tax". The block was right, but it left Sinéad with nothing to send to a prospect who asked for a price. Now, when a prospect's AI draft is blocked, the reviewer gets a standard reply built only from fixed wording, the code-inserted prices and the fee guide's next step, with an amber note: "The AI draft was blocked as tax advice, so the standard reply is shown". The blocked draft stays in the audit record.

**12. The next step fits the price.** Following a question about whether everyone needs a discovery call: the call is the fee guide's process for turning a "from" price into a fixed quote, so it stays for "from" prices. If every quoted price is fixed (such as the €60 bank letter), the reply invites the sender to reply to go ahead instead. For a sole trader's tax return, the wording is softer: "a quick, free 20-minute call to confirm your quote".

**13. RAGAS, second run** ([`eval/ragas-run-2.md`](eval/ragas-run-2.md)). The judge now also gets the client record, the firm's name and signatory, and the sender's email, which the drafting model had too. Faithfulness rose from 0.71 to **0.86**:
- Every prospect reply scored **1.00**.
- **T11 dropped to 0.83.** I first read this as catching an invented date. Day 4's statement-by-statement test showed the only unsupported statement was the Revenue web link (added by code from the page's address), and the date was supported.
- **T13 (0.29) and T14 (0.17).** ~~Real findings: the model invented a process and promised a meeting.~~ **Corrected 21 Oct:** both replies follow the firm's FAQ (Q13: email us the new bank details; Q10: book meetings through Sinéad), and those FAQ passages were among the retrieved text the checker was given. The low scores were the checker's error. The one unsupported part is Ioana's "next week" commitment.
- T08 got no score (the judge's answer couldn't be read). Context relevance was still 1.00 everywhere.

**14. Evaluation run 7** ([`eval/run-7-safe-reply.md`](eval/run-7-safe-reply.md)): Mateus (T05) now gets the safe standard reply, so all 7 prospects get a next step. Still no regressions: routing, urgent items, advice, lookup, checklists and injection at 100%; 0 combined prices; drafted replies found the right source 15/15. About $0.0013 per email, median 4.4 seconds.

**Final checks (T01, T06, T11):**
- **T01 (Liam) and T06 (Tom):** prices once, word for word, no totals, no "fee guide" wording, the discovery call included. The fee guide is suggested as an attachment, and "View" opens the PDF.
- **T11 (Ana):** the Revenue link is added. The fact check flags "18 November 2026" (Revenue's page says "18 November" without a year, so the year can't be verified), and the wording check flags "your 2025 tax return".

### Blocked and rerouted
| What happened | Why | What we did instead |
|---|---|---|
| `git pull` in CloudShell refused to run | The comparison had saved a local copy of `eval/rag-vs-stuffing.md`, and the fuller version was on GitHub | Deleted the local copy (its content was already on GitHub) and pulled again |
| A fix seemed not to work in the app | The Lambda was still running the old code, because the pull had failed | Checked the model-call count (2 calls meant no advice detected, so the new code would have skipped the search), found the failed pull, and redeployed |
| "Network error: could not reach the API" in the Lovable preview | The preview reloaded while Lovable was rebuilding | Waited for the build to finish and refreshed |
| Lovable didn't apply the change | It was in "Chat" mode, which plans and waits | Clicked "Build" |
| **First price design failed** | The model was asked to place a `{{PRICES}}` placeholder and add a `PRICE_ROWS:` line in a free-text email. It put the placeholder mid-sentence and three times over, still wrote "€450" and a "€104 a month" total itself, and assumed monthly payroll when the sender said weekly. T01 was blocked by the guardrail. | Split the job: a separate small call returns a JSON list of rows, and code inserts them. Second test: the price block was in the wrong place, because the model wrote its own "Here are our prices:" paragraph. Code now writes the lead-in and removes the model's. |
| No Revenue link on T11 | The draft dropped its `[S#]` source tags, and suggestions relied on them | A source also counts as used when the draft contains a date or amount from it |
| The Revenue link landed below the signature | The model left out "Kind regards" | Links go above the staff name when there's no closing line, and the prompt asks for "Kind regards," |
| Tom's own "€600k" was flagged as a price the model wrote | "k" wasn't read as thousands | The sender's own figures are normalised and ignored |
| "View" opened the Markdown source on GitHub | The first link pointed at the knowledge-base file | Built branded client PDFs and pointed "View" at them |
| "View" still opened the old page after the fix | That email was processed before the update; each email keeps the link it was given | Submitted a new email |
| Planned a knowledge-base re-sync to mark shareable documents | It would cost a sync and a step for no visible gain | Kept the shareable list in code; moving it into metadata is listed as a possible future feature |
| Evaluation run 6 had T07 "unsupported" facts ("20-minute", "3 working days") | Code added the discovery-call sentence, but the fee guide wasn't among T07's retrieved passages, so the fact check couldn't find those facts | When code adds the sentence, it also fetches the fee guide's "How quotes work" section from the knowledge base, so the facts are backed and visible to the reviewer |
| A loose fallback for Revenue links (link a Revenue page whenever a draft mentions Revenue) | Would add irrelevant links to prospect replies that just mention Revenue | Reverted. A source counts as used when the draft contains a date from it, even without the year |
| RAGAS: the `read -s` key prompt didn't wait, and the key was pasted as a command and shown on screen | A fiddly way to enter a secret | The key was deleted and replaced. The script now asks for the key itself, hidden |
| RAGAS: `gemini-2.5-flash` returned 404 | Closed to new API keys | Switched to `gemini-3.8-flash` |
| RAGAS: CloudShell signed out mid-run, and the installed packages were cleared | CloudShell sessions time out; results were only saved at the end | The script now saves after every email and resumes; packages are reinstalled in one line |
| **RAGAS: Gemini's free tier hit its daily limit** (20 requests per model per day; retry in 10 hours) | RAGAS makes several judge calls per email (about 60–80 for 13 drafts) | **Switched the judge to Bedrock** (EU profile): no extra key, data stays in EU regions, under $1 of credits |
| RAGAS: Claude Sonnet 5.5 returned AccessDeniedException, "not available for this account" | Claude models are listed in Stockholm but not enabled on this free-plan account | **Judge is Amazon Nova Pro** (EU profile), a larger model than the generator (Nova 2 Lite) but the same family. The script now stops at once if the judge returns no scores, instead of marking every email blank |
| Proposed "Sources found / Used" labels on screen | Not needed for the demo | Dropped, and listed as a possible future feature |

### Decided
- **RAGAS judge: Nova Pro on Bedrock.** Gemini's free tier was too limited, and Claude isn't available on this free-plan account (see the table above).
- **Don't publish RAGAS numbers until they're checked against the drafts, the sources and the expected answers.** (Corrected 21 Oct: the earlier version of this line said the second run "agrees with" the fact check on T11; both had flagged a correct date.)
- **Keep both checks, and treat both as flags for a person to check.** The rule-based fact check is exact for amounts and dates, but it flags a correct date when the source omits the year. The AI checker can miss evidence that's in front of it (T13, T14). Neither covers everything.
- **Keep RAG.** It was more accurate and cheaper on this test, and it's the only option that scales to a real firm's document volume.
- **The AI selects, code writes.** For anything that must be exact (prices, document names, checklists), the model chooses from a list and code produces the text. The model writes only the wording around it.
- **Suggest, never attach.** The system suggests documents, but only a person decides what reaches a client.
- **Shareable documents are listed in code for now** (see the table above).
- **A block shouldn't leave the reviewer empty-handed.** For prospects, a blocked AI draft is replaced by a safe standard reply (fixed wording, code-inserted prices, next step), marked clearly for the reviewer.
- **Warn, don't block, on wording.** A wording warning doesn't stop approval: the reviewer edits or accepts. Unsupported facts still need an override to approve.

### Learned
- **More context isn't better context.** With every document in the prompt, the model gave T11's deadlines with the wrong year, and the guardrail blocked T01's quote. With only the relevant passages, neither happened. (Corrected 21 Oct: the T01 draft was never read, so "advice-like wording" was a guess.)
- **At small scale, the difference is modest.** Prompt-stuffing still worked, cost a third of a cent and wasn't slower. The case for RAG here is accuracy and growth, not speed. Say so honestly rather than overselling it.
- **The safety layers are mode-independent.** The fact check and the guardrail caught the stuffing errors too.
- **A reply can be factually right and still wrong for a client.** Every fact in Liam's draft was in the fee guide, so the fact check passed it. Tone and commitments need their own check.
- **Small models handle selection better than formatting.** Asking Nova 2 Lite to place a placeholder and a control line inside an email failed; asking it for a short JSON list in a separate call works. Split jobs into small, checkable steps.
- **Prompts are still not guarantees.** Even with explicit rules and a bad-and-good example, the model sometimes writes a price, invents a date or addresses the sender. The checks in code are what make it safe; the prompt only makes it less frequent.
- **Not every source is shareable.** Past replies contain other clients' details, and the onboarding checklist describes the internal identity-check process. Retrieval doesn't care; the sharing rule has to.
- **"Sources used" usually means "sources found".** A RAG screen shows what the search returned, not what the answer relied on. In Tom's quote, 4 passages were listed; 1 supplied the facts, 1 the tone, and 2 weren't used. The similarity score (0 to 1) ranks passages; it isn't a percentage, and the most useful source isn't always first.
- **Free tiers are for trying, not for evaluation.** Gemini's free tier allowed 20 requests per model per day, and RAGAS needs several judge calls per email. Check the rate limits of a judge model against the number of calls before choosing it. Here, the judge already available in the same cloud (Bedrock) was cheaper in time, simpler (no extra key) and better for data residency.
- **The judge should be a different, stronger model than the one being judged.** The plan was Claude Sonnet 5.5 judging Nova 2 Lite's drafts, but Claude isn't available on this free-plan account. Nova Pro is larger than Nova 2 Lite but from the same family, so a shared blind spot is possible. Treat the scores as a second opinion alongside the rule-based fact check, not as proof.
- **Safe isn't the same as helpful.** The guardrail correctly blocked advice to Mateus, but the outcome was no reply at all to a prospect asking for a price. A safety layer needs a fallback that still serves the user.
- **"Listed" isn't "available".** A model appearing in the inference-profile list doesn't mean the account can call it. Test one call before building on it.
- **Long jobs need checkpoints.** A browser shell can time out at any moment; saving after each item turned a lost run into a resumable one.
- **An AI judge only knows what you show it.** RAGAS judged the replies against the retrieved passages only, but the drafting model also had the client record and the sender's email. Correct facts from the client record ("your accountant is Ciarán") looked unsupported, so simple admin replies scored 0.00.
- ~~The AI judge earned its place on the second run: it found replies that invent a process (T13) or promise a meeting (T14).~~ **Corrected 21 Oct:** both replies follow the firm's FAQ, which was in the material the checker was given; the low scores were the checker missing it. There was no knowledge gap to fill.
- **Automated scores need a sanity check against known cases, and so do my readings of them.** Context relevance was 1.00 for everything, so it measured nothing. And I read T11's score as missing an "invented date" without checking the source page, which did contain the date (day 4).
- **Label every estimate as an estimate.** The results page described the 33 documents as "about 10,000 tokens", a figure worked out from the text size, not measured, and it was nearly quoted in a LinkedIn post as a result. Every public number should come from a test, or say plainly that it's an estimate and how it was worked out. (Corrected 19 Oct; the measured figure is 8,625 input tokens per email, against 2,150 with RAG.)
- **Check where the code actually runs.** Two "fixes that didn't work" were the old code still deployed. Confirm the deploy (the commit in CloudShell, a fresh email) before debugging the logic.

## Day 4: Wednesday 21 October 2026: faithfulness, statement by statement

### Done
- Added `scripts/ragas_explain.py`, which shows how the faithfulness score is worked out: RAGAS splits the reply into statements, checks each one against the material it's given, and divides the supported ones by the total. Ran it on T01, T11 and T14, with documents only and with full context ([`eval/ragas-explain-21-oct.md`](eval/ragas-explain-21-oct.md)).

| Email | Documents only | Full context | What the statements showed |
|---|---|---|---|
| T01 Liam (correct quote) | 7/13 = 0.54 | 9/9 = 1.00 | 4 of the 6 unsupported statements were facts from Liam's own email (plumber, trading 3 years, spreadsheet, asked about cost); the other 2 described the reply ("Sinéad thanked Liam…"). The full-context check split the reply differently, into its own 9 lines, so the jump can't be credited to the added context. Some of its ✓ reasons quoted text that wasn't in the material. (Corrected 21 Oct.) |
| T11 Ana (deadline) | 5/6 = 0.83 | 5/6 = 0.83 | The only unsupported statement was the Revenue web link, added by code from the page's address. "18 November 2026" was supported both times. |
| T14 Ioana (meeting) | 0/6 = 0.00 | 1/7 = 0.14 | Almost everything marked unsupported, with reasons such as "It only includes Ioana's email". A follow-up check showed the FAQ answer on booking meetings ("contact Sinéad Kehoe, our practice manager") was among the retrieved passages, and the client record names Ciarán as her accountant. Only the "next week" commitment has no source. Pleasantries were also counted as unsupported. |

### Correction
- **"18 November 2026" was not invented.** Revenue's pay-and-file page says "the 31 October deadline is extended to 18 November", with no year; the model added 2026 from the page's 2026 example. The fact check flagged it because it requires the year, which is a fair caution. But I had described it as an "invented date" in the RAGAS reports, runs 6 and 7, the build log and a draft post, without checking the page. Corrected everywhere on 21 October.
- The earlier wrong-year cases stand: run 4 (31 October **2025**) and the prompt-stuffing run (2025 dates) gave years that contradict Revenue's page.

### Learned
- **A faithfulness score is supported statements ÷ all statements. Both parts can mislead.** The same reply was split into 13 statements in one call and 9 in another; greetings and sign-offs were counted as facts in one and not the other.
- **A ✗ isn't always an error.** Ana's only ✗ was a correct link; Ioana's mixed a real problem with pleasantries.
- **Read the statements before quoting the score.** The score only made sense once the statement-by-statement verdicts were on screen.
- **Check the source before calling something made up.** A flag from the fact check means "can't verify", which isn't the same as "invented".
- **The checker can miss evidence that's right in front of it.** Ioana's and Brian's replies follow the firm's FAQ, and the FAQ passages were in the checker's material (verified by printing the retrieved passages). It still scored them 0.14 and 0.29, and described its material as "only Ioana's email". I had reported both as replies that "made things up", and planned to add those processes to the FAQ, though they were already there.

### Done (afternoon): published the demo
- **Published the Lovable app:** https://nore-valley-inbox-triage.lovable.app
- **Key check passed.** In a private browser window, the browser's developer tools showed no `x-api-key` header on the request that loads the inbox. The key stays on the server.
- **Showcase setup for visitors** (all front-end changes; the API proxy and the key weren't touched; see [`frontend/lovable-changes-21-oct.md`](frontend/lovable-changes-21-oct.md)):
  - visitors see a fixed list of 11 showcase emails, plus only the emails they submit themselves
  - Approve, Edit and Reject on a showcase email change only that visitor's view, so the queue stays the same for everyone
  - drafted replies come first in the queue, and Lovable was asked to open a drafted reply on load
  - the sender name is required when submitting a new email
  - bold text in internal notes shows as bold, without the `**` asterisks
- **Ioana's email (T14) is left out of the showcase** (see "Found" below).

### Recorded late: the proxy fix (18 Oct)
- The secure proxy failed in Lovable's preview because its requests used redirect mode "error". Lovable switched it to "manual", and the app worked. Not logged at the time.

### Correction (afternoon)
- **Liam's 0.54 → 1.00 can't be credited to the added context.** Re-reading the screenshots: in the full-context check, RAGAS split the reply into its own 9 lines, and none of the six statements marked ✗ in the first check appeared. Some ✓ reasons also quoted text that wasn't in the material ("a reply to Liam Foley, starting with 'Hi Liam,'"). Corrected in `eval/ragas-explain-21-oct.md`, `eval/ragas-run-2.md` and the table above.
- **"Turned T01's quote into advice-like wording" (prompt-stuffing run) was never checked.** The blocked draft was never read. Corrected in `eval/rag-vs-stuffing.md` and Day 3's learnings.

### Found
- **Ioana's latest draft (made on 21 Oct) gave an existing client the prospect pitch:** a free discovery call, a fixed-fee quote and an engagement letter. It also promised a meeting "next week". Not yet investigated.
- **A new email with no sender name produced "Hi <first name>,".** The name is now required in the form; the pipeline itself still uses a placeholder.

### Learned (afternoon)
- **Re-read the evidence before each public claim, including your own earlier conclusions.** The 0.54 → 1.00 reading had been checked as a number but not as a cause, and the screenshot that disproved it was already in hand.
- **A shared demo needs a stable showcase.** With one shared inbox, the first visitors' clicks and test emails would change what everyone after them sees.

### Next session: resume checklist
1. **Investigate Ioana's draft:** why an existing client's meeting request got the prospect discovery-call wording.
2. **Optional prompt rule** against promising specific times ("next week").
3. **Pipeline:** when the sender's name is missing, greet with "Hello," instead of a placeholder.
4. **Don't run `scripts/reset_demo.sh`** without updating the showcase list in Lovable: it would clear the showcase emails.
5. Final README pass.
