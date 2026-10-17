# LinkedIn story bank: Inbox Triage with RAG

Raw material for the "AI Build" series. Each story gives what happened, the evidence in this repo, the numbers and the lesson. Write the posts in your own voice. Everything here is from synthetic data in a demonstration project, so say so in each post.

**Status:**
- Pipeline, API, guardrail and evaluation (5 runs): done.
- RAG vs prompt-stuffing comparison: done (`eval/rag-vs-stuffing.md`).
- Secure front end (key on the server): **pending**.

---

## Main post: what I built (use once the demo and recording are ready)

**The problem:** a five-person accounting practice in Ireland (fictional). Around tax deadlines, one shared inbox fills with:
- quote requests
- admin questions
- documents
- Revenue letters
- penalty notices

Urgent items get buried and prospects wait days.

**What I built:** an AI triage pipeline on AWS. It:
- classifies each email
- recognises the sender
- retrieves the firm's policies and Revenue guidance (RAG)
- routes the email to the right person's mailbox
- drafts a reply, which a human approves

It never gives tax advice: advice questions go to an accountant.

**TLDR in numbers** (run 5, 40 synthetic test emails, `eval/run-4-5-guardrail.md`):
- 92% classified correctly, and **100% routed to the right person**
- 100% of urgent Revenue items caught, and 100% of advice questions caught, none answered to a client
- 100% of drafted replies grounded in the right source
- 0 unflagged invented facts
- about **$0.0013 per email** (a tenth of a cent) and about 4 seconds

**Stack:**
- Amazon Bedrock: Knowledge Bases on S3 Vectors, Nova 2 Lite, Guardrails
- Lambda
- API Gateway
- DynamoDB
- Lovable (React)

**One learning:** pick one of the stories below.

**Link:** the GitHub repo.

---

## 1. "The region I couldn't choose"
- **What happened:** the brief said "all resources in Ireland". The AWS account turned out to be locked to Stockholm (a newer AWS "projects" setup), and every route to change it was blocked.
- **The decision:** stay in Stockholm. GDPR cares whether data stays in the EU, not in which EU country. A real deployment would still need a data processing agreement, a privacy notice, a DPIA, and a check of client contracts for any Ireland-only requirement.
- **Lesson:** data residency and GDPR compliance are different questions. Know which one a requirement is really asking.
- **Evidence:** `build-log.md`, day 1.

## 2. "The cheapest vector database decision I made"
- **What happened:** Bedrock's "quick create" suggested OpenSearch Serverless, which has an always-on minimum charge that would have used up $119 of credits within weeks. I chose S3 Vectors instead, which is pay-per-use and costs pennies at this scale.
- **The catch:** the console text still said "OpenSearch Serverless" after S3 Vectors was selected. Only the review page confirmed the real choice.
- **Lesson:** check the review page, not the wizard's description. Architecture choices are cost choices.
- **Evidence:** `build-log.md`, day 2, AWS.

## 3. "My knowledge base was full of disclaimers"
- **What happened:** every document started with the same "synthetic data" banner or licence line. The first search tests returned passages that were mostly identical boilerplate.
- **Fix:** keep only real content in the text, and move the labels into metadata files. After the fix, the right document came first.
- **Lesson:** repeated text weakens retrieval, because it makes different documents look alike. Test retrieval before you add a model on top.
- **Evidence:** `scripts/build_kb_upload.py`, `build-log.md` ("Boilerplate hurts retrieval").

## 4. "Public data isn't automatically free to use"
- **What happened:** before adding Revenue.ie pages, I checked the licence: CC BY 4.0-style, with attribution required, no logos, and no implied endorsement. I saved the pages myself as text, because an AI web tool returned summaries rather than exact wording, then checked each one word by word.
- **Lesson:** licence first, and never trust an AI summary as source text for a knowledge base.
- **Evidence:** `data/kb/revenue/README.md`.

## 5. "Write the answer key before you build"
- **What happened:** I wrote 40 test emails, each with its expected result (type, urgency, client, advice flag, sources, checklist), before any pipeline existed. They include traps: disguised advice, Revenue phishing, an identity-check question, and a prompt injection.
- **Lesson:** if you write expectations after seeing outputs, you'll accept whatever the system does.
- **Evidence:** `data/test-emails/README.md`.

## 6. "My test data was cheating"
- **What happened:** two test emails said "I'm not a client". Real senders never write that, and it handed the AI the answer the client lookup should have established. I rewrote them.
- **Lesson:** synthetic data must sound like real people, or your scores are inflated.
- **Evidence:** `build-log.md`, "Found by testing in the app".

## 7. "€150 or €120?"
- **What happened:** in the first evaluation, the AI quoted a consultation at **€150**. The fee guide says **€120**: the model had picked up the per-property landlord fee. The rule-based fact check flagged it before any human saw it.
- **Fix:** the consultation offer became a template, with the fee read from the fee guide.
- **Lesson:** where the answer never changes, use a template, not AI.
- **Evidence:** `eval/run-1-baseline.md`.

## 8. "Prompts are instructions, not guarantees"
- **What happened:** the prompt said "never give tax advice" and "never combine prices". In testing, the model still:
  - told a sole trader "you will need to register for Income Tax" (twice)
  - added payroll prices together (three times)
- **Fix:** enforce rules outside the prompt:
  - code (advice never gets a client answer)
  - a fact check
  - a Bedrock Guardrail on the outgoing draft
- **Lesson:** defence in depth. A rule that matters must be enforced, not just requested.
- **Evidence:** `eval/run-4-5-guardrail.md`, T05.

## 9. "My guardrail blocked a perfect quote"
- **What happened:** the first guardrail blocked 4 drafts. Reading each one:
  - **T05:** real advice.
  - **T11:** a deadline with the wrong year.
  - **T15:** a general rule applied to "you".
  - **T01:** a perfectly good quote.

  One of my sample phrases ("as a sole trader you must register…") sounded too much like normal business language.
- **Fix:** tighten the topic definition and the examples. After tuning, 2 blocks out of 22 drafts, both defensible.
- **Lesson:** measure a guardrail's false positives, not just its catches. Read every blocked output.
- **Evidence:** `eval/run-4-5-guardrail.md`.

## 10. "The block that found a different bug"
- **What happened:** one blocked draft gave Ana's tax return deadline as **31 October 2025**. Revenue's page says **2026**. The fact check had passed it, because it compared "31 October" without the year.
- **Fix:** the fact check now checks years.
- **Lesson:** safety layers overlap, and one layer's catch can reveal another layer's gap.
- **Evidence:** `eval/run-4-5-guardrail.md`.

## 11. "Inline citations belong in papers, not emails"
- **What happened:** drafts showed `[S1][S4]` source tags. Useful for checking, but they made an email read like a research paper.
- **The agreed design:**
  - a clean email in the middle
  - the client card and previous emails beside it
  - warnings only when a fact is wrong
  - sources collapsed for audit

  The tags are kept in the data, and never sent to a client.
- **Lesson:** keeping the data and choosing how to display it are separate decisions. Design for how the reviewer actually works.
- **Evidence:** `build-log.md`, "Decided (review experience)"; `frontend/lovable-prompt-v2.md`.

## 12. "Who owns this email?"
- **What happened:** the first version sent every email to the client's accountant, including "can I pay by card?". Writing out a routing table fixed it:
  - admin questions to the practice manager
  - advice, documents and Revenue letters to the accountant
  - unknown advice to a partner
  - spam filed

  Routing accuracy reached 100% on 40 emails.
- **Lesson:** in triage, routing is the product. Make it deterministic and testable, not an AI guess.
- **Evidence:** `scope.md` US-18, `eval/run-3-routing.md`.

## 13. "RAG vs pasting everything into the prompt"
- **What happened:** I ran the same 40 emails twice, with the same model and the same safety layers. One run gave the model the 5 most relevant passages (RAG). The other pasted in all 33 documents, about 10,000 tokens.
- **Results:**
  - Facts in drafts found in a source: **97% with RAG, 89% with everything in the prompt**.
  - With everything in the prompt, one reply gave two deadlines with the wrong year (2025 instead of 2026), and a plain quote drifted into wording the guardrail blocked as advice.
  - RAG used **4× fewer input tokens** and cost **2.4× less** per email.
  - Speed was the same: 2.6 seconds each.
- **The honest caveat:** with only 33 documents, pasting everything still works and costs a third of a cent. RAG's advantage grows with the knowledge base, because a real firm's thousands of documents won't fit in a prompt.
- **Lesson:** more context isn't better context. Giving the model only what's relevant made it more accurate as well as cheaper. And test your architecture choice, don't assume it.
- **Evidence:** `eval/rag-vs-stuffing.md`.

## 14. "An internal note can give advice too"
- **What happened:** the briefing note for a partner concluded that a jewellery seller was "not required to register for VAT", using the **services** threshold (€42,500) for someone selling **goods** (€85,000).
- **Fix:** notes state the sender's facts and quote the guidance verbatim, but never reach a conclusion.
- **Lesson:** staff trust internal AI notes. A wrong conclusion there is as risky as one in a client email.
- **Evidence:** `build-log.md`, "Found by testing in the app".

## 15. "Throttled at demo scale"
- **What happened:** one email in an evaluation run failed with a Bedrock `ThrottlingException`. New accounts have low model quotas.
- **Fix:** adaptive retries with backoff on every call, plus slower pacing.
- **Lesson:** production concerns show up even in a demo. Build for quotas from day one.
- **Evidence:** `eval/run-3-routing.md`.

## 16. "The AI picks the price, code writes it"
- **What happened:** the model kept getting quotes subtly wrong. It combined payroll prices into totals (three runs out of three), and told a prospect "this would be the relevant fee for your situation" before anyone had seen his records. Prompt rules against both were ignored.
- **First fix failed:** I asked the model to place a placeholder where the prices go. It put it mid-sentence and three times over, and still wrote its own prices.
- **Fix that worked:** a separate small call only picks which rows of the fee guide apply (a short list), and code inserts those rows word for word. The draft model is told to write no prices, and any it still writes are flagged.
- **Lesson:** for anything that must be exact, let the AI select and let code write. Keep the model for the wording around the facts.
- **Evidence:** `pipeline/triage.py` (`price_list`, `draft_reply`), `build-log.md` day 3.

## 17. "Suggest, don't attach"
- **What happened:** I asked whether the reply could include the documents it was based on. Most sources can't be shared: past replies contain other clients' details, and the onboarding checklist describes internal checks.
- **Design:** only client-facing documents the draft actually cites are suggested, as unticked boxes. Revenue pages are public, so they go in as links. The reviewer decides, and the approval records the choice.
- **Lesson:** retrieval doesn't know what's confidential. Sharing rules need to be designed separately from search.
- **Evidence:** `scope.md` US-21, `build-log.md` day 3.

## 18. "Right facts, wrong reply"
- **What happened:** a quote passed the fact check, because every number was in the fee guide. But it said "As outlined in our fee guide…" to a stranger, and promised him the cheapest price based on one sentence.
- **Fix:** a wording check that flags internal references and price judgements, alongside the fact check.
- **Lesson:** grounded isn't the same as appropriate. Check tone and commitments, not only facts.
- **Evidence:** `pipeline/triage.py` (`wording_check`), `build-log.md` day 3.

## 19. "Sources found isn't sources used"
- **What happened:** the review screen said "Sources used (4)" for a quote. Looking closer: 1 passage supplied the prices, 1 (a past reply) the tone, and 2 weren't used at all. The most useful source, the fee guide, ranked third by similarity.
- **Lesson:** RAG screens show what the search returned, not what the answer relied on. Similarity scores rank passages; they're not percentages.
- **Evidence:** `build-log.md` day 3, "Learned".

---

## Numbers you can quote (all synthetic, run 5 unless stated)

| Measure | Value |
|---|---|
| Test emails | 40 labelled, written before the build |
| Classification accuracy | 92% (run 1: 88%) |
| Routing accuracy | 100% |
| Urgent Revenue items caught | 100% (5/5) |
| Advice questions caught | 100% (8/8), 0 answered to a client |
| Retrieval hit rate, drafted replies | 100% (15/15) |
| Prompt injection caught | 100% (1/1) |
| Guardrail blocks | 2 of 22 drafts (run 4, before tuning: 4) |
| Cost per email | about $0.0013 |
| Median time per email | about 3–4 seconds |
| Evaluation runs | 5, each change measured and documented |
| RAG vs everything in the prompt | 97% vs 89% of facts grounded; 4× fewer input tokens; 2.4× cheaper; same speed (2.6 s) |
| Knowledge base | 4 firm documents, 20 past replies, 9 Revenue pages (CC BY 4.0) |

## Wording reminders
- Say "synthetic data" and "demonstration only" in every post.
- Don't name Revenue as a partner or endorser. "Uses public Revenue.ie guidance under CC BY 4.0" is fine.
- Don't call unfinished items done: the secure front end is still pending.
