"""Shared PDF rendering logic."""
try:
    from playwright.sync_api import sync_playwright
except ImportError as exc:
    raise ImportError(
        "Playwright is required for PDF rendering. "
        "Install it with: pip install playwright && playwright install chromium"
    ) from exc

import markdown as md_lib
import re
from typing import Optional


class PDFRenderer:
    """Render Markdown resume to PDF using Playwright."""

    def __init__(self, css: str):
        self.css = css

    def render(self, md_text: str, output_path: str, lang: Optional[str] = None) -> str:
        """Convert markdown to PDF and write to output_path. Returns the path."""
        md_text = re.sub(r"\s*\[EN:\s*[^\]]*\]", "", md_text)
        body = md_lib.markdown(md_text, extensions=["tables", "fenced_code", "nl2br"])
        lang_attr = f' lang="{lang}"' if lang else ""
        html = (
            f"<!DOCTYPE html><html{lang_attr}><head>"
            f'<meta charset="utf-8"/><style>{self.css}</style>'
            f"</head><body>{body}</body></html>"
        )
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")
            pdf_bytes = page.pdf(
                format="A4",
                margin={"top": "18mm", "bottom": "18mm", "left": "20mm", "right": "20mm"},
                print_background=True,
                prefer_css_page_size=False,
            )
            browser.close()
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        return output_path
