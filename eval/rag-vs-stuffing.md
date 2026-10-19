# RAG vs prompt-stuffing (US-16)

**The question:** does retrieving the relevant passages (RAG) beat simply pasting every document into the prompt?

**The test:** the same 40 test emails, the same model (Nova 2 Lite, EU profile), and the same prompts, guardrail and fact check. Only the source text given to the model differs:
- **RAG:** each draft or briefing note gets the top 5 passages retrieved from the Bedrock Knowledge Base (S3 Vectors).
- **Prompt-stuffing:** each draft or briefing note gets all 33 knowledge-base documents (39,190 characters of text) in the prompt.

**Note on token figures (corrected 19 Oct):** an earlier version of this page said the 33 documents were "about 10,000 tokens". That was an estimate from the text size (39,190 characters at roughly 4 characters per token), not a measurement. The measured figures are in the table below: **8,625 input tokens per email** with every document in the prompt, against **2,150 with RAG**. These are averages over all the emails that used sources, across every model call for each email, so they're not the size of a single prompt.

Produced by `scripts/run_eval.py` (with and without `--stuffing`) and `scripts/compare_rag_stuffing.py`.

## Results

| Measure | RAG | Prompt-stuffing |
|---|---|---|
| Emails compared | 40 | 40 |
| Classification accuracy (doesn't use sources) | 37/40 | 37/40 |
| Drafts produced | 22 | 21 |
| **Facts in drafts found in a source (grounded)** | **32/33 (97%)** | **25/28 (89%)** |
| Unsupported facts flagged | 0 | 2: T11 "18 November 2025", "31 October 2025" |
| Calculated amounts flagged | 1: T06 "€136" | 1: T06 "€104" |
| Drafts blocked by the guardrail (advice) | 2: T05, T15 | 3: T01, T05, T15 |
| **Avg input tokens per email** (emails that use sources) | **2,150** | **8,625** |
| Avg output tokens per email | 296 | 294 |
| **Avg cost per email** (emails that use sources) | **$0.00139** | **$0.00332** |
| Total cost of the run (model calls) | $0.0514 | $0.1192 |
| Median latency per email | 2.6 s | 2.6 s |

Prompt-stuffing sent **4.0× more input tokens** and cost **2.4× more** per email that uses sources. The cost ratio is lower than the token ratio because output tokens, which cost more, were the same in both.

### Emails where the outcome differed

| ID | RAG | Prompt-stuffing |
|---|---|---|
| T01 (quote request) | Draft for review | Blocked by the guardrail as advice |
| T11 (tax return deadline) | Draft for review, all facts supported | Draft for review with two dates flagged: the deadlines were given as **2025** instead of 2026 |

## What it means

- **RAG was more accurate.** 97% of facts in RAG drafts were found in a source, against 89% with every document in the prompt. With more text to work from, the model drifted more: it gave T11's deadlines with the wrong year, a mistake RAG drafts no longer make since the run 5 fixes. It also turned T01's plain quote into wording the guardrail treated as advice.
- **RAG was cheaper:** about 2.4× less per email.
- **Speed was the same.** At 33 documents, the larger prompt didn't slow the model down noticeably.
- **The safety layers worked in both modes.** The fact check flagged both wrong dates, and the guardrail blocked the advice drafts. No unchecked error would have reached a reviewer.
- **T06 combined prices in both modes,** with a different total each time (€136 and €104). This confirms the payroll quote should become a template (already on the list).

## Limits of this test

- **The knowledge base is small.** At 33 documents, prompt-stuffing still works and costs a third of a cent per email. RAG's advantage grows with the size of the knowledge base: a real practice with thousands of documents couldn't fit them in one prompt, and cost and latency would rise with every document added.
- **One run of each, on 40 emails.** The differences show a direction, not a statistically proven result.
- **RAG's retrieval and embedding cost is excluded.** It's a fraction of a cent per query at this scale.
- Costs use approximate Nova 2 Lite prices ($0.30 input and $2.50 output per million tokens).

## RAG run, compared with run 5

The RAG half of this test is also a fresh evaluation of the live pipeline. It matched run 5: classification 37/40, the same two guardrail blocks (T05 and T15), no unsupported facts, and T06 flagged as calculated.
