# Lovable prompt, version 2 (complete, for a fresh project)

A single prompt that builds the current design: shared inbox, routing to personal mailboxes, a clean draft and a client context panel (user stories US-13 and US-18 to US-20). The API key is a placeholder. After Lovable builds the app, send the follow-up: "In src/config.ts, set the API key to: <your key>".

---

Build a single-page React + TypeScript + Tailwind app called **"Nore Valley Inbox Triage"**. It's the review console for the shared inbox of a small accounting practice.

**How it works:** every email lands in the **Shared inbox**. An AI pipeline has already triaged it (type, urgency, client lookup, draft or internal note) and **routed it to one person's mailbox**. That person reviews it and approves, edits or rejects. **Nothing is ever sent.**

## Demo banner (always visible, top of page)
"Demonstration only. Fictional firm, synthetic data. No email is ever sent."

## API
- Base URL: `https://2ly8qg1zrc.execute-api.eu-north-1.amazonaws.com/prod`
- Every request needs the header `x-api-key: YOUR_API_KEY`, plus `Content-Type: application/json` for POST.
- Put the URL and key in one file, `src/config.ts`.
- Call the API directly from the browser (CORS is enabled). No backend or auth is needed.

Endpoints:
1. `GET /emails` returns all email records, sorted urgent-first. Optional query parameters:
   - `?assigned_to=Name`
   - `?from_email=address` returns that sender's emails, newest first
2. `POST /emails` takes `{from_email, from_name, subject, body, attachments: string[]}`. It runs the AI pipeline (3–10 seconds) and returns the new record.
3. `GET /emails/{email_id}` returns one record.
4. `POST /emails/{email_id}/decision` takes `{decision: "approve" | "edit" | "reject", edited_draft?: string, reason?: string, override?: boolean}` and returns the updated record.
   - Returns **409** with `{error, unsupported: string[]}` when approving a draft with unsupported facts and no override.
   - Returns **400** if rejecting without a reason.
5. `GET /test-emails` returns 40 example emails `{id, from_email, from_name, subject, body, attachments}`.

Email record fields (any can be null):
```
email_id, received_at, from_email, from_name, subject, body, attachments[],
status        // "urgent_for_accountant" | "needs_human_triage" | "blocked_by_guardrail" | "for_accountant" |
              // "awaiting_review" | "filed" | "approved (not sent - demo)" | "rejected"
action, urgency ("high" | "normal" | "low"),
flags[]       // any of "advice", "injection", "phishing", "low_confidence", "unsupported_facts", "guardrail"
assigned_to   // staff name, or null = filed
routing_reason
classification: { type, confidence (0-1), reason, extracted: { request_summary, deadline, dates_mentioned[] } }
   // type: prospect | admin_question | advice_question | documents_sent | revenue_or_penalty | spam_or_supplier
client: { client_id, name, client_type, business_name, business_activity, services[], assigned_accountant,
          partner, onboarding_status, outstanding[] } | null      // null = not a client
retrieved: [{ ref, source, score, url, snippet }]   // url only for revenue.ie pages
draft          // clean client-facing draft, plain text, no tags
briefing_note  // internal note for the accountant
checklist: { matched[], still_outstanding[], unmatched[] } | null
fact_check: { supported[], calculated[], unsupported[] } | null
usage: { calls, input_tokens, output_tokens, cost_usd }, latency_ms
history: [{ at, event, status, reason?, override? }]
final_client_text   // present after approval
```

## Layout

**Header:**
- the app name
- stat chips computed from `GET /emails`:
  - Total
  - Urgent
  - Awaiting review
  - Avg cost per email (from `usage.cost_usd`, in cents with 2 decimals)
  - Avg latency (seconds)
  - **Avg time to decision**: for records with a history event of approve, edit or reject, the time between `received_at` and that event's `at`, averaged, in minutes
- a **"New email"** button and a refresh button

**Left column:**
- **Mailbox dropdown** at the top, with these options:
  - **Shared inbox** (all emails, the default)
  - Sinéad Kehoe (Practice Manager)
  - Ciarán Doyle (Accountant)
  - Niamh Rowe (Accountant)
  - Declan Furlong (Partner)
  - Aoife Gallagher (Partner)

  Show a count next to each option. Selecting a person shows only records whose `assigned_to` equals that name. Remember the selection in localStorage, inside a try/catch.
- **Tabs:**
  - **Queue:** everything except filed, approved and rejected
  - **Filed:** status "filed" or `assigned_to` null
  - **Done:** approved or rejected
- **Queue row:**
  - a red urgency stripe for high urgency
  - the sender name
  - a client badge with the client name, or "Unknown sender"
  - the subject
  - a type chip and a status chip
  - a small "→ {assigned_to}" label, or "Filed"
  - flag icons: advice ⚖️, injection 🛡️, phishing 🎣, unsupported facts ⚠️
  - the received time

  Keep the API order.

**Detail panel:** two columns on wide screens. On narrow screens, the client column moves above the draft, and the whole panel is a full-screen sheet.

*Main column, in this order:*
1. **Email:** from, subject, body and attachment chips.
2. **Routing line:**
   - "Routed to **{assigned_to}**", with `routing_reason` in small muted text underneath
   - a type chip and a confidence percentage
   - urgency, and any deadline (`classification.extracted.deadline`) shown in red
3. **Warnings, only if there are any:**
   - For each item in `fact_check.unsupported`, a red alert: "**{item}** isn't in any of the firm's documents. Check before approving."
   - For each item in `fact_check.calculated`, an amber alert: "**{item}** was calculated by the AI. Check the maths."
   - Plain-English alerts for these flags:
     - **injection:** "This email tried to give instructions to the system. No action was taken."
     - **phishing:** "Looks like phishing. Don't click links."
     - **low_confidence:** "The AI wasn't sure how to classify this. Please check."
     - **guardrail:** "The safety filter blocked the draft."
     - **advice:** "Advice question: no answer is drafted for the client; a briefing note goes to the accountant."
   - If there are no warnings, show **nothing**.
4. **Draft reply** (if `draft` exists): render it as a clean email in plain text with line breaks. Below it:
   - **Edit**, which turns it into a textarea, and **Save edit & approve**
   - **Approve**
   - **Reject**, which asks for a reason

   On a 409 response, show a dialog listing the unsupported facts, with "Edit draft" and "Approve anyway (override, logged)" (which resends with `override: true`). After a decision, refresh and show a toast. Approved items show "Approved (not sent – demo)" and the `final_client_text`.
5. **Briefing note** (if present): in a muted box labelled "Internal: not for the client".
6. **Checklist** (if present): green ticks for matched, amber for still outstanding, grey for unmatched files.
7. **Sources used (n):** a **collapsed** section at the bottom, closed by default. For each `retrieved` item: a friendly file name (for example, "firm/faq.md" becomes "FAQ"), the score and the `snippet` in a small quote block. Where `url` exists, link "revenue.ie" (new tab) and add "Information provided courtesy of the Revenue Commissioners under CC BY 4.0".
8. **History** timeline, then a footer: "Cost {cents} · {seconds} · {calls} model calls".

*Side column: "Client":*
- If `client` exists, show a card with:
  - the name
  - business_name or business_activity
  - "Sole trader" or "Company"
  - services, as small chips
  - "Accountant: {assigned_accountant}"
  - "Partner: {partner}"
  - "Onboarding in progress" in amber, if `onboarding_status` is "in_progress"
  - **Outstanding:** the `client.outstanding` items in amber, or "Nothing outstanding" in green
- If `client` is null: "**Not a client.** Unknown sender ({from_email})".
- Below the card, **"Previous emails from this sender"**: from `GET /emails?from_email={from_email}`, excluding the current one. For each, show the date, subject, type chip and status chip. Clicking one opens it. If there are none, show "No previous emails."
- No AI-written explanations or summaries.

**"New email" dialog:**
- fields: from name, from email, subject, body, and attachments (comma-separated file names)
- a **"Load example"** dropdown from `GET /test-emails` (show "T01 — Liam Foley: Price for tax return") that fills the form
- on Submit, show "Triaging… (usually 3–10 seconds)" with a spinner, then select the new record
- show API errors clearly

## Style
A calm, professional internal tool:
- off-white background, white cards, slate text, one teal accent
- red only for urgent and unsupported items, amber for warnings
- Inter font, compact density, rounded-lg corners, subtle borders and no heavy shadows

Status chip colours:
- urgent: red
- needs triage or blocked: orange
- for accountant: violet
- awaiting review: blue
- filed: grey
- approved: green
- rejected: dark grey

Empty state: "No emails yet — click New email or load an example."
