"""LinguaResume package."""
import logging

def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure root logger for the package."""
    logger = logging.getLogger("linguaresume")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(levelname)s | %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger
