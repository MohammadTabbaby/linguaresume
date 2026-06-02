"""Validation result type."""
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class ValidationResult:
    passed: bool
    failures: List[str]
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def should_retry(self) -> bool:
        return not self.passed and bool(self.failures)
