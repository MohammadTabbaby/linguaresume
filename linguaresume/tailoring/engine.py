"""High-level tailoring and assembly engine."""
import os
import re
import sys
import json
import logging
import unicodedata
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from linguaresume.config import Config
from linguaresume.models import Requirement, ValidationResult
from linguaresume.llm.client import LLMClient
from linguaresume.llm.prompts import (
    render_middle_prompt,
    render_translate_prompt,
    render_requirements_prompt,
    render_title_translate_prompt,
)
from linguaresume.parsing.splitter import (
    split_resume_sections,
    build_mutable_bundle,
    build_static_bundle,
    replace_subtitle,
    _make_alias_map,
    _heading_normalize,
)
from linguaresume.parsing.extractor import (
    extract_companies,
    extract_dates,
    extract_keywords,
    extract_total_months,
    company_matches,
    normalize_text,
    _sig_tokens,
    load_text,
)
from linguaresume.validation import (
    validate_companies,
    validate_dates,
    validate_bullet_retention,
    validate_experience,
    TechValidator,
    validate_static_sections,
)

logger = logging.getLogger("linguaresume")


def detect_language(text: str) -> str:
    text_lower = text.lower()
    fr_words = {"le", "la", "les", "de", "et", "à", "dans", "pour", "avec", "un", "une", "des", "du", "sur"}
    de_words = {"der", "die", "das", "und", "für", "mit", "von", "zu", "auf", "bei", "ist", "sich", "werden"}
    en_words = {"the", "and", "for", "with", "this", "that", "from", "have", "been", "are", "was", "were"}
    words = set(re.findall(r"\b[a-z]{2,}\b", text_lower))
    fr_count = len(words & fr_words)
    de_count = len(words & de_words)
    en_count = len(words & en_words)
    if fr_count >= 2 and fr_count > de_count and fr_count > en_count:
        return "fr"
    elif de_count >= 2 and de_count > en_count:
        return "de"
    else:
        return "en"


def clean_markdown(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:markdown)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```\s*$", "", text)
    text = re.sub(r"^\d+\s*\n", "", text, count=1)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("\\)", ")").replace("\\(", "(")
    text = re.sub(r"\(([^a-zA-Z$#%_{}&])", r"\1", text)
    if not text.endswith("\n"):
        text += "\n"
    return text


def apply_corrections(text: str, corrections: list, master_name: Optional[str] = None) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if master_name:
        text = re.sub(r'^#\s+.*$', f"# {master_name}", text, count=1, flags=re.MULTILINE)

    for entry in corrections:
        pattern = entry["pattern"]
        replacement = entry["replacement"]
        flags = entry.get("flags", "")
        if flags == "VERB":
            def replacer(m, repl=replacement):
                w = m.group(0)
                return repl if w[0].isupper() else repl[0].lower() + repl[1:]
            text = re.sub(pattern, replacer, text, flags=re.IGNORECASE)
        elif flags == "IGNORECASE":
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        else:
            text = re.sub(pattern, replacement, text)

    forbidden = [
        r"^##\s+Comp[eé]tences?\s*$",
        r"^##\s+Key\s+Skills?\s*.*?(?=^##|\Z)",
        r"^##\s+Skills?\s+Summary\s*.*?(?=^##|\Z)",
    ]
    for pat in forbidden:
        text = re.sub(pat, "", text, flags=re.MULTILINE | re.DOTALL)

    strip_lines = [
        r"^Note\s*:.*$", r"^Remarque\s*:.*$", r"^Notez\s+que\b.*$",
        r"^Please\s+note\b.*$", r"^\*Note\s*:.*\*\s*$", r"^I have (followed|respected|adhered).*$",
        r"^J'ai (respecté|suivi|appliqué).*$", r"^J'ai (identifié|traduit|ajouté|conservé).*$",
        r"^En (suivant|respectant|appliquant).*$",
    ]
    for pat in strip_lines:
        text = re.sub(pat, "", text, flags=re.MULTILINE)

    strip_blocks = [
        r"(?m)^Notez\s+que\b[\s\S]*?(?=\n\n|\Z)",
        r"(?m)^Note\s*:[\s\S]*?(?=\n\n|\Z)",
        r"(?m)^J'ai respecté[\s\S]*?(?=\n\n|\Z)",
        r"(?m)^Please\s+note[\s\S]*?(?=\n\n|\Z)",
    ]
    for pat in strip_blocks:
        text = re.sub(pat, "", text, flags=re.IGNORECASE)

    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.rstrip() + "\n"


def enforce_headings(text: str, target_lang: str) -> str:
    heading_map = {
        "en": {
            "profile": "Profile",
            "tech": "Technical Skills",
            "experience": "Professional Experience",
            "edu": "Education",
            "lang": "Languages",
        },
        "fr": {
            "profile": "Profil",
            "tech": "Compétences techniques",
            "experience": "Expérience Professionnelle",
            "edu": "Formation",
            "lang": "Langues",
        },
        "de": {
            "profile": "Profil",
            "tech": "Technische Fähigkeiten",
            "experience": "Berufserfahrung",
            "edu": "Ausbildung",
            "lang": "Sprachen",
        },
    }
    h = heading_map.get(target_lang, heading_map["en"])
    
    text = re.sub(
        r"(?m)^##\s*(?:Profile|Professional Profile|Profil|Berufliches Profil).*$",
        f"## {h['profile']}", text
    )
    text = re.sub(
        r"(?m)^##\s*(?:Technical\s+Skills|Compétences techniques|Technische Fähigkeiten|Skills|Compétences|Fähigkeiten|Technical Skills Stack).*$",
        f"## {h['tech']}", text
    )
    text = re.sub(
        r"(?m)^##\s*(?:Professional\s+Experience|Expérience\s+Professionnelle|Expérience|Experience|Berufserfahrung|Berufliche\s+Erfahrung).*$",
        f"## {h['experience']}", text
    )
    text = re.sub(
        r"(?m)^##\s*(?:Education|Formation|Ausbildung|Éducation).*$",
        f"## {h['edu']}", text
    )
    text = re.sub(
        r"(?m)^##\s*(?:Languages|Langues|Sprachen).*$",
        f"## {h['lang']}", text
    )
    return text


def extract_json_object(text: str) -> Optional[dict]:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        try:
            return json.loads(text)
        except Exception:
            pass
    try:
        import importlib
        repair_module = importlib.import_module("json_repair")
        repair_json = getattr(repair_module, "repair_json", None)
    except ImportError:
        repair_json = None
    if repair_json:
        try:
            repaired = repair_json(text)
            return json.loads(repaired)
        except Exception:
            pass
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    end = None
    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if not in_string:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
    if end is None:
        return None
    candidate = text[start:end]
    try:
        return json.loads(candidate)
    except Exception:
        if repair_json:
            try:
                return json.loads(repair_json(candidate))
            except Exception:
                pass
    return None


def slugify(text: str, max_len: int = 40) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text).strip("_")
    return text[:max_len]


class TailoringEngine:
    def __init__(
        self,
        config: Config,
        llm_client: LLMClient,
        force: bool = False,
        domain_override: Optional[str] = None,
    ):
        self.cfg = config
        self.llm = llm_client
        self.force = force
        self.domain_override = domain_override
        self.alias_map = _make_alias_map(self.cfg.section_aliases)
        self.static_keys = self.cfg.static_section_keys
        self.stopwords = set(self.cfg.stopwords)
        self.master_lang = "en"
        self.job_desc = ""
        self.target_lang = "en"
        self.domain = "other"
        self.master_md = ""
        self.master_name = ""
        self.master_companies: Set[str] = set()
        self.master_dates: Set[str] = set()
        self.requirements = Requirement()
        self.output_dir = ""
        self.tech_validator = TechValidator(self.alias_map)
        self.bullet_token_overlap = self.cfg.validation.bullet_token_overlap_threshold
        self.bullet_retention = self.cfg.validation.bullet_retention_threshold

    def detect_language(self, text: str) -> str:
        return detect_language(text)

    def extract_requirements(self) -> Requirement:
        prompt = render_requirements_prompt(job_desc=self.job_desc)
        response = self.llm.complete(
            "You are a JSON expert. Return only valid JSON.",
            prompt,
        )
        req_dict = extract_json_object(response)
        if req_dict is None:
            logger.warning("⚠️ LLM JSON parsing failed; using fallback domain detection.")
            req_dict = {
                "job_title": self._fallback_job_title(),
                "company": "",
                "domain": self._fallback_domain(self.job_desc),
                "must_haves": [],
                "nice_to_haves": [],
                "soft_skills": [],
                "job_focus": "",
                "language_tone": "professional",
            }
        valid_domains = {"devops", "webdev", "fullstack", "other"}
        if req_dict.get("domain") not in valid_domains:
            req_dict["domain"] = self._fallback_domain(self.job_desc)
        self.domain = req_dict["domain"]
        if self.domain_override:
            self.domain = self.domain_override
            req_dict["domain"] = self.domain_override
            logger.info("📌 Domain overridden to: %s", self.domain)

        self.requirements = Requirement(
            job_title=req_dict.get("job_title", ""),
            company=req_dict.get("company", ""),
            domain=req_dict.get("domain", "other"),
            must_haves=req_dict.get("must_haves", []),
            nice_to_haves=req_dict.get("nice_to_haves", []),
            soft_skills=req_dict.get("soft_skills", []),
            job_focus=req_dict.get("job_focus", ""),
            language_tone=req_dict.get("language_tone", "professional"),
        )

        if self.target_lang != "en" and self.requirements.job_title:
            trans_prompt = render_title_translate_prompt(
                target_lang=self.target_lang,
                job_title=self.requirements.job_title,
            )
            trans_resp = self.llm.complete("You are a translator.", trans_prompt)
            self.requirements.job_title_translated = trans_resp.strip()
        return self.requirements

    def _fallback_domain(self, text: str) -> str:
        lower = text.lower()
        frontend_kw = {"react", "next.js", "nextjs", "vue", "svelte", "angular"}
        devops_kw = {"kubernetes", "k8s", "docker", "nginx", "load balancer", "digitalocean", "ci/cd", "jenkins", "terraform", "ansible"}
        has_frontend = any(kw in lower for kw in frontend_kw)
        score_d = sum(1 for kw in devops_kw if kw in lower)
        score_w = sum(1 for kw in frontend_kw if kw in lower)

        if score_d == 0 and score_w == 0:
            return "other"
        if has_frontend and score_d > 0:
            if score_d >= 2:
                return "fullstack"
            else:
                return "webdev"
        if score_d > 0:
            return "devops"
        if has_frontend:
            return "webdev"
        return "other"

    def _fallback_job_title(self) -> str:
        patterns = [
            r"\b(?:recherchons|recrutons|embauchons)\s+(?:un(?:e)?\s+)?([\w\-\s]{4,60}?)(?:[.,;]|\s+(?:pour|afin|à|dans|en)\b)",
            r"(?:est|sommes)\s+à\s+la\s+recherche\s+d['\s]?un(?:e)?\s+([\w\-\s]{4,60}?)(?:[.,;]|\s+(?:pour|afin|à|dans|en)\b)",
            r"recherche\s+(?:un|une|des)\s+([\w\-\s]{4,60}?)(?:[.,;]|\s+(?:pour|afin|à|dans|en)\b)",
            r"recrute\s+(?:un|une|des)\s+([\w\-\s]{4,60}?)(?:[.,;]|\s+(?:pour|afin|à|dans|en)\b)",
        ]
        for pat in patterns:
            m = re.search(pat, self.job_desc, re.IGNORECASE)
            if m:
                title = m.group(1).strip()
                title = re.sub(r"\bDéveloppeurs\b", "Développeur", title, flags=re.IGNORECASE)
                title = re.sub(r"\bIngénieurs\b", "Ingénieur", title, flags=re.IGNORECASE)
                title = re.sub(r"\bFullstack\b", "Full-Stack", title, flags=re.IGNORECASE)
                return title
        return ""

    def select_master_cv(self) -> None:
        domain = self.domain
        if self.cfg.enable_junior_special_case:
            job_title = self.requirements.job_title.lower()
            if any(kw in job_title for kw in self.cfg.junior_keywords):
                domain = f"{domain}_junior"
                logger.info("🔰 Junior position detected – trying junior master CV")
        lang_domain_key = f"{self.target_lang}_{domain}"
        cv_file = self.cfg.cv_map.get(lang_domain_key)
        if cv_file:
            logger.info("📄 Using language‑specific CV: %s", cv_file)
            self.master_lang = self.target_lang
        else:
            cv_file = self.cfg.cv_map.get(domain, self.cfg.fallback_cv)
            logger.info("📄 No %s CV, using English master: %s", lang_domain_key, cv_file)
            self.master_lang = "en"

        if not os.path.exists(cv_file):
            raise FileNotFoundError(f"Master CV file not found: {cv_file}")
        self.master_md = load_text(cv_file)
        name_match = re.search(r"^#\s+(.+)", self.master_md, re.MULTILINE)
        self.master_name = name_match.group(1).strip() if name_match else "Candidate"
        self.master_companies = extract_companies(self.master_md)
        self.master_dates = extract_dates(self.master_md)

    def compatibility_check(self) -> None:
        master_norm = unicodedata.normalize("NFKD", self.master_md)
        master_norm = "".join(ch for ch in master_norm if not unicodedata.combining(ch))
        master_kw = extract_keywords(master_norm, self.stopwords)
        job_text = " ".join(
            self.requirements.must_haves +
            self.requirements.nice_to_haves +
            self.requirements.soft_skills
        )
        job_kw = extract_keywords(job_text, self.stopwords)
        common = master_kw & job_kw
        pct = len(common) / max(len(job_kw), 1) * 100
        logger.info("📋 Compatibility: %.1f%% (%d of %d job keywords present in master)", pct, len(common), len(job_kw))
        if pct < 30 and not self.force:
            logger.warning("⚠️ Low match – the LLM will focus on transferable skills.")
            if os.environ.get("LINGUARESUME_YES", "").lower() in ("1", "true", "yes"):
                logger.info("Auto-continuing via LINGUARESUME_YES.")
            else:
                try:
                    response = input("Continue anyway? (y/n): ").strip().lower()
                    if response != "y":
                        sys.exit(0)
                except EOFError:
                    logger.error("Non-interactive mode detected. Use --force or set LINGUARESUME_YES=1")
                    sys.exit(1)
        elif pct < 30 and self.force:
            logger.warning("⚠️ Low match but --force flag set, continuing.")

    def split_master(self) -> Tuple[str, str, str]:
        header, sections = split_resume_sections(self.master_md, self.alias_map)
        mutable = build_mutable_bundle(sections, self.static_keys, self.alias_map)
        static = build_static_bundle(sections, self.static_keys, self.alias_map)
        return header, mutable, static

    def tailor_middle(self, master_mutable: str) -> str:
        system = """You are a resume optimization engine. Your task is to rewrite resume content to align with a job description while following strict constraints:

1. OUTPUT FORMAT: Wrap the entire response in <resume_middle> XML tags.
2. FACTUAL FIDELITY: Every claim must be verifiable in the source material. Do not invent companies, dates, technologies, or experience duration.
3. TRANSLATION: Translate all content into the target language except proper nouns.
4. BULLET PRESERVATION: Keep the exact same number of bullets per employer as the source.
5. TECHNOLOGY BOUNDARY: Only mention tools/frameworks explicitly listed in the source CV. If the job requires something missing, omit it entirely.
6. NO META-COMMENTARY: Do not include notes, explanations, or "I have followed" statements.
7. HEADING ENFORCEMENT: Use exactly the section headings specified in the user prompt."""
        prompt = self._build_middle_prompt(master_mutable)
        raw = self.llm.complete(system, prompt)
        cleaned = clean_markdown(raw)

        match = re.search(r'<resume_middle>(.*?)</resume_middle>', cleaned, re.DOTALL | re.IGNORECASE)
        if match:
            cleaned = match.group(1).strip()
        else:
            cleaned = re.sub(r'</?[a-z_]+>', '', cleaned).strip()

        if self.target_lang == "fr":
            cleaned = apply_corrections(cleaned, self.cfg.corrections_fr, self.master_name)
        elif self.target_lang == "de":
            cleaned = apply_corrections(cleaned, self.cfg.corrections_de, self.master_name)
        cleaned = enforce_headings(cleaned, self.target_lang)
        return cleaned

    def _build_middle_prompt(self, master_mutable: str) -> str:
        req = self.requirements
        failures = req.failures
        missing = req.missing_must
        missing_soft = req.missing_soft

        retry_notes = []
        if missing:
            retry_notes.append(f"MISSING_MUST_HAVES: {json.dumps(missing, ensure_ascii=False)}")
        if missing_soft:
            retry_notes.append(f"MISSING_SOFT_SKILLS: {json.dumps(missing_soft, ensure_ascii=False)}")
        if "hallucinated_companies" in failures:
            retry_notes.append("RULE: Use EXACT company names from master. No translations, no inventions.")
        if "invented_dates" in failures:
            retry_notes.append("RULE: Use EXACT date ranges from master. No modifications.")
        if "bullets_dropped" in failures:
            retry_notes.append("RULE: Preserve every bullet point. Do not merge, split, or delete.")
        if "static_sections_altered" in failures:
            retry_notes.append("RULE: Do not write Education or Languages sections. They are appended automatically.")
        if "experience_inflated" in failures:
            retry_notes.append("RULE: Total experience must not exceed master CV.")
        if "added_new_technologies" in failures:
            retry_notes.append("RULE: Only use technologies explicitly listed in master CV.")

        retry_block = "\n".join(retry_notes)

        lang_name = {"en": "English", "fr": "French", "de": "German"}.get(self.target_lang, "English")

        heading_map = {
            "en": {"profile": "Profile", "tech": "Technical Skills", "experience": "Professional Experience"},
            "fr": {"profile": "Profil", "tech": "Compétences techniques", "experience": "Expérience Professionnelle"},
            "de": {"profile": "Profil", "tech": "Technische Fähigkeiten", "experience": "Berufserfahrung"},
        }
        h = heading_map.get(self.target_lang, heading_map["en"])

        return render_middle_prompt(
            lang_name=lang_name,
            profile_heading=h["profile"],
            tech_heading=h["tech"],
            experience_heading=h["experience"],
            job_desc=self.job_desc,
            must_haves=req.must_haves,
            nice_to_haves=req.nice_to_haves,
            soft_skills=req.soft_skills,
            job_focus=req.job_focus,
            retry_block=retry_block,
            master_mutable=master_mutable,
        )

    def translate_static_sections(self, static_bundle: str) -> str:
        if self.master_lang == self.target_lang or not static_bundle.strip():
            return static_bundle

        prompt = render_translate_prompt(
            target_lang=self.target_lang,
            static_bundle=static_bundle,
        )
        system = "You are a translation engine. Output only the translated text."
        translated = self.llm.complete(system, prompt)
        translated = clean_markdown(translated)
        translated = enforce_headings(translated, self.target_lang)
        return translated

    def _compute_missing(self, tailored_middle: str) -> None:
        tailored_tokens = _sig_tokens(tailored_middle)
        self.requirements.missing_must = [
            r for r in self.requirements.must_haves
            if len(_sig_tokens(r) & tailored_tokens) / max(len(_sig_tokens(r)), 1) < 0.5
        ]
        self.requirements.missing_soft = [
            s for s in self.requirements.soft_skills
            if s.lower() not in tailored_middle.lower()
        ]

    def validate_final(self, final_md: str, static_bundle: str) -> ValidationResult:
        failures = []
        details: Dict[str, Any] = {}
        translating = (self.master_lang != self.target_lang)

        if not validate_companies(final_md, self.master_companies, translating=translating):
            failures.append("hallucinated_companies")
        if not validate_dates(final_md, self.master_dates):
            failures.append("invented_dates")
        if not validate_static_sections(final_md, static_bundle, self.alias_map, self.static_keys):
            failures.append("static_sections_altered")
        if not validate_bullet_retention(
            self.master_md, final_md, lang_mismatch=translating,
            token_overlap_threshold=self.bullet_token_overlap,
            retention_threshold=self.bullet_retention,
        ):
            failures.append("bullets_dropped")
        if not validate_experience(self.master_md, final_md):
            failures.append("experience_inflated")
        extra_techs = self.tech_validator.get_extra_techs(self.master_md, final_md)
        if extra_techs:
            failures.append("added_new_technologies")
            details["added_new_technologies"] = sorted(extra_techs)

        header, final_sections = split_resume_sections(final_md, self.alias_map)
        final_titles = [_heading_normalize(t) for t, _ in final_sections]
        tech_aliases = self.alias_map.get("tech_skills", [])
        has_tech = any(t in tech_aliases for t in final_titles)
        if not has_tech:
            failures.append("missing_technical_skills")
            logger.warning("⚠️ Technical Skills section is missing from output")

        passed = not failures
        if passed:
            logger.info("✅ Validation passed.")
        return ValidationResult(passed=passed, failures=failures, details=details)

    def assemble(self, header: str, tailored_middle: str, static_bundle: str) -> str:
        static_bundle = self.translate_static_sections(static_bundle)
        job_title = self.requirements.job_title_translated or self.requirements.job_title
        final_header = replace_subtitle(header, job_title) if job_title else header.rstrip()
        parts = [final_header.rstrip(), "", tailored_middle.strip(), "", static_bundle.strip()]
        return "\n".join(parts).strip() + "\n"

    def setup_output_dir(self) -> None:
        parts = [self.requirements.company, self.requirements.job_title]
        slug_parts = [slugify(p) for p in parts if p]
        if not slug_parts:
            slug_parts.append(f"resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        dir_name = "_".join(slug_parts)
        out_dir = os.path.join(self.cfg.output.subdir, dir_name)
        os.makedirs(out_dir, exist_ok=True)
        self.output_dir = out_dir
        logger.info("📁 Output directory: %s", out_dir)

    # ─── NEW: professional filename builder ───
    def _build_filename_stem(self) -> str:
        """Return CV_Name_Role stem for final files."""
        name_slug = slugify(self.master_name)
        role = self.requirements.job_title_translated or self.requirements.job_title
        role_slug = slugify(role) if role else "resume"
        return f"CV_{name_slug}_{role_slug}"

    def save_markdown(self, final_md: str) -> str:
        stem = self._build_filename_stem()
        md_path = os.path.join(self.output_dir, f"{stem}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(final_md)
        logger.info("📄 Markdown saved to %s", md_path)
        return md_path

    def convert_to_pdf(self, md_path: str) -> str:
        from linguaresume.pdf.renderer import PDFRenderer
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        pdf_path = os.path.splitext(md_path)[0] + ".pdf"
        renderer = PDFRenderer(self.cfg.resume_css)
        renderer.render(content, pdf_path, lang=self.target_lang)
        logger.info("📄 PDF ready: %s", pdf_path)
        # Auto-open PDF
        try:
            import platform
            if platform.system() == "Windows":
                os.startfile(pdf_path)
            elif platform.system() == "Darwin":
                import subprocess
                subprocess.call(["open", pdf_path])
            else:
                import subprocess
                subprocess.call(["xdg-open", pdf_path])
        except Exception:
            pass  # Silently fail if auto-open isn't possible
        return pdf_path

    def run(self, job_desc_path: str) -> Tuple[str, str]:
        self.job_desc = load_text(job_desc_path)
        self.target_lang = self.detect_language(self.job_desc)
        logger.info("🌐 Detected job description language: %s", self.target_lang.upper())

        self.extract_requirements()
        logger.info("📂 Domain: %s", self.domain)

        self.select_master_cv()
        self.compatibility_check()

        header, master_mutable, static_bundle = self.split_master()

        retries = 0
        max_retries = self.cfg.output.max_retries
        final_md = ""

        while True:
            logger.info("✏️ Generating tailored resume (attempt %d)...", retries + 1)
            tailored_middle = self.tailor_middle(master_mutable)
            final_md = self.assemble(header, tailored_middle, static_bundle)

            result = self.validate_final(final_md, static_bundle)
            if result.passed:
                break

            retries += 1
            if retries > max_retries:
                logger.warning("⚠️ After %d retries, proceeding with current version.", max_retries)
                break

            self._compute_missing(tailored_middle)
            self.requirements.failures = result.failures
            logger.info("🔁 Retrying with targeted feedback (failures: %s)", result.failures)

        self.setup_output_dir()
        md_path = self.save_markdown(final_md)
        logger.info("📄 Converting to PDF...")
        pdf_path = self.convert_to_pdf(md_path)
        logger.info("✅ All done!")
        return md_path, pdf_path