# Lovable change request, 17 October 2026

Sent to the secure (server-side key) Lovable project as one message, after the pipeline changes on the same day. Paste everything between the lines.

---

Please make these changes to the email review screen. Keep the API key server-side only, exactly as now, and don't change anything else.

1. **Suggested attachments.** Each email may now have `suggested_attachments`, a list of objects:
   - `kind: "attachment"` with `title`, `file_name` and `view_url`
   - `kind: "link"` with `title` and `url`

   Under the draft, above the Approve button, add a section **"Attachments and links"**, shown only when the list isn't empty:
   - For each attachment: an **unticked checkbox**, the title, the file name in grey, and a small **"View"** link that opens `view_url` in a new tab.
   - For each link: the title as a link to `url` (new tab), with a grey note "Included in the email".
   - Under the section, in small grey text: "Suggested from the sources this reply uses. Nothing is attached unless you tick it."

2. **Send the ticked attachments with the decision.** When the reviewer clicks Approve, or Save edit & approve, include `"attachments": [titles of the ticked items]` in the POST body to `/emails/{id}/decision`. After approval, show "Attached: <titles>" (from `final_attachments`) under the final text, or "No attachments" if the list is empty.

3. **Sources box.** If `retrieved` is empty and the email has a checklist, replace the "Sources used (0)" box with one grey line: "Reply built from the client's checklist using a fixed template. No sources used." If `retrieved` is empty and there's no checklist, hide the box.

4. **Wording warning.** If `wording_check` is not empty, show an amber notice above the draft: "Check the wording before approving:" followed by each item as `"<text>" (<issue>)`. Example: `"As outlined in our fee guide" (internal reference)`. Show it like the existing unsupported-facts warning, but don't block approval.

5. **Flags.** Show the new flag `wording` as an amber chip "Wording", like the other flags.
