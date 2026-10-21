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

**T01:** of the six ✗ in the documents-only check, four were facts from Liam's own email ("Liam is a self-employed plumber", "has been trading for 3 years", "maintains his records in a spreadsheet", "inquired about the cost") and two described the reply ("Sinéad responded to Liam's inquiry", "Sinéad thanked Liam…"). ~~With his email included, everything was supported.~~ Every price and the discovery-call details were ✓ in both checks. **(Corrected 21 Oct, later the same day:** an earlier version said "With his email included, everything was supported". Re-reading the screenshots showed that the full-context check split the reply into its own 9 lines, and none of the six statements marked ✗ in the first check appeared in it, so they were never checked against his email. Some ✓ reasons in that check were also untrue: "The context includes a reply to Liam Foley, starting with 'Hi Liam,'". No such reply was in the material; "Hi Liam" appears nowhere in the knowledge base or test data, and Liam's email starts "Hi,".)

**T11:** the only ✗, in both checks, was "Revenue's guidance can be read here: https://www.revenue.ie/…". That link is added by our code from the page's web address, which isn't part of the page text. "If the tax return is filed through ROS, the deadline is extended to 18 November 2026" was ✓, quoting Revenue's page: "When you pay and file through the Revenue Online Service (ROS), the 31 October deadline is extended to 18 November."

**T14:** almost every statement was marked unsupported, with reasons such as "It only includes Ioana's email". **A follow-up check (printing the retrieved passages) showed the firm's FAQ answer was in the material:** "10. How do I book a meeting? Reply to any email from us or contact Sinéad Kehoe, our practice manager." The full-context material also included the client record naming Ciarán Doyle as her accountant. So the reply's offer to arrange the meeting through the practice manager, with her accountant, is supported. Only "next week" has no source. Pleasantries ("Sinéad Kehoe thanked Ioana", "sent kind regards") were also counted as unsupported. (An earlier version of this page said "No firm document describes booking meetings". That was wrong.)

**T13 (checked the same way):** Brian's reply ("Please send us the new account details so we can update our records") matches FAQ Q13 ("I've changed address or bank details. What do I do? Email us with the new details…"), which was among his retrieved passages. It scored 0.29 in the second RAGAS run.

## Findings

1. **The score changed, but this test can't say why.** Liam's reply scored 0.54 with documents only and 1.00 with full context. Two things changed between the checks: the material, and how the reply was split into statements (the six ✗ statements didn't appear in the second split). So the jump can't be credited to the added context. Giving the checker everything the drafting model had is still the right setup, because it can only confirm what it can see. (Corrected 21 Oct; an earlier version said "What the checker sees decides the score".)
2. **The same reply is split differently from one call to the next.** Liam's reply became 13 statements in one call and 9 in the other; Ioana's became 6 and 7. Greetings and sign-offs were counted as statements in one call only. So the score can move even when nothing else changes. (Checked in the RAGAS 0.2.15 code: the statements are built from only the email and the reply, which were identical in both calls.)
3. **A ✗ isn't always an error.** T11's only ✗ was a correct link. T14's ✗s include statements the FAQ supports, and pleasantries; only "next week" is a real gap.
4. **A ✓ isn't always right either.** Some ✓ verdicts gave reasons quoting text that wasn't in the material (see T01).
5. **The checker can miss evidence in front of it.** For T14 and T13, the FAQ answer was in the material, yet the replies scored 0.14 and 0.29.
6. **Correction:** "18 November 2026" (T11) was described as an "invented date" in earlier reports. It isn't: Revenue's page gives "18 November" without a year, and the model added 2026 from the page's 2026 example. The rule-based fact check flags it because it requires the year, which is a fair caution. But a flag means "can't verify", not "invented".

## Limits
Three emails, one checker model, one run each way. This shows how the score is built and how it can mislead; it doesn't measure how often.
