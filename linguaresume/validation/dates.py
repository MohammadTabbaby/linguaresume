"""Date validation."""
import logging
from typing import Set

from linguaresume.parsing.extractor import extract_dates

logger = logging.getLogger("linguaresume")


def validate_dates(final_md: str, master_dates: Set[str]) -> bool:
    out_dates = extract_dates(final_md)
    extra = out_dates - master_dates
    if extra:
        logger.warning("⚠️ INVENTED DATES: %s", extra)
        return False
    logger.info("✅ All dates match master resume.")
    return True
