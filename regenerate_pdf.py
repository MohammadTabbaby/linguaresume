#!/usr/bin/env python3
"""
Regenerate a PDF from an already tailored Markdown file.
Uses the shared PDFRenderer and auto-detects language.
Usage: python regenerate_pdf.py path\to\resume.md
"""

import sys
import os

from linguaresume.config import Config
from linguaresume.pdf.renderer import PDFRenderer


def detect_md_lang(md_text: str) -> str:
    fr_words = {"profil", "compétences", "expérience", "formation", "langues"}
    de_words = {"profil", "fähigkeiten", "erfahrung", "ausbildung", "sprachen"}
    text_lower = md_text.lower()
    if any(w in text_lower for w in fr_words):
        return "fr"
    if any(w in text_lower for w in de_words):
        return "de"
    return "en"


def regenerate(md_path: str, config_path: str = "config.yaml") -> str:
    cfg = Config.from_yaml(config_path)

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    lang = detect_md_lang(content)
    pdf_path = os.path.splitext(md_path)[0] + ".pdf"
    renderer = PDFRenderer(cfg.resume_css)
    renderer.render(content, pdf_path, lang=lang)
    print(f"✅ PDF regenerated: {pdf_path}")
    return pdf_path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python regenerate_pdf.py resume.md")
        sys.exit(1)
    regenerate(sys.argv[1])
