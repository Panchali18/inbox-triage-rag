# RAGAS scores, first run (US-15, AC4), 17 Oct 2026

**Judge:** Amazon Nova Pro on Bedrock (`eu.amazon.nova-pro-v1:0`, EU inference profile). It's larger than the model that wrote the drafts (Nova 2 Lite), but from the same family.
**Data:** the 13 AI-written replies from evaluation run 6. Templates, blocked drafts and internal briefing notes are excluded.
**Software:** RAGAS 0.2.15, `scripts/run_ragas.py`.

## Results

| Metric | Average | What it measures |
|---|---|---|
| Faithfulness | **0.71** | Share of the reply's claims that the retrieved passages support (1.00 = all supported) |
| Context relevance | **1.00** | How relevant the retrieved passages are to the sender's email |

| ID | Email | Type | Faithfulness | Context relevance |
|---|---|---|---|---|
| T01 | Liam: price for a tax return | prospect | 0.38 | 1.00 |
| T02 | Chiara: new bakery company | prospect | 0.67 | 1.00 |
| T03 | David: "do you do accounts? how much" | prospect | 0.89 | 1.00 |
| T04 | Aisha: rental properties | prospect | 0.60 | 1.00 |
| T06 | Tom: accounts and payroll | prospect | 0.67 | 1.00 |
| T07 | Grace: can you start this week? | prospect | 0.89 | 1.00 |
| T08 | Siobhán: still waiting | admin | 1.00 | 1.00 |
| T09 | Kevin: paying an invoice | admin | 1.00 | 1.00 |
| T10 | Lukas: income letter for the bank | admin | 1.00 | 1.00 |
| T11 | Ana: when is my return due? | admin | 1.00 | 1.00 |
| T12 | Fiona: send ROS login? | admin | 0.86 | 1.00 |
| T13 | Brian: new bank account | admin | 0.20 | 1.00 |
| T14 | Ioana: book a meeting with my accountant | admin | 0.00 | 1.00 |

## First reading (not conclusions yet)

These scores don't line up with what we know from reading the drafts and the rule-based fact check, so they need checking before anyone quotes them.

1. ~~**T11 scored 1.00**, but its draft contains an invented date ("18 November 2026"), which our fact check flagged. The judge missed a made-up fact.~~ **Corrected 21 Oct:** the date is in Revenue's page ("extended to 18 November", without a year). The fact check flagged it because the year couldn't be verified. The judge's 1.00 was reasonable. See `eval/ragas-explain-21-oct.md`.
2. **T14 scored 0.00 and T13 0.20.** Both are simple admin replies. (21 Oct: both replies follow the firm's FAQ, which was among the retrieved passages; see `eval/ragas-explain-21-oct.md`.) The likely cause is that the judge was only given the retrieved passages, not the **client record**. A reply saying "your accountant, Ciarán Doyle, will be in touch" is correct, because it comes from the client record, but to the judge it looks unsupported.
3. **The prospect replies (T01–T07) score lower** than the admin replies. Possible causes: the code-inserted discovery-call and price lines, friendly sentences ("thanks for getting in touch about your tax return") counted as claims, or the sender's own facts repeated back. We need to read the judge's claim-by-claim verdicts to know.
4. **Context relevance is 1.00 for every email.** A perfect score everywhere usually means the metric isn't discriminating. The judge may be too lenient, or the metric's coarse scale (it rates on 0–2 and averages) saturates. Our own retrieval check is more informative: the right source was found for 15/15 drafted replies.

## Next step

Re-run with the client record and the sender's email added to what the judge sees, since the drafting model had both. Then read the claims behind the lowest scores before drawing conclusions.
