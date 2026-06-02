"""Validation package."""
from linguaresume.validation.base import ValidationResult
from linguaresume.validation.companies import validate_companies
from linguaresume.validation.dates import validate_dates
from linguaresume.validation.bullets import validate_bullet_retention
from linguaresume.validation.experience import validate_experience
from linguaresume.validation.tech import TechValidator
from linguaresume.validation.static import validate_static_sections

__all__ = [
    "ValidationResult",
    "validate_companies",
    "validate_dates",
    "validate_bullet_retention",
    "validate_experience",
    "TechValidator",
    "validate_static_sections",
]
