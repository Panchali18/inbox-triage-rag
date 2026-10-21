# Evaluation run 7: safe standard reply and a next step that fits the price (17 Oct 2026)

**What changed since run 6:**
- A blocked prospect draft is replaced by the safe standard reply (US-23).
- The discovery call is offered only for "from" prices, with softer wording for sole traders.
- The added next-step sentence is backed by the fee guide.

Same 40 synthetic test emails, model `eu.amazon.nova-2-lite-v1:0`, guardrail on. 0 errors.

| Metric | Run 6 | **Run 7** | Target |
|---|---|---|---|
| Classification accuracy | 37/40 (92%) | **37/40 (92%)** | at least 90% |
| Routing accuracy | 40/40 (100%) | **40/40 (100%)** | at least 90% |
| Urgent-item recall | 5/5 (100%) | **5/5 (100%)** | 100% |
| Advice detection recall | 8/8 (100%) | **8/8 (100%)** | 100% |
| Advice false positives | 1 (T30) | **1 (T30)** | low |
| Advice questions answered to a client | 0 | **0** | 0 |
| Client lookup accuracy | 40/40 | **40/40 (100%)** | 100% |
| Retrieval hit rate, all emails that search | 22/28 (79%) | **21/28 (75%)** | at least 80% |
| Retrieval hit rate, drafted replies | 15/15 (100%) | **15/15 (100%)** | at least 90% |
| Checklist matching accuracy | 7/7 | **7/7 (100%)** | 100% |
| Prompt injection caught, no draft | 1/1 | **1/1 (100%)** | 100% |
| Drafts claiming identity verified | 0 | **0** | 0 |
| Drafts blocked by the guardrail | 2 (T05, T15) | **2 (T05, T15)** | only drafts that give advice |
| **Blocked prospect drafts replaced by the safe standard reply** (new) | | **1/1 (T05)** | every blocked prospect draft |
| Drafts produced | 22 | **23** (T05 now has a reply) | |
| Unsupported facts flagged | 1 (T11) | **1 (T11 "18 November 2026")** | 0 reaching approval |
| Calculated amounts (combined prices) | 0 | **0** | |
| Wording warnings | 2 (T07, T11) | **3:** T05 safe standard reply (a notice, as designed), T10 price written by the model, T11 rule applied to the sender | low, all visible to the reviewer |
| Prospect replies offering the next step | 6/6 | **7/7 (100%)**, including T05 | 100% |
| Drafts with suggested attachments or links | 8 | **9:** fee guide (T01, T02, T03, T04, T06, T07), terms of engagement (T08), FAQ (T09), Revenue pay and file page (T11) | |
| Cost per email | about $0.00133 | **about $0.00129** ($0.052 for the run) | |
| Median latency | 3.2 s | **4.4 s** (max 9.5 s) | under 29 s |

## What it shows

- **Mateus (T05) now gets a usable reply.** The guardrail still blocks the AI draft (correctly), and the safe standard reply takes its place. Every prospect, all 7, now gets a next step.
- **No regressions** in routing, urgent items, advice, lookup, checklists or injection.
- **Retrieval for drafted replies stays at 15/15.** The overall rate (75%) moves by one email between runs. All the misses are advice emails (T16–T22) that only get an internal briefing note.
- **The median latency rose to 4.4 seconds,** probably because of the extra knowledge-base lookup for the fee guide's "How quotes work" section, and normal Bedrock variation. It's well under the 29-second API limit.
- **The open items stay visible to the reviewer:** T10's model-written price, T11's "18 November 2026" (flagged because Revenue's page gives the date without a year; corrected 21 Oct, it isn't invented) and its "your 2025 tax return" wording.
