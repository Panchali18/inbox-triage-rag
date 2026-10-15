# Client lookup table (synthetic)

**Synthetic data, demonstration only.** All 15 clients are fictional. Emails use the reserved `example.com` domain, so no real address can be reached.

The pipeline checks this table, not the knowledge base. It looks up the sender's email (the DynamoDB partition key) and answers four questions: is this an existing client, which services do they have, who is their accountant, and what is still outstanding?

## Fields

| Field | Meaning |
|---|---|
| `email` | Partition key. The sender's email address. |
| `client_id` | Internal ID, `C001` to `C015` |
| `client_type` | `sole_trader` or `company` |
| `business_name` | Company name (companies only) |
| `services` | `form11`, `vat`, `payroll`, `company_accounts`, `bookkeeping_monthly`, `landlord_rental` |
| `assigned_accountant` / `partner` | Who owns the relationship |
| `year_end` | Company financial year end, as `MM-DD` |
| `records_deadline` | When annual records are due, as set out in the engagement terms |
| `onboarding_status` | `complete` or `in_progress`. Only a partner can mark identity verification complete. |
| `onboarding_checklist` / `annual_checklist` | Checklist code mapped to `received` or `outstanding`. Codes match `data/kb/firm/onboarding-checklist.md`. |
| `notes` | Short history. Matches the past replies. |

## Test cases built in

| Client | Situation | What it tests |
|---|---|---|
| C010 Wojciech Nowak | Expenses and motor log outstanding | Documents email: match the files, list what's still missing |
| C011 Eoin Byrne | No records at all, past the deadline | Chasing, late-records charge |
| C007 Joe Dunne | Two items outstanding, late | Partial documents |
| C013 Marta Silva | Onboarding in progress | Must never say identity is verified |
| C014 Adaeze Okafor | Company, payroll and loans outstanding | Company checklist codes |
| C015 Olena Shevchenko | Company, stock valuation outstanding | Company with a June year end |
| C012 Sarah Chen | Earlier Revenue compliance letter | Revenue or penalty routing |
| C009 Rahul Mehta | Earlier advice question | Advice detection |

Any sender not in this table is treated as `unknown`.
