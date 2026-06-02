"""Company name validation."""
import logging
from typing import Set

from linguaresume.parsing.extractor import extract_companies, company_matches

logger = logging.getLogger("linguaresume")


def validate_companies(final_md: str, master_companies: Set[str], translating: bool = False) -> bool:
    out = extract_companies(final_md)
    extra = {comp for comp in out if not any(company_matches(m, comp) for m in master_companies)}
    if extra:
        if translating:
            logger.warning("⚠️ Translated company names (likely correct): %s", extra)
            return True
        else:
            logger.warning("⚠️ HALLUCINATED COMPANIES: %s", extra)
            return False
    logger.info("✅ All companies match master resume.")
    return True
