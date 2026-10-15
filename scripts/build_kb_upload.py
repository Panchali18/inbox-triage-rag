"""Build clean Knowledge Base files from data/kb/.

The repo copies in data/kb/ keep their banners, attribution and header tables
so people reading GitHub see them. For the Knowledge Base we:
  - strip the repeated banner / attribution lines and header tables from the text
  - move those labels into a <file>.metadata.json sidecar, which Bedrock reads
    automatically and which can be used to filter searches.

Run:  python3 scripts/build_kb_upload.py
Output: kb-upload/ (upload the three folders inside it to the S3 bucket)
"""
import json, re, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "data" / "kb", ROOT / "kb-upload"
REV_ATTR = ("Information provided courtesy of the Revenue Commissioners under a "
            "Creative Commons Attribution 4.0 International (CC BY 4.0) licence")
REV_LICENCE = ("https://www.revenue.ie/en/corporate/using-revenue/"
               "reuse-of-public-sector-information/public-sector-information-licence.pdf")

def strip_banner(text):
    """Remove the leading blockquote (lines starting with '>')."""
    lines = text.splitlines()
    i = 0
    while i < len(lines) and (lines[i].startswith(">") or not lines[i].strip()):
        i += 1
    return "\n".join(lines[i:])

def take_table(text):
    """Pull out the '| Field | Value |' table; return (fields, text_without_table)."""
    fields, keep = {}, []
    for line in text.splitlines():
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|$", line)
        if m:
            k, v = m.group(1), m.group(2)
            if k not in ("Field", "---") and not set(k) <= set("-"):
                fields[k] = v
            continue
        keep.append(line)
    return fields, "\n".join(keep)

def write(folder, name, body, meta):
    d = OUT / folder
    d.mkdir(parents=True, exist_ok=True)
    body = re.sub(r"\n{3,}", "\n\n", body).strip() + "\n"
    (d / name).write_text(body, encoding="utf-8")
    (d / (name + ".metadata.json")).write_text(
        json.dumps({"metadataAttributes": meta}, ensure_ascii=False, indent=2), encoding="utf-8")

if OUT.exists():
    shutil.rmtree(OUT)
count = 0

# Firm documents
for f in sorted((SRC / "firm").glob("*.md")):
    write("firm", f.name, strip_banner(f.read_text(encoding="utf-8")), {
        "source_type": "firm_document",
        "document": f.stem,
        "synthetic": True,
    })
    count += 1

# Past replies: keep the client's question (Context) as text, it helps matching
for f in sorted((SRC / "past-replies").glob("*.md")):
    fields, body = take_table(strip_banner(f.read_text(encoding="utf-8")))
    title, _, rest = body.partition("\n")
    rest = rest.replace("## Reply", "Reply:", 1)
    body = f"{title}\n\nClient's question: {fields['Context']}\n{rest}"
    write("past-replies", f.name, body, {
        "source_type": "past_reply",
        "reply_id": fields["Reply ID"],
        "category": fields["Category"],
        "date": fields["Date"],
        "sent_by": fields["Sent by"],
        "synthetic": True,
    })
    count += 1

# Revenue pages
for f in sorted((SRC / "revenue").glob("*.md")):
    if f.name == "README.md":
        continue
    fields, body = take_table(strip_banner(f.read_text(encoding="utf-8")))
    write("revenue", f.name, body, {
        "source_type": "revenue_guidance",
        "source_url": fields["URL"],
        "section": fields["Source"],
        "saved_on": fields["Saved on"],
        "attribution": REV_ATTR,
        "licence_url": REV_LICENCE,
        "synthetic": False,
    })
    count += 1

print(f"Wrote {count} documents (+{count} metadata files) to {OUT}")
