"""Technology hallucination validation."""
import logging
import re
import unicodedata
from typing import Set, Dict, List

from linguaresume.parsing.splitter import split_resume_sections, _heading_normalize

logger = logging.getLogger("linguaresume")


class TechValidator:
    def __init__(self, alias_map: Dict[str, List[str]]):
        self.alias_map = alias_map

    def _normalize_tech_token(self, token: str) -> str:
        token = unicodedata.normalize("NFKD", token)
        token = token.strip().lower()
        token = re.sub(r"\s*\([^)]*\)$", "", token)
        token = re.sub(r"\s*[+\-]\s*\d+.*$", "", token)
        token = re.sub(r"\d+\.?\d*", "", token)
        token = re.sub(r"[^\w#+.\-\s]", "", token)
        token = re.sub(r"\s+", " ", token)
        return token.strip()

    def _extract_tech_items(self, md: str) -> Set[str]:
        items: Set[str] = set()
        header, sections = split_resume_sections(md, self.alias_map)

        tech_aliases = self.alias_map.get("tech_skills", [])
        for title, content in sections:
            if _heading_normalize(title) in tech_aliases:
                for line in content.splitlines():
                    if re.match(r"^\s*\|?[-:\s|]+\|?\s*$", line):
                        continue
                    if "|" in line:
                        parts = [p.strip() for p in line.split("|") if p.strip()]
                        for cell in parts[1:]:
                            for token in re.split(r",|;|/|\|\band\b|-", cell):
                                tok = self._normalize_tech_token(token)
                                if tok:
                                    items.add(tok)
                    else:
                        for token in re.split(r",|;|/|\|\band\b|-", line):
                            tok = token.strip().lstrip("-* ")
                            if tok:
                                items.add(self._normalize_tech_token(tok))

        exp_aliases = self.alias_map.get("experience", [])
        for title, content in sections:
            if _heading_normalize(title) in exp_aliases:
                multiword = re.findall(r'\b[A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)+\b', content)
                for mw in multiword:
                    items.add(self._normalize_tech_token(mw))
                standalone = re.findall(r'\b[A-Z][a-zA-Z0-9]*\b', content)
                for sw in standalone:
                    items.add(self._normalize_tech_token(sw))

        exclude = {
            "agile", "scrum", "safe", "methodology", "process", "team",
            "collaboration", "project", "management", "analysis", "design",
            "documentation", "client", "company", "university", "master",
            "bachelor", "engineer", "developer", "senior", "junior", "lead",
            "january", "february", "march", "april", "may", "june", "july",
            "august", "september", "october", "november", "december",
            "present", "current", "france", "tunisia", "english", "french",
            "german", "profile", "skills", "experience", "education", "languages"
        }
        return {t for t in items if t not in exclude and len(t) > 1}

    def get_extra_techs(self, master_md: str, final_md: str) -> Set[str]:
        return self._extract_tech_items(final_md) - self._extract_tech_items(master_md)

    def validate(self, master_md: str, final_md: str) -> bool:
        extra = self.get_extra_techs(master_md, final_md)
        if extra:
            logger.warning("⚠️ ADDED NEW TECHNOLOGIES: %s", sorted(extra))
            return False
        logger.info("✅ No new technologies added.")
        return True
