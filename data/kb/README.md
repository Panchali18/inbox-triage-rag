# Knowledge base source documents

These are the human-readable copies of the knowledge base documents. Each one starts with a banner ("synthetic data" or the Revenue attribution) and, for past replies and Revenue pages, a header table.

| Folder | Files | Contents |
|---|---|---|
| `firm/` | 4 | Services and fees, engagement terms, onboarding and records checklists, FAQ (synthetic) |
| `past-replies/` | 20 | Past replies from the firm (synthetic) |
| `revenue/` | 9 | revenue.ie pages, saved as text under CC BY 4.0 (see `revenue/README.md`) |

**These files are not uploaded to the knowledge base directly.** Run `python3 scripts/build_kb_upload.py` to create `kb-upload/`. That folder holds the same text without the banners and header tables, plus a `.metadata.json` file for each document. In testing, the repeated banners weakened search results, so they now live in metadata instead. See the build log for day 2.
