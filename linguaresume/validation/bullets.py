"""Bullet point retention validation."""
import logging
from typing import Dict, List

from linguaresume.parsing.extractor import _bullet_sections, _sig_tokens

logger = logging.getLogger("linguaresume")


def validate_bullet_retention(
    master_md: str,
    tailored_md: str,
    lang_mismatch: bool = False,
    token_overlap_threshold: float = 0.35,
    retention_threshold: float = 0.60,
) -> bool:
    master_sec = _bullet_sections(master_md)
    tailored_sec = _bullet_sections(tailored_md)

    if lang_mismatch:
        if len(master_sec) != len(tailored_sec):
            logger.warning("⚠️ Bullet retention: employer count mismatch (master %d vs tailored %d)",
                         len(master_sec), len(tailored_sec))
            return False
        for emp, bullets in master_sec.items():
            matched = None
            best_overlap = 0
            for t_emp in tailored_sec:
                overlap = len(_sig_tokens(emp) & _sig_tokens(t_emp))
                if overlap > best_overlap:
                    best_overlap = overlap
                    matched = t_emp
            if matched is None or best_overlap < 1:
                logger.warning("⚠️ Cannot match employer '%s' structurally", emp)
                return False
            count_diff = abs(len(bullets) - len(tailored_sec[matched]))
            if count_diff > 1:
                logger.warning("⚠️ Bullet count mismatch for '%s': master %d vs tailored %d",
                             emp, len(bullets), len(tailored_sec[matched]))
                return False
        logger.info("✅ Structural bullet retention passed (translation mode).")
        return True

    if not master_sec:
        return True
    ok = True
    for employer, m_bullets in master_sec.items():
        m_tok = _sig_tokens(employer)
        matched_key = None
        best_overlap = 0
        for t_emp in tailored_sec:
            overlap = len(m_tok & _sig_tokens(t_emp))
            if overlap > best_overlap:
                best_overlap = overlap
                matched_key = t_emp
        if matched_key is None or best_overlap < 1:
            logger.warning("⚠️ Cannot match employer '%s'", employer)
            ok = False
            continue
        t_bullets = tailored_sec[matched_key]
        content_scores = []
        for bullet in m_bullets:
            key = _sig_tokens(bullet)
            if not key:
                continue
            if any(len(key & _sig_tokens(tb)) / max(len(key), 1) >= token_overlap_threshold for tb in t_bullets):
                content_scores.append(True)
        if m_bullets and len(content_scores) / len(m_bullets) < retention_threshold:
            logger.warning(
                "⚠️ Low content retention for '%s': %d/%d bullets retained",
                employer, len(content_scores), len(m_bullets),
            )
            ok = False
    if ok:
        logger.info("✅ Bullet content retention check passed.")
    return ok
