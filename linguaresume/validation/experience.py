"""Experience duration validation."""
import logging
import re

from linguaresume.parsing.extractor import extract_total_months

logger = logging.getLogger("linguaresume")


def validate_experience(master_md: str, tailored_md: str) -> bool:
    master_months = extract_total_months(master_md)
    tailored_months = extract_total_months(tailored_md)

    profile_match = re.search(r'(?i)(\d+)\s*(?:ans?|years?)\s*d?[\'’e]?\s*exp[eé]rience', tailored_md)
    if profile_match:
        claimed_years = int(profile_match.group(1))
        if claimed_years * 12 > master_months + 6:
            logger.warning(
                "⚠️ Experience inflation: claims %d years but master has ~%.1f years",
                claimed_years, master_months / 12,
            )
            return False

    if tailored_months > master_months + 6:
        logger.warning(
            "⚠️ Experience inflation: tailored total %.0f months vs master %.0f months",
            tailored_months, master_months,
        )
        return False

    logger.info("✅ Experience duration matches master CV.")
    return True
