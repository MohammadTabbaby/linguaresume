"""Static section content validation."""
import logging
import re
from typing import Dict, List

from linguaresume.parsing.splitter import split_resume_sections, is_static_section

logger = logging.getLogger("linguaresume")


def validate_static_sections(final_md: str, static_bundle: str, alias_map: Dict, static_keys: List[str]) -> bool:
    if not static_bundle.strip():
        return True
    header, final_sections = split_resume_sections(final_md, alias_map)
    final_static_parts = []
    for title, content in final_sections:
        if is_static_section(title, static_keys, alias_map):
            final_static_parts.append(content.strip())
    final_static = "\n\n".join(final_static_parts)

    def normalize(s: str) -> set:
        s = re.sub(r'(?m)^## .*$', '', s)
        lines = [re.sub(r'\s+', ' ', line).strip()
                 for line in s.splitlines()
                 if line.strip()]
        return set(lines)

    final_norm = normalize(final_static)
    static_norm = normalize(static_bundle)

    if final_norm != static_norm:
        missing = static_norm - final_norm
        extra = final_norm - static_norm
        if len(missing) > 2 or len(extra) > 2:
            churn = (len(missing) + len(extra)) / max(len(static_norm), 1)
            if churn > 0.10:
                logger.warning("⚠️ Static sections content was altered or missing (churn %.0f%%).", churn * 100)
                return False
    logger.info("✅ Static sections content preserved.")
    return True
