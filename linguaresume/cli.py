"""CLI entry point with subcommands for LinguaResume."""
import argparse
import logging
import os
import sys
from typing import Optional

from linguaresume import setup_logging
from linguaresume.config import Config
from linguaresume.llm.client import OllamaClient, OpenAIClient
from linguaresume.tailoring.engine import TailoringEngine
from linguaresume.pdf.renderer import PDFRenderer
from linguaresume.parsing.extractor import load_text, extract_companies, extract_dates
from linguaresume.parsing.splitter import split_resume_sections, build_static_bundle, _make_alias_map
from linguaresume.validation.tech import TechValidator

logger = logging.getLogger("linguaresume")


def _build_llm_client(cfg: Config, api_key: Optional[str] = None):
    if api_key or os.environ.get("OPENAI_API_KEY"):
        return OpenAIClient(
            api_key=api_key or os.environ["OPENAI_API_KEY"],
            model=cfg.ollama.model,
            temperature=cfg.ollama.temperature,
            timeout=cfg.ollama.timeout,
        )
    return OllamaClient(
        url=cfg.ollama.url,
        model=cfg.ollama.model,
        temperature=cfg.ollama.temperature,
        timeout=cfg.ollama.timeout,
    )


def cmd_tailor(args):
    setup_logging(level=logging.INFO)
    cfg = Config.from_yaml(args.config)
    llm = _build_llm_client(cfg, args.api_key)
    engine = TailoringEngine(cfg, llm, force=args.force, domain_override=args.domain)
    md_path, pdf_path = engine.run(args.job_description)
    print(f"\n✅ Done!\nMarkdown: {md_path}\nPDF:      {pdf_path}")


def cmd_validate(args):
    setup_logging(level=logging.INFO)
    cfg = Config.from_yaml(args.config)
    final_md = load_text(args.markdown)

    master_path = args.master or cfg.fallback_cv
    if not os.path.exists(master_path):
        print(f"Master CV not found: {master_path}")
        sys.exit(1)

    master_md = load_text(master_path)
    llm = _build_llm_client(cfg)
    engine = TailoringEngine(cfg, llm)
    engine.master_md = master_md
    engine.master_name = "Candidate"
    engine.master_companies = extract_companies(master_md)
    engine.master_dates = extract_dates(master_md)
    engine.alias_map = _make_alias_map(cfg.section_aliases)
    engine.static_keys = cfg.static_section_keys
    engine.tech_validator = TechValidator(engine.alias_map)
    engine.bullet_token_overlap = cfg.validation.bullet_token_overlap_threshold
    engine.bullet_retention = cfg.validation.bullet_retention_threshold
    engine.master_lang = args.master_lang
    engine.target_lang = args.target_lang

    header, sections = split_resume_sections(master_md, engine.alias_map)
    static_bundle = build_static_bundle(sections, engine.static_keys, engine.alias_map)

    result = engine.validate_final(final_md, static_bundle)
    print(f"Validation {'PASSED' if result.passed else 'FAILED'}")
    if result.failures:
        for f in result.failures:
            print(f"  - {f}")
    if result.details:
        for k, v in result.details.items():
            print(f"  {k}: {v}")
    sys.exit(0 if result.passed else 1)


def cmd_pdf(args):
    setup_logging(level=logging.INFO)
    cfg = Config.from_yaml(args.config)
    md_text = load_text(args.markdown)
    pdf_path = args.output or os.path.splitext(args.markdown)[0] + ".pdf"
    renderer = PDFRenderer(cfg.resume_css)
    renderer.render(md_text, pdf_path, lang=args.lang)
    print(f"📄 PDF regenerated: {pdf_path}")


def cmd_translate(args):
    setup_logging(level=logging.INFO)
    cfg = Config.from_yaml(args.config)
    llm = _build_llm_client(cfg)
    engine = TailoringEngine(cfg, llm)
    engine.target_lang = args.to
    engine.master_lang = args.from_lang

    md_text = load_text(args.markdown)
    header, sections = split_resume_sections(md_text, _make_alias_map(cfg.section_aliases))
    static = build_static_bundle(sections, cfg.static_section_keys, _make_alias_map(cfg.section_aliases))

    if not static.strip():
        print("No static sections found to translate.")
        sys.exit(0)

    translated = engine.translate_static_sections(static)
    print(translated)


def main():
    parser = argparse.ArgumentParser(description="LinguaResume - Language-Agnostic Resume Tailor")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    sub = parser.add_subparsers(dest="command", required=True)

    p_tailor = sub.add_parser("tailor", help="Run full tailoring pipeline")
    p_tailor.add_argument("job_description", help="Path to job description text file")
    p_tailor.add_argument("--force", action="store_true", help="Skip compatibility confirmation")
    p_tailor.add_argument("--domain", choices=["webdev", "devops", "fullstack", "other"], help="Force domain")
    p_tailor.add_argument("--api-key", help="OpenAI API key (optional)")

    p_val = sub.add_parser("validate", help="Run validators on a tailored resume")
    p_val.add_argument("markdown", help="Path to tailored resume markdown")
    p_val.add_argument("--master", help="Path to master CV for comparison")
    p_val.add_argument("--master-lang", default="en", choices=["en", "fr", "de"])
    p_val.add_argument("--target-lang", default="en", choices=["en", "fr", "de"])

    p_pdf = sub.add_parser("pdf", help="Regenerate PDF from markdown")
    p_pdf.add_argument("markdown", help="Path to markdown file")
    p_pdf.add_argument("--output", "-o", help="Output PDF path")
    p_pdf.add_argument("--lang", default="en", choices=["en", "fr", "de"])

    p_trans = sub.add_parser("translate", help="Translate static sections of a resume")
    p_trans.add_argument("markdown", help="Path to markdown file")
    p_trans.add_argument("--to", required=True, choices=["en", "fr", "de"], help="Target language")
    p_trans.add_argument("--from-lang", default="en", choices=["en", "fr", "de"])

    args = parser.parse_args()

    if args.command == "tailor":
        cmd_tailor(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "pdf":
        cmd_pdf(args)
    elif args.command == "translate":
        cmd_translate(args)


if __name__ == "__main__":
    main()
