# Lovable changes for the public demo (21 Oct 2026)

All changes are front end only. The API proxy, the server function that calls the API and the `TRIAGE_API_KEY` secret were not changed.

## Why
The app has one shared inbox. Once the link is public, every visitor would see every other visitor's test emails, and one visitor approving a draft would move it to Done for everyone.

## Changes
1. **Showcase list.** A config constant `SHOWCASE_EMAIL_IDS` lists 11 emails: Olena Shevchenko, Brian Walsh, Adaeze Okafor, Rahul Mehta, Aisha Khan, Kevin Brady, Ana García, Tax News Weekly, Tom Hennessy, Chiara Romano and Liam Foley. Ioana Popescu's email is left out (see the build log, day 4).
2. **Own submissions.** Emails a visitor submits are saved by ID in their browser (localStorage) and shown only to them.
3. **Local decisions on showcase emails.** Showcase emails always show in the Queue as awaiting review. Approve, Edit and Reject on them change only that visitor's view.
4. **Queue order.** Emails with a draft reply come first (Liam, Chiara, Tom, Aisha, Kevin, Ana), then those routed to an accountant.
5. **Opens on a draft.** Lovable was asked to open Aisha Khan's email on load, so visitors see a drafted reply first.
6. **Counters** are calculated from the visible emails only.
7. **Bold text** in internal notes renders as bold instead of showing `**`.
8. **Sender name required** in the New email form.

## Checked
- The live link opens with all showcase emails in a private window.
- No `x-api-key` header on the request that loads the inbox.
- A test email appeared in the window it was sent from.
