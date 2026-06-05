# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Tailoring Engine Enhancements
- **XML Tag Wrapping**: LLM output now wrapped in `<resume_middle>` tags for reliable parsing
- **Robust JSON Extraction**: New `extract_json_object()` function with fallback to `json_repair` library
- **Text Processing Utilities**:
  - `clean_markdown()`: Strips code blocks, decodes HTML entities, normalizes formatting
  - `apply_corrections()`: Language-specific regex replacements with verb conjugation support
  - `enforce_headings()`: Standardizes section headings across languages (EN/FR/DE)
  - `slugify()`: Creates filesystem-safe filenames from arbitrary text
- **Professional Filename Generation**: New `_build_filename_stem()` method creates `CV_{Name}_{Role}` format
- **Enhanced Requirement Model**:
  - `job_title_translated`: Translated job titles in target language
  - `failures`: Tracks validation failures for feedback loops
  - `missing_must`: Missing must-have skills from tailored output
  - `missing_soft`: Missing soft skills from tailored output

#### Validation Enhancements
- **Missing Technical Skills Detection**: Validates presence of Technical Skills section in output
- **Detailed Failure Tracking**: Each validation failure tracked with specific details
- **Feedback Loop Refinement**: Failed validations now generate targeted feedback for LLM retry
  - Missing companies → "MISSING_COMPANIES" feedback
  - Dropped bullets → "RULE: Preserve every bullet point"
  - Added technologies → "RULE: Only use technologies explicitly listed in master CV"
  - Inflated experience → "RULE: Total experience must not exceed master CV"

#### Domain & Language Features
- **Junior Position Detection**: 
  - Configurable `junior_keywords` list (junior, débutant, anfänger, entry-level, graduate)
  - Appends "_junior" suffix to domain for CV selection
  - Example: "fullstack" + junior job → tries `cv_map["fullstack_junior"]` first
- **Fallback Job Title Extraction**: Regex patterns to detect job titles from French job descriptions
- **Domain Fallback Classification**: When LLM JSON parsing fails, uses keyword-based classification
  - Frontend keywords: react, next.js, vue, svelte, angular
  - DevOps keywords: kubernetes, docker, nginx, load balancer, ci/cd, terraform, ansible
  - Scoring algorithm determines best domain match

#### Configuration Updates
- Support for `enable_junior_special_case` configuration flag
- Configurable `junior_keywords` list for position-level detection
- New `corrections_de` and `corrections_fr` support for language-specific fixes
- Enhanced `section_aliases` for multi-language support

#### Error Handling & Logging
- Custom CSS styling support in PDF rendering
- Language-specific text corrections (French, German)
- Multi-language section alias support
- Validation feedback loop with retry mechanism (max_retries configurable, default 3)
- Caching system for LLM responses
- Comprehensive error messages with actionable feedback

### Changed
- Improved resume section parsing with multi-language support
- Enhanced validation with token-level overlap checking
- Refactored LLM client architecture for extensibility
- Improved domain classification algorithm with fallback strategy
- Better error handling and logging throughout
- LLM system prompt now includes specific constraints:
  - OUTPUT FORMAT: XML tag wrapping for reliable extraction
  - FACTUAL FIDELITY: Strict requirement preservation
  - BULLET PRESERVATION: Exact bullet count enforcement
  - TECHNOLOGY BOUNDARY: Only master CV technologies
  - NO META-COMMENTARY: Remove explanatory text
  - HEADING ENFORCEMENT: Standardized section headers

### Fixed
- Date extraction and validation edge cases
- Company name normalization for matching (Unicode NFKD decomposition)
- Bullet point retention calculation with token-level overlap
- PDF rendering with special characters and Unicode
- HTML entity handling in LLM responses
- Escaped bracket handling in markdown
- Excessive newline normalization (3+ → 2)

### Deprecated
- Support for Python 3.7 (upgrading to 3.8+ requirement)
- Direct string concatenation for resume assembly (replaced with proper `assemble()` method)

### Removed
- Legacy resume format support
- Unstructured text-based section parsing (now uses alias maps)

### Security
- Added input validation for file paths (prevents directory traversal)
- Environment variable handling for secrets (API keys never in config)
- Timeout protection for LLM calls (configurable, default 720 seconds)
- Sanitized file path handling in output directory creation

### Technical Details

#### New Methods in `TailoringEngine`
```python
def _build_filename_stem() -> str:
    """Return CV_Name_Role stem for final files."""
    
def extract_requirements() -> Requirement:
    """Extract and parse job requirements with robust JSON handling."""
    
def tailor_middle(master_mutable: str) -> str:
    """Generate tailored middle section with XML tag extraction."""
    
def _build_middle_prompt(master_mutable: str) -> str:
    """Build detailed prompt with validation feedback."""
    
def validate_final(final_md: str, static_bundle: str) -> ValidationResult:
    """Comprehensive 6-tier validation with detailed failure tracking."""
    
def _compute_missing(tailored_middle: str) -> None:
    """Calculate missing must-have and soft skills from output."""
```

#### New Helper Functions in `tailoring.engine` Module
- `detect_language(text: str) -> str` - Language detection with word frequency matching
- `clean_markdown(text: str) -> str` - LLM output cleanup
- `apply_corrections(text, corrections, master_name) -> str` - Language-specific fixes
- `enforce_headings(text, target_lang) -> str` - Header normalization
- `extract_json_object(text) -> Optional[dict]` - Robust JSON parsing
- `slugify(text, max_len) -> str` - Filesystem-safe naming

### API Stability Notes
- All new functions in `tailoring.engine` are public and stable
- `Requirement` dataclass extended with backward-compatible fields
- `ValidationResult` enhanced with failure details tracking
- LLM client interface remains unchanged (fully backward compatible)

## [1.0.0] - 2024-06-02

### Added
- Initial release of LinguaResume
- Core resume tailoring engine
- Multi-language support (English, French, German)
- Multiple domain-specific master CVs (Full-Stack, DevOps, Web, Non-Technical)
- LLM integration (Ollama and OpenAI support)
- Comprehensive validation framework
  - Company name validation
  - Date preservation validation
  - Bullet point retention validation
  - Experience duration validation
  - Technology stack validation
  - Static section preservation
- PDF rendering from markdown
- Configuration system with YAML
- Command-line interface with subcommands
  - `tailor`: Main resume tailoring
  - `validate`: Standalone validation
  - `pdf`: Generate PDF from markdown
  - `translate`: Translate resume sections
- Response caching for LLM calls
- Retry mechanism with validation feedback
- Comprehensive test suite
- Documentation (README, ARCHITECTURE, SETUP, CONFIG, CONTRIBUTING)
- 12 master resume templates (3 languages × 4 domains)

### Features

#### Tailoring Engine
- Automatic language detection (EN, FR, DE)
- Domain classification (fullstack, devops, webdev, other)
- CV selection with language and domain fallbacks
- Resume section splitting (mutable vs static)
- Job requirement extraction and parsing
- LLM-powered content adaptation
- Multi-pass validation with feedback

#### Validation Framework
- 6-tier validation system:
  1. Company name preservation
  2. Date range preservation
  3. Bullet point retention (token-based)
  4. Experience duration consistency
  5. Technology stack verification
  6. Static section integrity
- Configurable validation thresholds
- Detailed error feedback for LLM refinement

#### LLM Integration
- Support for Ollama (local/remote)
- Support for OpenAI API (GPT-4, GPT-3.5, etc)
- Support for mock LLM (testing)
- Extensible client architecture
- Response caching with SHA256 hashing
- Retry logic with exponential backoff
- Configurable temperature and timeout

#### Output Generation
- Markdown resume output
- PDF export with custom styling
- Job title translation
- Timestamped output directories
- Multiple file format support

#### Configuration
- YAML-based configuration file
- 12 master CV mappings
- Multi-language section aliases (8 sections)
- Validation thresholds
- Text corrections (FR, DE)
- Custom CSS styling
- Environment variable overrides

#### Testing
- Unit tests for core functions
- Integration tests with mock LLM
- 80%+ code coverage
- Test fixtures for common scenarios

---

## Planned Features

### Version 1.1.0 (Next Release)
- [ ] Web UI dashboard
- [ ] Batch processing for multiple jobs
- [ ] A/B testing different prompts
- [ ] Integration with LinkedIn API
- [ ] Real-time resume preview
- [ ] Advanced analytics and metrics

### Version 1.2.0
- [ ] Additional language support (Spanish, Italian, Portuguese)
- [ ] New domain types (Consulting, Sales, Operations)
- [ ] Cover letter generation
- [ ] Interview prep suggestions
- [ ] Resume scoring system

### Version 2.0.0
- [ ] Real-time collaboration features
- [ ] Cloud synchronization
- [ ] Mobile app integration
- [ ] AI-powered feedback system
- [ ] Multi-stage application tracking

---

## Version History

### Known Issues

#### 1.0.0
- PDF generation may fail with certain Unicode characters
- Large job descriptions (>10K words) may hit LLM token limits
- Language detection relies on word patterns (not 100% accurate)

### Compatibility

| Version | Python | Status |
|---------|--------|--------|
| 1.0.0 | 3.8-3.11 | ✅ Stable |
| Unreleased | 3.8-3.12 | 🚧 Development |

---

## Migration Guides

### From v0.x to v1.0.0

If upgrading from any pre-1.0.0 version:

1. **Update configuration**
   - Backup your `config.yaml`
   - Use new `config.yaml` template from docs
   - Merge any custom settings

2. **Update dependencies**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. **Test with sample job**
   ```bash
   python -m linguaresume tailor sample_job.txt
   ```

---

## Contributors

### v1.0.0 Release
- Initial development team
- Community feedback and testing

---

## Support

For issues or feature requests, please visit:
- **GitHub Issues**: Report bugs and suggest features
- **Discussions**: Ask questions and share feedback

---

## License

See LICENSE file for details.

---

## Maintenance Notes

### Branches

- `main`: Stable release branch
- `develop`: Development branch for next release
- `feature/*`: Feature branches
- `bugfix/*`: Bug fix branches

### Release Schedule

- Patch releases: As needed for critical bugs
- Minor releases: ~Every 2-3 months for features
- Major releases: As needed for breaking changes

### Support Timeline

| Version | Released | Supported Until |
|---------|----------|-----------------|
| 1.0.0 | 2024-06-02 | 2025-06-02 |
| 1.1.0 | TBD | TBD |

---

## Acknowledgments

Thank you to all contributors and users who help improve LinguaResume!

Special thanks to:
- Ollama project for local inference
- OpenAI for their API
- Playwright for reliable PDF generation
- Jinja2 for powerful templating

---

**Last Updated**: June 2, 2024
