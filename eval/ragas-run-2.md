# RAGAS scores, second run (US-15, AC4), 17 Oct 2026

**What changed since the first run:** the judge now sees everything the drafting model had: the retrieved passages, plus the client record, the firm's name and signatory, and the sender's email. The pipeline also had the latest changes: the safe standard reply for blocked prospect drafts, and a next step that fits the price.

**Judge:** Amazon Nova Pro on Bedrock (`eu.amazon.nova-pro-v1:0`, EU inference profile). It's larger than the drafting model (Nova 2 Lite), but from the same family.
**Data:** the AI-written replies from the latest evaluation run. Templates, the safe standard reply and internal briefing notes are excluded.

## Results

| Metric | First run | **Second run** |
|---|---|---|
| Faithfulness (average) | 0.71 | **0.86** (12 drafts scored; T08 returned no score) |
| Context relevance (average) | 1.00 | **1.00** (13 drafts) |

| ID | Email | Type | Faithfulness, run 1 | **Faithfulness, run 2** |
|---|---|---|---|---|
| T01 | Liam: price for a tax return | prospect | 0.38 | **1.00** |
| T02 | Chiara: new bakery company | prospect | 0.67 | **1.00** |
| T03 | David: "do you do accounts? how much" | prospect | 0.89 | **1.00** |
| T04 | Aisha: rental properties | prospect | 0.60 | **1.00** |
| T06 | Tom: accounts and payroll | prospect | 0.67 | **1.00** |
| T07 | Grace: can you start this week? | prospect | 0.89 | **1.00** |
| T08 | Siobhán: still waiting | admin | 1.00 | **no score** (the judge's answer couldn't be read) |
| T09 | Kevin: paying an invoice | admin | 1.00 | **1.00** |
| T10 | Lukas: income letter for the bank | admin | 1.00 | **1.00** |
| T11 | Ana: when is my return due? | admin | 1.00 | **0.83** |
| T12 | Fiona: send ROS login? | admin | 0.86 | **1.00** |
| T13 | Brian: new bank account | admin | 0.20 | **0.29** |
| T14 | Ioana: book a meeting with my accountant | admin | 0.00 | **0.17** |

## What the scores mean now

1. **Prospect replies are fully grounded (1.00).** In the first run, they looked weak only because the judge couldn't see the sender's email or the firm's details. Every price, the discovery call and the quote timing trace back to the fee guide.
2. ~~**T11 now scores 0.83, which matches what we know.** Its draft contains an invented online-filing date…~~ **Corrected 21 Oct:** the statement-by-statement test showed T11's only unsupported statement is the Revenue web link (added by code from the page's address), and the date is supported: Revenue's page says "extended to 18 November". See `eval/ragas-explain-21-oct.md`.
3. **T13 and T14 are real findings, not judge errors.** Reading the drafts:
   - **T13 (Brian):** "Please send us the new account details so we can update our records." That's a reasonable answer, but no firm document describes this process, so the model invented the procedure.
   - **T14 (Ioana):** "I can arrange a meeting with your accountant, Ciarán Doyle, to go through your tax return next week… I will coordinate with Ciarán." Ciarán is correct (client record), but the promise of a meeting **next week** isn't backed by anything. The model committed the firm to availability it can't know.

   Our rule-based fact check can't catch these, because they contain no amounts or dates to check. This is exactly where an AI judge adds value.
4. **Context relevance is still 1.00 everywhere,** so it doesn't distinguish good retrieval from bad here. Our own retrieval check (the right source found for 15/15 drafted replies) is more informative.

## What to do about T13 and T14 (not done yet)

- **Fill the knowledge gap:** add the firm's real process for bank-detail changes and appointment booking to the FAQ, so the model has a source to follow.
- **Prompt rule:** don't promise times, availability or processes that aren't in the sources; say a member of the team will confirm.
- **Optionally,** add "promises availability" (for example "next week", "tomorrow", "I can arrange") to the wording check.
