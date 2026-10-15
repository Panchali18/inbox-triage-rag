# Inbox Triage with RAG

**Demonstration only.** This is a portfolio project. The firm, its staff, clients and emails are all fictional. No real data is used and no email is ever sent.

An AI pipeline that triages the shared inbox of a small accounting practice. It classifies each email, looks up the sender, retrieves the relevant firm policy and Revenue guidance, and drafts a grounded reply for a human to approve. Advice questions always go to an accountant.

> **Status: in progress.** Week 1 (account checks, synthetic data, knowledge base, client table and test set) is complete. Week 2 (Lambda, API, guardrails and front end) has not started. Close date: Friday 6 November 2026. See [build-log.md](build-log.md) for progress, decisions and learnings.

---

## The problem

Nore Valley Accountants is a fictional five-person practice in Kilkenny, Ireland, serving sole traders and small companies. Around tax deadlines the shared inbox floods with:
- prospects asking for quotes
- clients asking admin questions
- documents sent in
- forwarded Revenue letters
- occasional urgent penalty notices

Urgent items get buried, prospects wait days, and staff answer the same admin questions again and again.

## What it does (v1 design)

1. **Classify** the email: prospect, admin question, advice question, documents sent, Revenue letter or penalty, or spam/supplier.
2. **Extract** the sender, what they need, any dates, and the urgency.
3. **Look up** the sender in the client table: are they a client, what services do they have, who is their accountant, what's outstanding?
4. **Retrieve** relevant passages from the knowledge base: firm documents, past replies and Revenue guidance.
5. **Act by type:**
   - **Prospect or admin question:** draft a grounded reply with citations.
   - **Advice question:** no client draft; a briefing note goes to the accountant.
   - **Documents sent:** match them to the checklist and list what's missing.
   - **Revenue letter or penalty:** mark urgent and put it at the top of the queue.
   - **Spam or supplier:** file it.
6. **Check** that every fee, date and promise in a draft appears in a retrieved source.
7. **Human review:** approve, edit or reject. Nothing is sent.

Full user stories and acceptance criteria: [scope.md](scope.md).

## Design rules
- The AI never gives tax advice to clients. Advice questions always go to a person.
- The AI requests identity documents from the checklist, but never decides on anti-money-laundering verification. Only a partner does that.
- Email content is untrusted data, because of the prompt-injection risk.
- If no source answers a question, the draft says so. It never guesses.

---

## Architecture

| Component | Service | Status |
|---|---|---|
| Knowledge base | Amazon Bedrock Knowledge Bases | ✅ Built and tested |
| Vector store | Amazon S3 Vectors | ✅ |
| Embeddings | Amazon Titan Text Embeddings V2 (1024 dimensions) | ✅ |
| Document storage | Amazon S3 | ✅ |
| Main model | Amazon Nova 2 Lite (EU cross-region inference profile) | ✅ Tested in the console |
| Client lookup | Amazon DynamoDB (`inbox-triage-v1-clients`, 15 clients) | ✅ Loaded |
| Pipeline | AWS Lambda (Python) | Planned, week 2 |
| API | Amazon API Gateway with an API key | Planned, week 2 |
| Safety | Amazon Bedrock Guardrails (no tax advice, PII filters) | Planned, week 2 |
| Front end | Lovable (React) | Planned, week 2 |
| Evaluation | RAGAS, plus a custom test set of 40 emails | Planned, week 3 |
| Observability | Amazon CloudWatch | Planned, week 2 |

**Region:** eu-north-1 (Stockholm). The AWS account is locked to this region. Data stays in the EU, which is the test that matters under GDPR. A real deployment for an Irish firm could choose eu-west-1 (Ireland).

### Why RAG for documents but lookup for clients

- **RAG (search by meaning)** suits documents. An email asking "what do you charge for a return?" has to match a fee guide that says "Form 11 starts from €450".
- **Exact lookup** suits facts about a specific client, such as who their accountant is and which documents are outstanding. Similarity search could return the wrong client's record. A database query by email address can't.

---

## Repository layout

| Path | Contents |
|---|---|
| `scope.md` | User stories, acceptance criteria, assumptions and open questions |
| `build-log.md` | Step-by-step log of decisions and learnings |
| `data/kb/firm/` | 4 synthetic firm documents: fees, engagement terms, checklists, FAQ |
| `data/kb/past-replies/` | 20 synthetic past replies |
| `data/kb/revenue/` | 9 revenue.ie pages, saved as text with attribution |
| `data/test-emails/` | 40 labelled test emails for the evaluation |
| `data/clients/clients.json` | 15 synthetic clients for the DynamoDB lookup |
| `scripts/load_clients.py` | Loads `clients.json` into DynamoDB (run in AWS CloudShell) |
| `scripts/build_kb_upload.py` | Builds `kb-upload/`: clean text plus `.metadata.json` files |
| `kb-upload/` | The files actually uploaded to S3 for the knowledge base |

`data/kb/` is the human-readable copy, with banners and attribution at the top of each file. `kb-upload/` is the machine copy. Boilerplate is moved into metadata files, because repeated text at the top of every chunk was found to weaken search results (see the build log, day 2).

To rebuild the knowledge base files after editing `data/kb/`:

```
python3 scripts/build_kb_upload.py
```

Then upload the three folders in `kb-upload/` to the S3 bucket and sync the knowledge base.

---

## Data

- **All firm, staff, client and email data is synthetic.** Client emails use the reserved `example.com` domain.
- **Revenue guidance:** Information provided courtesy of the Revenue Commissioners under a [Creative Commons Attribution 4.0 International (CC BY 4.0) licence](https://www.revenue.ie/en/corporate/using-revenue/reuse-of-public-sector-information/public-sector-information-licence.pdf). Pages were saved on 15 October 2026 and may have changed since. The text only is stored, with no Revenue logos. This project is not affiliated with or endorsed by the Revenue Commissioners. See [data/kb/revenue/README.md](data/kb/revenue/README.md).

## What a real deployment would need (GDPR note)

This demo uses synthetic data only. A real practice would also need:
- a data processing agreement with AWS
- a privacy notice and a data protection impact assessment (DPIA)
- a check of client contracts for any requirement to hold data in Ireland
- a retention policy for emails, logs and drafts, in line with the six-year records rule
- access controls (staff login, not an API key) and audit logging of approvals

## Cost controls

- A $5 monthly AWS budget alert.
- Pay-per-use services only. S3 Vectors was chosen over OpenSearch Serverless, which has an always-on minimum charge.
- Every resource is tagged `Project=inbox-triage-v1`, `Owner=panchali`, `Env=demo` and `DeleteAfter=2027-04-10`.

### AWS resources (clean-up list)

| Resource | Name |
|---|---|
| S3 bucket | `inbox-triage-v1-kb-docs-pd` |
| Bedrock Knowledge Base | `inbox-triage-v1-kb` (data source `inbox-triage-v1-kb-docs`) |
| S3 vector bucket and index | Created automatically by the Knowledge Base quick create |
| DynamoDB table | `inbox-triage-v1-clients` |
| IAM role | `AmazonBedrockExecutionRoleForKnowledgeBase_vg70k` |
| AWS Budget | `account-monthly-5usd` (account-wide, kept after clean-up) |

## Limitations (so far)

- Synthetic data only. Real inbox email is messier.
- The Revenue pages are a snapshot from 15 October 2026.
- In retrieval tests, one Revenue question ranked the best page second rather than first. This will be measured properly in the week-3 evaluation.
