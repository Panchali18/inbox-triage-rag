"""Build the client-facing PDFs (fee guide, FAQ, terms of engagement) from data/kb/firm/.

These are the files a reviewer can tick as attachments (US-21). Fictional firm, synthetic content.
Run locally:  python3 scripts/build_client_pdfs.py   (needs the `markdown` package and Chromium)
"""
import re
import subprocess
import tempfile
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "client-documents"
CHROME = "/opt/pw-browsers/chromium"
DOCS = {"services-and-fees.md": "Nore-Valley-Services-and-Fees.pdf",
        "faq.md": "Nore-Valley-Client-FAQ.pdf",
        "engagement-terms.md": "Nore-Valley-Terms-of-Engagement.pdf"}

CSS = """
@page { size: A4; margin: 22mm 20mm 20mm 20mm; }
body { font-family: 'DejaVu Sans', Arial, sans-serif; font-size: 10.5pt; line-height: 1.5; color: #1f2933; }
.brand { border-bottom: 3px solid #0f766e; padding-bottom: 6px; margin-bottom: 4px; display: flex;
         justify-content: space-between; align-items: baseline; }
.brand b { font-size: 15pt; color: #0f766e; letter-spacing: .3px; }
.brand span { font-size: 9pt; color: #52606d; }
.demo { background: #fff7e6; border: 1px solid #f0c36d; color: #7a5200; font-size: 8.5pt; padding: 5px 9px;
        margin: 8px 0 14px; border-radius: 4px; }
h1 { font-size: 17pt; margin: 6px 0 10px; color: #102a43; }
h2 { font-size: 12.5pt; color: #0f766e; margin: 18px 0 6px; border-bottom: 1px solid #d9e2ec; padding-bottom: 3px; }
table { border-collapse: collapse; width: 100%; margin: 6px 0 10px; font-size: 9.8pt; }
th { background: #f0f4f8; text-align: left; }
th, td { border: 1px solid #d9e2ec; padding: 5px 8px; vertical-align: top; }
td:last-child { white-space: nowrap; }
p, li { margin: 4px 0; }
.foot { margin-top: 22px; font-size: 8.5pt; color: #7b8794; border-top: 1px solid #d9e2ec; padding-top: 6px; }
"""

for src, pdf in DOCS.items():
    text = (ROOT / "data" / "kb" / "firm" / src).read_text(encoding="utf-8")
    text = re.sub(r"^>\s*\*\*Synthetic data.*$\n?", "", text, flags=re.M).strip()      # banner shown separately
    text = re.sub(r"^# Nore Valley Accountants:\s*", "# ", text, flags=re.M)          # brand is in the header
    body = markdown.markdown(text, extensions=["tables"])
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="brand"><b>Nore Valley Accountants</b><span>Kilkenny · Ireland</span></div>
<div class="demo"><b>Demonstration only.</b> Nore Valley Accountants is a fictional firm. Fees and terms are invented
for a portfolio project.</div>
{body}
<div class="foot">Nore Valley Accountants (fictional) · Synthetic document for the Inbox Triage with RAG portfolio project</div>
</body></html>"""
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
    OUT.mkdir(parents=True, exist_ok=True)
    subprocess.run([CHROME, "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={OUT / pdf}", f"file://{f.name}"], check=True, capture_output=True)
    print("built", OUT / pdf)
