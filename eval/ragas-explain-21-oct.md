# Faithfulness, statement by statement (21 Oct 2026)

**Why:** to see how RAGAS faithfulness is actually worked out, instead of trusting the number. `scripts/ragas_explain.py` runs the two steps RAGAS uses and prints them:
1. split the reply into statements;
2. check each statement against the material given (✓ supported, ✗ not supported, with a reason).

**Score = ✓ ÷ all statements.**

Each email was checked twice, with the drafts from evaluation run 7. Checker: Amazon Nova Pro (`eu.amazon.nova-pro-v1:0`).
- **Documents only:** the retrieved passages (the first, flawed setup).
- **Full context:** the passages, plus the sender's email, the client record and the firm's details (the fix).

## Results

| Email | Documents only | Full context |
|---|---|---|
| **T01 Liam:** price for a tax return (a correct reply) | 7/13 = **0.54** | 9/9 = **1.00** |
| **T11 Ana:** when is my return due? | 5/6 = **0.83** | 5/6 = **0.83** |
| **T14 Ioana:** book a meeting with my accountant | 0/6 = **0.00** | 1/7 = **0.14** |

## What the statements showed

**T01:** all six ✗ in the documents-only check were about Liam's own email: "Liam is a self-employed plumber", "has been trading for 3 years", "maintains his records in a spreadsheet", "inquired about the cost", and the reply's framing ("Sinéad thanked Liam…"). With his email included, everything was supported. Every price and the discovery-call details were ✓ in both checks.

**T11:** the only ✗, in both checks, was "Revenue's guidance can be read here: https://www.revenue.ie/…". That link is added by our code from the page's web address, which isn't part of the page text. "If the tax return is filed through ROS, the deadline is extended to 18 November 2026" was ✓, quoting Revenue's page: "When you pay and file through the Revenue Online Service (ROS), the 31 October deadline is extended to 18 November."

**T14:** the promises are genuinely unsupported: "I can arrange a meeting with your accountant… next week" and "I will coordinate with Ciarán". No firm document describes booking meetings. But pleasantries were also counted as unsupported statements ("Sinéad Kehoe thanked Ioana", "sent kind regards"), which pushes the score down further.

## Findings

1. **What the checker sees decides the score.** Liam's correct reply went from 0.54 to 1.00 when his own email was included.
2. **The same reply is split differently from one call to the next.** Liam's reply became 13 statements in one call and 9 in the other; Ioana's became 6 and 7. Greetings and sign-offs were counted as statements in one call only. So the score can move even when nothing else changes.
3. **A ✗ isn't always an error.** T11's only ✗ was a correct link; T14's mix a real problem with pleasantries.
4. **Correction:** "18 November 2026" (T11) was described as an "invented date" in earlier reports. It isn't: Revenue's page gives "18 November" without a year, and the model added 2026 from the page's 2026 example. The rule-based fact check flags it because it requires the year, which is a fair caution. But a flag means "can't verify", not "invented".

## Limits
Three emails, one checker model, one run each way. This shows how the score is built and how it can mislead; it doesn't measure how often.
