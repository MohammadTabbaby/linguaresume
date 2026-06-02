"""Shared dataclasses for LinguaResume."""
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class ResumeSection:
    title: str
    content: str
    is_static: bool = False


@dataclass
class Requirement:
    job_title: str = ""
    company: str = ""
    domain: str = "other"
    must_haves: List[str] = field(default_factory=list)
    nice_to_haves: List[str] = field(default_factory=list)
    soft_skills: List[str] = field(default_factory=list)
    job_focus: str = ""
    language_tone: str = "professional"
    job_title_translated: str = ""
    failures: List[str] = field(default_factory=list, repr=False)
    missing_must: List[str] = field(default_factory=list, repr=False)
    missing_soft: List[str] = field(default_factory=list, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_title": self.job_title,
            "company": self.company,
            "domain": self.domain,
            "must_haves": self.must_haves,
            "nice_to_haves": self.nice_to_haves,
            "soft_skills": self.soft_skills,
            "job_focus": self.job_focus,
            "language_tone": self.language_tone,
            "job_title_translated": self.job_title_translated,
        }


@dataclass
class ValidationResult:
    passed: bool
    failures: List[str]
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def should_retry(self) -> bool:
        return not self.passed and bool(self.failures)
