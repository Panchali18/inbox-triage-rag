# Lovable prompt (front end)

**Version 1.** This is the prompt used to generate the first version of the front end in Lovable. A follow-up prompt for the agreed redesign (US-18 to US-20 in `scope.md`: routing, personal mailboxes, clean draft, client context panel) will be added below once it's written. The API key is replaced with a placeholder here. The real key goes only into the Lovable project.

---

Build a single-page React + TypeScript + Tailwind app called **"Nore Valley Inbox Triage"**. It's a review console for staff at a small accounting practice. An AI pipeline has already triaged each email. Staff review the result and approve, edit or reject drafts. **Nothing is ever sent.**

## Demo banner (always visible, top of page)
"Demonstration only. Fictional firm, synthetic data. No email is ever sent."

## API
- Base URL: `https://2ly8qg1zrc.execute-api.eu-north-1.amazonaws.com/prod`
- Every request needs the header `x-api-key: YOUR_API_KEY`, plus `Content-Type: application/json` for POST.
- Put the URL and key in one config file (`src/config.ts`).
- No authentication or backend is needed. Call the API directly from the browser (CORS is enabled).

Endpoints:
1. `GET /emails` returns an array of email records, already sorted urgent-first.
2. `POST /emails` takes `{from_email, from_name, subject, body, attachments: string[]}`. It runs the AI pipeline (this takes 3–10 seconds) and returns the new record.
3. `GET /emails/{email_id}` returns one record.
4. `POST /emails/{email_id}/decision` takes `{decision: "approve" | "edit" | "reject", edited_draft?: string, reason?: string, override?: boolean}` and returns the updated record.
   - Returns **409** with `{error, unsupported: string[]}` when approving a draft with unsupported facts and no override.
   - Returns **400** if rejecting without a reason.
5. `GET /test-emails` returns 40 example emails `{id, from_email, from_name, subject, body, attachments}` for the "Load example" picker.

An email record has these fields (some can be null):
```
email_id, received_at, from_email, from_name, subject, body, attachments[],
status        // "urgent_for_accountant" | "needs_human_triage" | "blocked_by_guardrail" | "for_accountant" |
              // "awaiting_review" | "filed" | "approved (not sent - demo)" | "rejected"
action        // short text, e.g. "draft reply", "briefing note", "documents logged", "filed"
urgency       // "high" | "normal" | "low"
flags[]       // any of "advice", "injection", "phishing", "low_confidence", "unsupported_facts", "guardrail"
assigned_to
classification: { type, confidence (0-1), reason, extracted: { request_summary, deadline, dates_mentioned[] } }
   // type is one of prospect, admin_question, advice_question, documents_sent, revenue_or_penalty, spam_or_supplier
client: { client_id, name, assigned_accountant, partner } | null     // null = unknown sender
retrieved: [{ ref: "S1", source: "firm/services-and-fees.md", score, url }]   // url only for revenue.ie pages
draft          // client-facing draft (may contain tags like [S1] [S3])
briefing_note  // internal note for the accountant
checklist: { matched[], still_outstanding[], unmatched[] } | null
fact_check: { supported[], calculated[], unsupported[] } | null
usage: { calls, input_tokens, output_tokens, cost_usd }, latency_ms
history: [{ at, event, status, reason?, override? }]
```

## Layout
**Header:** the app name, then small stat chips computed from `GET /emails`: total emails, urgent, awaiting review, average cost per email (from `usage.cost_usd`, shown in cents with 2 decimals) and average latency in seconds. Add a **"New email"** button and a refresh button.

**Left: the queue.** Tabs: **Queue** (everything except filed, approved and rejected), **Filed**, **Done** (approved or rejected). Each row shows:
- an urgency stripe (red for high)
- the sender name, and a client badge (the client name) or an "Unknown sender" badge
- the subject
- a type chip
- a status chip
- flag icons: advice ⚖️, injection 🛡️, phishing 🎣, unsupported facts ⚠️
- the received time

Keep the API's order (urgent first).

**Right: the detail panel for the selected email.**
1. **Email:** from, subject, body, and attachments as file chips.
2. **AI triage:** type, confidence as a percentage, the reason, urgency, any deadline (highlighted in red if present), the assigned person, and the action.
3. **Client:** name, ID and accountant, or "Not a client".
4. **Flags:** explain each one in plain English, for example:
   - "Advice question: no client answer is drafted; a briefing note goes to the accountant."
   - "Possible prompt injection: no action taken."
5. **Checklist** (if present): green ticks for matched, amber for still outstanding, grey for unmatched files.
6. **Briefing note** (if present): in a muted "Internal: not for the client" box.
7. **Draft reply** (if present):
   - in an editable textarea, behind an "Edit" toggle
   - render `[S1]` tags as small superscript badges; hovering shows the source file name
   - **highlight every string from `fact_check.unsupported` in red, and `fact_check.calculated` in amber**, with a legend: "Red = not found in any source. Amber = calculated, check the maths."
8. **Sources:** a list of the `retrieved` items: the ref, a friendly file name and the score. If `url` exists, link "revenue.ie" (open in a new tab) and add "Information provided courtesy of the Revenue Commissioners under CC BY 4.0".
9. **Decision buttons:** Approve, Save edit & approve, Reject (asks for a reason).
   - On a 409 response, show a dialog listing the unsupported facts, with "Edit draft" and "Approve anyway (override, logged)" (which resends with `override: true`).
   - After any decision, refresh the record and show a toast.
   - Approve labels the result "Approved (not sent – demo)".
10. **History:** the timeline from `history`.
11. **Footer line:** "Cost {cost in cents} · {latency in seconds} · {calls} model calls".

**"New email" dialog:**
- fields: from name, from email, subject, body, and attachments (comma-separated file names)
- a **"Load example"** dropdown filled from `GET /test-emails` (show `id — from_name: subject`) that fills the form
- on Submit, show a "Triaging… (usually 3–10 seconds)" state with a spinner, then select the new record in the queue
- show any API error message clearly

## Style
A calm, professional internal tool:
- off-white background, white cards, slate text, one teal accent
- red only for urgent and unsupported items, amber for warnings
- Inter font, compact density, rounded-lg corners, subtle borders and no heavy shadows
- responsive: on narrow screens the detail panel becomes a full-screen sheet

Status chip colours:
- urgent: red
- needs triage or blocked: orange
- for accountant: violet
- awaiting review: blue
- filed: grey
- approved: green
- rejected: dark grey

Handle loading and empty states ("No emails yet — click New email or load an example").
