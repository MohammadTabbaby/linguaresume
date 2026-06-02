"""Configuration dataclasses for LinguaResume."""
from dataclasses import dataclass, field
from typing import Dict, List
import os
import yaml


@dataclass
class OllamaConfig:
    url: str
    model: str
    timeout: int
    temperature: float


@dataclass
class OutputConfig:
    subdir: str
    max_retries: int


@dataclass
class ValidationConfig:
    bullet_token_overlap_threshold: float = 0.35
    bullet_retention_threshold: float = 0.60


@dataclass
class Config:
    ollama: OllamaConfig
    cv_map: Dict[str, str]
    fallback_cv: str
    output: OutputConfig
    section_aliases: Dict[str, List[str]]
    static_section_keys: List[str]
    junior_keywords: List[str]
    enable_junior_special_case: bool
    corrections_fr: List[dict]
    corrections_de: List[dict]
    stopwords: List[str]
    resume_css: str
    validation: ValidationConfig = field(default_factory=ValidationConfig)

    @classmethod
    def from_yaml(cls, path: str = "config.yaml") -> "Config":
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        ollama_raw = raw.get("ollama", {})
        output_raw = raw.get("output", {})
        validation_raw = raw.get("validation", {})

        cfg = cls(
            ollama=OllamaConfig(
                url=ollama_raw.get("url", "http://127.0.0.1:1234/v1/chat/completions"),
                model=ollama_raw.get("model", "qwen/qwen3.5-9b"),
                timeout=ollama_raw.get("timeout", 720),
                temperature=ollama_raw.get("temperature", 0.3),
            ),
            cv_map=raw.get("cv_map", {}),
            fallback_cv=raw.get("fallback_cv", "./cvs/master_en.md"),
            output=OutputConfig(
                subdir=output_raw.get("subdir", "outputs"),
                max_retries=output_raw.get("max_retries", 3),
            ),
            section_aliases=raw.get("section_aliases", {}),
            static_section_keys=raw.get("static_section_keys", ["education", "languages"]),
            junior_keywords=raw.get("junior_keywords", ["junior", "débutant"]),
            enable_junior_special_case=raw.get("enable_junior_special_case", False),
            corrections_fr=raw.get("corrections_fr", []),
            corrections_de=raw.get("corrections_de", []),
            stopwords=raw.get("stopwords", []),
            resume_css=raw.get("resume_css", ""),
            validation=ValidationConfig(
                bullet_token_overlap_threshold=validation_raw.get(
                    "bullet_token_overlap_threshold", 0.35
                ),
                bullet_retention_threshold=validation_raw.get(
                    "bullet_retention_threshold", 0.60
                ),
            ),
        )
        cfg._validate_cv_paths()
        return cfg

    def _validate_cv_paths(self) -> None:
        all_paths = list(self.cv_map.values()) + [self.fallback_cv]
        for path in all_paths:
            if not os.path.exists(path):
                raise FileNotFoundError(f"CV file not found: {path}")
