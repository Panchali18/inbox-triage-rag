# Evaluation run 2: after the first fixes (15 Oct 2026, 10:27 UTC)

Changes since run 1:
- newsletters are classified as spam
- a client's attachments are always logged, even when the email also asks something
- the consultation offer is a template, with the fee read from the fee guide

| Metric | Run 1 | Run 2 | Target |
|---|---|---|---|
| Classification accuracy | 35/40 (88%) | **36/40 (90%)** | at least 90% |
| Urgent-item recall | 5/5 | 5/5 | 100% |
| False urgent | 0 | 0 | 0 |
| Advice detection recall | 8/8 | 8/8 | 100% |
| Advice questions answered to a client | 0 | 0 | 0 |
| Client lookup accuracy | 40/40 | 40/40 | 100% |
| Retrieval hit rate (all emails with expected sources) | 28/35 (80%) | 27/35 (77%) | at least 80% |
| Checklist matching accuracy | 6/7 | **7/7 (100%)** | 100% |
| Prompt injection caught, no draft | 1/1 | 1/1 | 100% |
| Drafts claiming identity verified | 0 | 0 | 0 |
| Unsupported facts flagged | 1 (T19 €150) | **0** | 0 |
| Calculated amounts flagged | 1 (T06 €104) | 2 (T04 €900 correct, T06 €104 wrong) | |
| Cost per email | $0.0013 | $0.0013 | |
| Latency per email (median / max) | 3.5 s / 6.6 s | 3.1 s / 9.0 s | under 29 s |

## Remaining misclassifications
T19, T35 and T40 are the judgement calls described in run 1. In each, the pipeline's action was still correct. **T29** is still classified as an advice question, but its files are now logged correctly, which was the real problem.

## Retrieval misses: what they show
Six of the eight misses are advice emails (T16–T22), where I'd expected `engagement-terms.md` (the "no advice by email" policy) to be retrieved. On reflection, that expectation was unnecessary. Advice emails never get a drafted reply. The no-advice rule is **enforced in code**, and retrieval only feeds the internal briefing note. The retrieved passages (VAT thresholds, registration and the fee guide) are relevant context for the accountant.

So run 3 reports a second, more meaningful measure: **retrieval hit rate for emails that get a drafted reply** (prospect and admin questions). In run 2, that was 14/15. The only miss was T07, which retrieved the past reply listing the onboarding documents rather than the checklist itself.

The original metric is kept, unchanged, alongside the new one.

## T06: €104, a real risk the fact check exposes
The draft added the €40 monthly payroll fee to 8 × €8 per-run fees, mixing a monthly charge with a per-run charge. The fact check marked it as "calculated", which only means the sum is arithmetically derivable from the sources, not that it's right. **Fix for run 3:** the draft prompt now forbids adding or combining prices. Each listed price is quoted separately, and the fixed-fee quote follows the discovery call.
