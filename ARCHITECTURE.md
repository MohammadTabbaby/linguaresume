# LinguaResume Architecture

> Detailed technical documentation of the LinguaResume system

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Modules](#core-modules)
3. [Data Flow](#data-flow)
4. [Design Patterns](#design-patterns)
5. [Validation Strategy](#validation-strategy)
6. [Configuration System](#configuration-system)
7. [Extension Points](#extension-points)

---

## System Overview

LinguaResume is built on a modular architecture that separates concerns across distinct layers:

```
┌─────────────────────────────────────────────┐
│           CLI & User Interface               │
│         (cli.py - argparse)                  │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│      Configuration Layer                     │
│  (config.py - YAML parsing & validation)    │
└────────────────────┬────────────────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
┌─────▼────┐  ┌─────▼────┐  ┌─────▼────┐
│  LLM     │  │ Parsing  │  │ Tailoring │
│ Layer    │  │ Layer    │  │ Engine    │
└──────────┘  └──────────┘  └──────┬───┘
                                    │
      ┌─────────────────────────────┼─────────────────────────────┐
      │                             │                             │
┌─────▼──────────┐     ┌──────────▼─────────┐      ┌────────▼────┐
│  Validation    │     │  PDF Rendering     │      │  Output     │
│  Framework     │     │  (Playwright)      │      │  Generation │
└────────────────┘     └────────────────────┘      └─────────────┘
```

### Design Principles

1. **Separation of Concerns** - Each module has a single, well-defined responsibility
2. **Dependency Injection** - Components receive dependencies rather than creating them
3. **Factory Pattern** - CV selection and LLM instantiation use factory logic
4. **Strategy Pattern** - Validation rules are pluggable and composable
5. **Template Method** - Prompt generation uses Jinja2 templates
6. **Caching** - LLM responses cached to optimize cost and performance

---

## Core Modules

### 1. LLM Layer (`linguaresume/llm/`)

#### Purpose
Abstract LLM interactions behind a common interface, supporting multiple providers with caching and retry logic.

#### Components

**`client.py` - Abstract LLM Interface**
```python
class LLMClient(ABC):
    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """Complete a prompt with system and user messages."""
```

**Concrete Implementations:**

1. **OllamaClient**
   - Connects to local or remote Ollama instance
   - Endpoint: `http://localhost:1234/v1/chat/completions`
   - Features:
     - Exponential backoff retry (2 attempts by default)
     - Configurable temperature for output randomness
     - Streaming support (disabled in current implementation)
   - Use Case: Local development, cost-effective inference

2. **OpenAIClient**
   - Uses OpenAI API (GPT-4, GPT-3.5-Turbo, etc.)
   - Authentication via Bearer token
   - Features:
     - Retry logic with exponential backoff
     - Custom base URL support (for Azure OpenAI)
     - Per-request timeout
   - Use Case: Production inference, higher quality outputs

3. **MockLLMClient**
   - Returns pre-defined responses
   - Use Case: Testing, CI/CD pipelines

**`cache.py` - LLM Response Caching**
```python
class LLMCache:
    def get(self, key: str) -> Optional[str]
    def set(self, key: str, value: str) -> None
```

Cache Key Strategy:
- Combines: `model_name:temperature:system_prompt:user_prompt`
- Hash: SHA256 of concatenated string
- Avoids re-computing identical requests
- Persists to disk if `cache_dir` is set

**`prompts.py` - Jinja2 Prompt Templates**

Template System:
- Uses Jinja2 for dynamic prompt generation
- Supports conditional blocks and loops
- Easily maintainable and versioned

Key Templates:

1. **`_MIDDLE_TEMPLATE`** - Main resume tailoring prompt
   - Inputs: job requirements, master CV content, language
   - Output: Tailored Profile + Technical Skills + Experience sections
   - Safety Rules:
     - Enforce exact section headings
     - Preserve bullet count per employer
     - No new technologies added
     - Language-specific output (e.g., French past participles)

2. **`_REQUIREMENTS_TEMPLATE`** - Job description parsing
   - Extracts: must-haves, nice-to-haves, soft skills, job focus
   - Output: Structured JSON for downstream processing

3. **`_TRANSLATE_TEMPLATE`** - Static section translation
   - Translates Education, Languages sections
   - Preserves proper nouns and formatting
   - Maintains table structure

4. **`_TITLE_TRANSLATE_TEMPLATE`** - Job title translation
   - Translates job title to target language
   - Single-line, focused prompt

#### LLM Call Flow

```
User Input (prompt)
        │
        ├─► Cache Lookup (SHA256 hash)
        │   ├─► Hit? Return cached response
        │   └─► Miss? Continue...
        │
        ├─► Prepare Payload
        │   (model name, messages, temperature, options)
        │
        ├─► HTTP POST to LLM
        │   (with timeout & retry logic)
        │
        ├─► Parse Response
        │   (extract message content from JSON)
        │
        ├─► Cache Result
        │
        └─► Return to Caller
```

---

### 2. Parsing Layer (`linguaresume/parsing/`)

#### Purpose
Extract structured information from resume markdown to enable validation and analysis.

#### Components

**`extractor.py` - Content Extraction**

Core Functions:

1. **`load_text(path: str) -> str`**
   - Reads markdown file with UTF-8 encoding
   - Strips BOM if present

2. **`extract_companies(markdown_text: str) -> Set[str]`**
   - Regex: Finds employer names under `### Company Name` headings
   - Returns: Normalized company name set
   - Example: `### Acme Corp, Inc. (2022–2024)` → "Acme Corp, Inc."

3. **`extract_dates(markdown_text: str) -> Set[str]`**
   - Regex: Finds date ranges in `MM/YYYY – MM/YYYY` format
   - Returns: All unique date pairs found
   - Used in validation to ensure dates aren't modified

4. **`extract_total_months(md: str) -> float`**
   - Parses all dates and calculates total months
   - Handles overlapping roles, gaps, etc.
   - Returns: Float (e.g., 48.5 for 4 years 6 months)
   - Critical for experience duration validation

5. **`extract_keywords(text: str, stopwords: Set[str]) -> Set[str]`**
   - Tokenizes text (split on whitespace/punctuation)
   - Removes stopwords (common words in each language)
   - Returns: Significant keyword set
   - Used for tech stack and requirement matching

6. **`_bullet_sections(md: str) -> Dict[str, List[str]]`**
   - Parses bullet points by employer section
   - Returns: `{employer_name: [bullet1, bullet2, ...]}`
   - Used for bullet retention validation

7. **`_sig_tokens(text: str) -> Set[str]`**
   - Extracts significant tokens from text
   - Removes punctuation, normalizes whitespace
   - For token-level similarity comparison

**`splitter.py` - Resume Section Splitting**

Core Functions:

1. **`split_resume_sections(md_text: str, alias_map) -> Tuple[str, List[Tuple[str, str]]]`**
   - Parses markdown headers (## Level 2, ### Level 3)
   - Groups content between headers into sections
   - Returns: Static preamble + [(section_title, section_content), ...]
   - Header normalization handles multi-language aliases

2. **`is_static_section(title: str, static_keys, alias_map) -> bool`**
   - Checks if section title matches static section aliases
   - Static sections: Education, Languages, Certifications
   - Mutable sections: Profile, Technical Skills, Experience

3. **`build_mutable_bundle(sections, static_keys, alias_map) -> str`**
   - Concatenates only mutable sections
   - Used as source for LLM tailoring
   - Contains: Profile + Technical Skills + Experience

4. **`build_static_bundle(sections, static_keys, alias_map) -> str`**
   - Concatenates only static sections
   - Used for translation or verification
   - Contains: Education + Languages + Certifications

5. **`replace_subtitle(header: str, new_subtitle: str) -> str`**
   - Modifies job title in header (e.g., `### Acme Corp, Software Engineer (2022–2024)`)
   - Preserves dates and company name
   - Used when translating job titles

#### Text Normalization
```python
def normalize_text(text: str) -> str:
    # 1. Unicode NFD normalization (decompose accents)
    # 2. Lowercase conversion
    # 3. Whitespace collapsing
    # Returns: Normalized text for comparison
```

Used in company name matching to handle accent variations.

---

### 3. Tailoring Engine (`linguaresume/tailoring/`)

#### Purpose
Orchestrate the complete resume tailoring workflow from job description to polished output.

#### Main Class: `TailoringEngine`

**Constructor**
```python
def __init__(self, config: Config, llm_client: LLMClient):
    self.config = config
    self.llm = llm_client
    self.alias_map = _make_alias_map(config.section_aliases)
```

**Main Method: `tailor(job_description_text: str) -> str`**

Workflow:

```
1. Load Job Description
   ├─ Detect language (EN/FR/DE)
   └─ Extract requirements via LLM (JSON parsing)

2. Classify Domain
   ├─ Analyze keywords against domain patterns
   └─ Determine CV type: fullstack, devops, webdev, other

3. Load Master CV
   ├─ Lookup cv_map[f"{lang}_{domain}"]
   ├─ Fallback to cv_map[domain]
   └─ Final fallback to config.fallback_cv

4. Parse Resume
   ├─ Split into mutable & static sections
   ├─ Extract companies, dates, keywords
   └─ Prepare for validation later

5. Generate Tailored Content
   ├─ Build LLM prompt (requirements + mutable content)
   ├─ Call LLM with system & user prompts
   └─ Extract tailored sections

6. Validate & Retry Loop
   ├─ Run all validation checks
   ├─ If fail: Generate feedback, retry (max 3x)
   └─ If pass: Proceed to output

7. Assemble Final Resume
   ├─ Combine: static sections + tailored sections
   ├─ Translate job title if needed
   └─ Write to markdown file

8. Generate PDF
   └─ Convert markdown to PDF with styling

9. Save Outputs
   └─ outputs/{job_name}/ → {CV.md, CV.pdf, letter.md, etc}
```

**Key Sub-methods:**

1. **`_classify_domain(master_text: str, job_text: str) -> str`**
   - Extracts keywords from master CV and job description
   - Matches against domain-specific patterns
   - Scoring algorithm determines best fit

2. **`detect_language(text: str) -> str`**
   - Pattern-based detection using language-specific word frequencies
   - Common words per language:
     - French: le, la, les, de, et, à, dans, pour, avec
     - German: der, die, das, und, für, mit, von, zu, auf, bei
     - English: the, and, for, with, this, that, from, have, been
   - Counts matches and returns highest scoring language

3. **`extract_requirements() -> Requirement`**
   - Calls LLM with requirements extraction prompt
   - Parses JSON response with robust fallback handling
   - Supports `json_repair` library for malformed JSON
   - Extracts: must-haves, nice-to-haves, soft skills, job focus
   - Domain validation with fallback classification
   - Translates job title to target language if needed

4. **`tailor_middle(master_mutable: str) -> str`**
   - Generates middle prompt with requirements and mutable content
   - Calls LLM with detailed system instructions
   - Extracts content wrapped in `<resume_middle>` XML tags
   - Applies language-specific text corrections (French/German)
   - Enforces consistent heading formatting
   - Returns cleaned markdown content

5. **`validate_final(final_md: str, static_bundle: str) -> ValidationResult`**
   - Comprehensive 6-tier validation:
     1. Company name preservation
     2. Date range validation
     3. Static section integrity
     4. Bullet point retention
     5. Experience duration consistency
     6. Technology stack validation
   - Detects missing Technical Skills section
   - Returns `ValidationResult` with failure details
   - Used in retry loop for feedback generation

6. **`assemble(header: str, tailored_middle: str, static_bundle: str) -> str`**
   - Combines static and tailored sections
   - Translates static sections if needed
   - Updates job title in header (translated if applicable)
   - Ensures proper markdown formatting

7. **`_build_filename_stem() -> str`**
   - Creates professional filename stem: `CV_{Name}_{Role}`
   - Slugifies names and roles for filesystem compatibility
   - Used for all output files (markdown and PDF)

#### Helper Functions

**Text Processing & Cleanup**

1. **`clean_markdown(text: str) -> str`**
   - Strips markdown code blocks (` ``` `)
   - Decodes HTML entities (&amp;, &lt;, &gt;)
   - Fixes escaped parentheses and brackets
   - Removes leading numbers/prefixes
   - Normalizes line endings
   - Ensures trailing newline

2. **`apply_corrections(text: str, corrections: list, master_name: Optional[str]) -> str`**
   - Applies language-specific regex patterns
   - Handles verb conjugation (flags="VERB" for case-insensitive replacement)
   - Removes forbidden sections (e.g., "Compétences" in French)
   - Strips meta-commentary lines
   - Example corrections:
     ```yaml
     corrections_fr:
       - pattern: "avoir fait"
         replacement: "avoir réalisé"
         flags: "IGNORECASE"
     ```
   - Removes header title and strips leading numbers
   - Normalizes excessive newlines (3+ → 2)

3. **`enforce_headings(text: str, target_lang: str) -> str`**
   - Standardizes section headings by language
   - Maps variants to canonical headers:
     - EN: "Profile", "Technical Skills", "Professional Experience", "Education", "Languages"
     - FR: "Profil", "Compétences techniques", "Expérience Professionnelle", "Formation", "Langues"
     - DE: "Profil", "Technische Fähigkeiten", "Berufserfahrung", "Ausbildung", "Sprachen"
   - Handles common typos and alternate spellings
   - Ensures consistency for parsing and validation

4. **`extract_json_object(text: str) -> Optional[dict]`**
   - Robust JSON extraction from LLM responses
   - Handles markdown code block wrapping
   - Attempts direct JSON parsing
   - Falls back to `json_repair` library if available
   - Manual parsing with depth tracking if needed
   - Returns `None` on complete failure
   - Used for requirement extraction from LLM

5. **`slugify(text: str, max_len: int = 40) -> str`**
   - Converts text to URL-safe filename format
   - Unicode normalization (NFKD decomposition)
   - Lowercase with underscore separators
   - Removes special characters
   - Truncates to max length (default 40 chars)
   - Example: "Senior DevOps Engineer" → "senior_devops_engineer"

**Requirement Enhancements**

The `Requirement` dataclass now includes:
- `job_title_translated` - Translated job title in target language
- `failures` - List of validation failures from previous attempts
- `missing_must` - Must-have skills not found in tailored output
- `missing_soft` - Soft skills not found in tailored output

These fields enable the validation feedback loop to communicate specific failures back to the LLM for targeted refinement.

**Junior Position Handling**

When `enable_junior_special_case: true` in config:
- Detects job titles matching `junior_keywords` (e.g., "junior", "débutant", "anfänger")
- Automatically appends "_junior" to domain (e.g., "fullstack_junior")
- Allows organization to maintain separate junior-focused CVs
- Logs detection for transparency

**Configuration Enhancements**

```yaml
# New config options for engine
enable_junior_special_case: true
junior_keywords:
  - "junior"
  - "débutant"     # French
  - "anfänger"     # German
  - "entry-level"
  - "graduate"
```

---

### 4. Validation Framework (`linguaresume/validation/`)

#### Purpose
Ensure tailored resumes maintain factual accuracy and prevent LLM hallucination.

#### Validation Strategy

**Multi-Pass Validation:**
```
Pass 1: Companies
  ├─ Extract companies from master & tailored
  └─ Verify all master companies present in output

Pass 2: Dates
  ├─ Extract date ranges from master & tailored
  └─ Ensure all dates preserved exactly

Pass 3: Bullet Retention
  ├─ Extract bullets from master & tailored per employer
  └─ Calculate token overlap (must exceed threshold)

Pass 4: Experience Duration
  ├─ Calculate total months from master
  ├─ Calculate total months from tailored
  └─ Verify difference ≤ 1% (allow rounding)

Pass 5: Tech Stack
  ├─ Extract technologies from master
  └─ Ensure tailored doesn't add new tech

Pass 6: Static Sections
  ├─ Extract Education, Languages, etc.
  └─ Verify exact preservation in tailored
```

**Validation Rules (`validation/*.py`):**

1. **`companies.py`**
   ```python
   def validate_companies(final_md: str, master_companies: Set[str], 
                         translating: bool = False) -> bool
   ```
   - Checks: All master companies present in final MD
   - Fuzzy matching handles accents/capitalization
   - Special case: Allow missing companies during translation

2. **`dates.py`**
   ```python
   def validate_dates(final_md: str, master_dates: Set[str]) -> bool
   ```
   - Checks: All master date ranges preserved
   - Exact string matching (allows reordering)

3. **`bullets.py`**
   ```python
   def validate_bullet_retention(master_md: str, final_md: str, 
                                retention_threshold: float = 0.60) -> bool
   ```
   - Algorithm:
     1. Extract bullets per employer from both versions
     2. For each employer, compare bullet count:
        - Master: 4 bullets
        - Final: 3 bullets (75% retention) ✓
     3. Calculate token-level overlap (min 35%)
     4. Enforce: bullets_count_final ≥ retention_threshold × bullets_count_master
   - Threshold: Default 60% (configurable)

4. **`experience.py`**
   ```python
   def validate_experience(master_md: str, tailored_md: str) -> bool
   ```
   - Calculates total months from date ranges
   - Allows ±1 month difference (rounding tolerance)
   - Example: 60 months → 60.5 months is OK

5. **`tech.py` - TechValidator**
   ```python
   class TechValidator:
       def validate(self, master_tech: Set[str], 
                   tailored_tech: Set[str]) -> bool
   ```
   - Parses technology stack from skill tables
   - Ensures tailored ⊆ master (no new tech added)
   - Handles tech aliases (e.g., "Node.js" vs "Node")

6. **`static.py`**
   ```python
   def validate_static_sections(final_md: str, static_bundle: str, 
                               alias_map: Dict, static_keys: List[str]) -> bool
   ```
   - Verifies Education/Languages sections untouched
   - Compares normalized text (ignores whitespace)

#### Validation Feedback Loop

When validation fails:

```python
# Example validation failure
missing_companies = ["Acme Corp"]
error_feedback = """
VALIDATION FAILED:
- Missing companies: Acme Corp
  (present in master CV, not in tailored output)

Please regenerate the resume ensuring:
1. All employer names are mentioned
2. Date ranges are exact
3. No new technologies are added
4. Bullet points are preserved from master
"""

# Retry prompt includes detailed feedback
retry_prompt = f"{base_prompt}\n\n{feedback}"
response = llm.complete(system, retry_prompt)
```

---

### 5. PDF Rendering (`linguaresume/pdf/`)

#### Purpose
Convert markdown resumes to professional PDF documents.

#### Components

**`renderer.py` - PDFRenderer Class**

```python
class PDFRenderer:
    def __init__(self, css: Optional[str] = None):
        # CSS for styling
        # Uses Playwright for browser automation
    
    def render(self, markdown_text: str, output_path: str) -> None:
        # 1. Convert markdown → HTML
        # 2. Apply CSS styling
        # 3. Render HTML → PDF via Playwright
```

**Process:**

1. **Markdown → HTML**
   - Uses `markdown` library with extensions
   - Preserves table formatting
   - Converts links to interactive PDF links

2. **CSS Styling**
   - Default CSS: Professional resume styling
   - Custom CSS: Overrideable via `config.resume_css`
   - Features:
     - Font: Segoe UI / Arial fallback
     - Margins: 0.5 inch
     - Tables: Bordered styling
     - Links: Blue, underlined

3. **HTML → PDF**
   - Uses Playwright (Chromium backend)
   - Headless browser rendering
   - High-quality PDF output (300 DPI equivalent)
   - Preserves interactive links

**CSS Customization:**
```css
/* Example: config.resume_css */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 10pt;
    line-height: 1.4;
    margin: 0.5in;
}

h2 {
    border-bottom: 2px solid #333;
    padding-bottom: 5px;
    margin-top: 12px;
}

table {
    width: 100%;
    border-collapse: collapse;
}

table, th, td {
    border: 1px solid #ddd;
    padding: 8px;
}
```

---

### 6. Configuration System (`linguaresume/config.py`)

#### Purpose
Centralized configuration management with YAML-based declarative setup.

#### Config Hierarchy

```
config.yaml (disk)
    ↓
YAML parsing (PyYAML)
    ↓
Config dataclass (type-safe)
    ↓
Runtime access (singleton pattern)
```

#### Configuration Structure

```yaml
# LLM Provider
ollama:
  url: "http://127.0.0.1:1234/v1/chat/completions"
  model: "qwen/qwen3.5-9b"
  timeout: 720
  temperature: 0.3

# Master CV Mapping (language × domain)
cv_map:
  # Language-specific (checked first)
  fr_fullstack: "./cvs/master_fr.md"
  de_webdev: "./cvs/web_de.md"
  # ... 
  # Fallback (checked second)
  fullstack: "./cvs/master_en.md"
  webdev: "./cvs/web_en.md"
  # ...
  fallback_cv: "./cvs/master_en.md"

# Output Configuration
output:
  subdir: "outputs"
  max_retries: 3

# Section Aliases (multi-language support)
section_aliases:
  profile:
    - "Profil"           # German
    - "Profile"          # English
    - "Profil Professionnel"  # French
  technical_skills:
    - "Technische Fähigkeiten"
    - "Technical Skills"
    - "Compétences techniques"
  # ... other sections

# Validation Thresholds
validation:
  bullet_token_overlap_threshold: 0.35
  bullet_retention_threshold: 0.60

# Language-specific Corrections
corrections_fr:
  - search: "avoir fait"
    replace: "avoir réalisé"
corrections_de:
  - search: "haben gemacht"
    replace: "haben durchgeführt"

# Stopwords for keyword extraction
stopwords:
  - "the"
  - "and"
  - "or"
  # ... (100+ words)
```

#### CV Selection Algorithm

```python
def select_cv(job_language: str, domain: str) -> str:
    # Priority 1: Exact language + domain match
    key = f"{job_language}_{domain}"
    if key in cv_map:
        return cv_map[key]
    
    # Priority 2: Domain only (English fallback)
    if domain in cv_map:
        return cv_map[domain]
    
    # Priority 3: Global fallback
    return config.fallback_cv
```

Example:
```
French + DevOps
  → Check "fr_devops" ✓ Found! → ./cvs/devops_fr.md

German + NonTech
  → Check "de_nontech" ✗ Not found
  → Check "nontech" ✓ Found! → ./cvs/nontech_master_en.md

Spanish + FullStack
  → Check "es_fullstack" ✗ Not found
  → Check "fullstack" ✓ Found! → ./cvs/master_en.md
```

---

## Data Flow

### Complete Workflow Sequence

```
┌─────────────────────────────────────┐
│ 1. User Input: Job Description      │
│    (Text file or CLI argument)       │
└──────────────┬──────────────────────┘

┌──────────────▼──────────────────────┐
│ 2. Load Configuration                │
│    - Parse config.yaml               │
│    - Initialize LLM client           │
│    - Load section aliases            │
└──────────────┬──────────────────────┘

┌──────────────▼──────────────────────┐
│ 3. Detect Language & Domain          │
│    - Language: detect_language()     │
│    - Domain: _classify_domain()      │
│    Result: "fr", "devops"            │
└──────────────┬──────────────────────┘

┌──────────────▼──────────────────────┐
│ 4. Select Master CV                  │
│    - Lookup: cv_map["fr_devops"]     │
│    - Load: ./cvs/devops_fr.md        │
└──────────────┬──────────────────────┘

┌──────────────▼──────────────────────┐
│ 5. Parse Master CV                   │
│    - Extract: companies, dates       │
│    - Split: mutable vs static        │
│    - Count: bullets per employer     │
└──────────────┬──────────────────────┘

┌──────────────▼──────────────────────┐
│ 6. Extract Job Requirements          │
│    - Call LLM with job description   │
│    - Parse JSON: must-haves, skills  │
│    - Result: Requirement object      │
└──────────────┬──────────────────────┘

┌──────────────▼──────────────────────┐
│ 7. Generate Tailoring Prompt         │
│    - Use Jinja2 template             │
│    - Fill: requirements + mutable    │
│    - System prompt: role instruction │
│    - User prompt: detailed task      │
└──────────────┬──────────────────────┘

┌──────────────▼──────────────────────┐
│ 8. Call LLM                          │
│    - Cache lookup                    │
│    - HTTP POST to Ollama/OpenAI      │
│    - Parse response                  │
│    - Cache result                    │
└──────────────┬──────────────────────┘

┌──────────────▼──────────────────────┐
│ 9. Validate Output (Attempt 1)       │
│    - Check companies                 │
│    - Check dates                     │
│    - Check bullets                   │
│    - Check experience duration       │
│    - Check tech stack                │
│    - Check static sections           │
└──────────┬──────────────────────────┘
           │
      ┌────▼──────────┐
      │   All Valid?  │
      └┬──────────┬───┘
       │          │
      YES        NO
       │          │
       │    ┌─────▼─────────────────┐
       │    │ 10. Generate Feedback │
       │    │ - Missing companies   │
       │    │ - Bullet count low    │
       │    │ - New tech detected   │
       │    └──────────┬────────────┘
       │               │
       │    ┌──────────▼─────────────┐
       │    │ 11. Retry Loop         │
       │    │ - Max 3 attempts       │
       │    │ - Append feedback      │
       │    │ - Call LLM again       │
       │    │ - Goto step 9          │
       │    └────────────────────────┘
       │
       └─────────────┬──────────────┐
                     │              │
         ┌───────────▼──────┐       │
         │ All Attempts OK? │       │
         └┬────────────┬────┘       │
          │            │           │
         YES          NO           │
          │            │           │
          │      ┌─────▼───────────┤
          │      │ Log Error       │
          │      │ Exit (fail)     │
          │      └─────────────────┤
          │                        │
┌─────────▼─────────────────────────┐
│ 12. Assemble Final Resume          │
│    - Combine: static + tailored    │
│    - Preserve: formatting          │
└──────────────┬────────────────────┘

┌──────────────▼────────────────────┐
│ 13. Translate Job Title            │
│    - Call LLM for translation      │
│    - Update header                 │
└──────────────┬────────────────────┘

┌──────────────▼────────────────────┐
│ 14. Generate PDF                   │
│    - Markdown → HTML               │
│    - Apply CSS styling             │
│    - Render with Playwright        │
└──────────────┬────────────────────┘

┌──────────────▼────────────────────┐
│ 15. Save Outputs                   │
│    - outputs/{job_name}/           │
│    - {CV.md, CV.pdf}               │
│    - [letter.md, letter.pdf]       │
└────────────────────────────────────┘
```

---

## Design Patterns

### 1. Strategy Pattern (LLM Selection)

```python
# Abstract strategy
class LLMClient(ABC):
    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        pass

# Concrete strategies
class OllamaClient(LLMClient):
    def complete(self, system: str, user: str) -> str:
        # Ollama implementation
        
class OpenAIClient(LLMClient):
    def complete(self, system: str, user: str) -> str:
        # OpenAI implementation

# Factory
def _build_llm_client(cfg: Config, api_key: Optional[str] = None) -> LLMClient:
    if api_key:
        return OpenAIClient(api_key)
    else:
        return OllamaClient(cfg.ollama.url, cfg.ollama.model)
```

### 2. Template Method Pattern (Validation)

```python
# Base validation runner
def validate_all(resume_md, master_md, config):
    validators = [
        (validate_companies, "companies"),
        (validate_dates, "dates"),
        (validate_bullets, "bullets"),
        (validate_experience, "experience"),
        (validate_tech_stack, "tech"),
        (validate_static, "static"),
    ]
    
    failures = []
    for validator_func, name in validators:
        try:
            if not validator_func(...):
                failures.append(name)
        except Exception as e:
            failures.append(f"{name}: {e}")
    
    return len(failures) == 0, failures

# Each validator implements the contract:
def validate_companies(...) -> bool:
    pass  # Custom logic
```

### 3. Factory Pattern (CV Selection)

```python
class CVFactory:
    @staticmethod
    def select_cv(job_lang: str, domain: str, 
                  cv_map: Dict[str, str],
                  fallback: str) -> str:
        # Try language-specific first
        key = f"{job_lang}_{domain}"
        if key in cv_map:
            return cv_map[key]
        
        # Try domain-only
        if domain in cv_map:
            return cv_map[domain]
        
        # Final fallback
        return fallback
```

### 4. Builder Pattern (Resume Assembly)

```python
class ResumeBuilder:
    def __init__(self):
        self.sections = {}
    
    def add_static_sections(self, content: str) -> "ResumeBuilder":
        self.sections["static"] = content
        return self
    
    def add_mutable_sections(self, content: str) -> "ResumeBuilder":
        self.sections["mutable"] = content
        return self
    
    def translate_title(self, title: str) -> "ResumeBuilder":
        self.sections["title"] = title
        return self
    
    def build(self) -> str:
        return "\n".join([
            self.sections["title"],
            self.sections["static"],
            self.sections["mutable"],
        ])
```

### 5. Chain of Responsibility (Validation Feedback)

```python
class ValidationFeedbackChain:
    def generate_feedback(self, failures: List[str]) -> str:
        feedback_parts = []
        
        for failure in failures:
            handler = self._get_handler(failure)
            feedback_parts.append(handler.generate(failure))
        
        return "\n".join(feedback_parts)
    
    def _get_handler(self, failure: str) -> FeedbackHandler:
        # Route to appropriate handler
        if "companies" in failure:
            return CompanyFeedbackHandler()
        elif "dates" in failure:
            return DateFeedbackHandler()
        # ... etc
```

---

## Configuration System Details

### Priority Order

1. **config.yaml** (default)
2. **Environment Variables** (override)
3. **CLI Arguments** (highest priority)

### Example: OpenAI Override

```bash
# Default: uses Ollama from config.yaml
python -m linguaresume tailor job.txt

# Override: use OpenAI
OPENAI_API_KEY=sk-... python -m linguaresume tailor job.txt

# CLI argument
python -m linguaresume tailor job.txt --llm openai --model gpt-4
```

### Validation Configuration

```yaml
validation:
  # Bullet token overlap threshold
  # If master bullet has 100 tokens, final must have ≥35% overlap
  bullet_token_overlap_threshold: 0.35
  
  # Bullet retention threshold
  # If master has 4 bullets, final must have ≥2.4 (~2) bullets
  bullet_retention_threshold: 0.60
```

Tuning Guide:
- Looser validation: Decrease thresholds (0.3, 0.5)
- Stricter validation: Increase thresholds (0.5, 0.7)
- More retries: Increase output.max_retries (default: 3)

---

## Extension Points

### 1. Add a New LLM Provider

```python
# In linguaresume/llm/client.py
class AnthropicClient(LLMClient):
    def __init__(self, api_key: str, model: str = "claude-3-opus"):
        self.api_key = api_key
        self.model = model
    
    def complete(self, system: str, user: str) -> str:
        # Implement Anthropic API integration
        pass

# Register in CLI
def _build_llm_client(cfg, api_key=None, llm_type=None):
    if llm_type == "anthropic":
        return AnthropicClient(api_key)
    # ... existing logic
```

### 2. Add a New Validation Rule

```python
# In linguaresume/validation/custom.py
def validate_custom_rule(master_md: str, final_md: str) -> bool:
    """Custom validation logic."""
    master_data = extract_custom_data(master_md)
    final_data = extract_custom_data(final_md)
    return check_rule(master_data, final_data)

# Register in TailoringEngine
def _validate_and_retry(...):
    validators = [
        (validate_companies, "companies"),
        (validate_custom_rule, "custom"),  # Add here
        # ...
    ]
```

### 3. Add a New Language

1. Create new master CVs for the language
2. Add language codes to `section_aliases` in config.yaml
3. Update `detect_language()` in tailoring engine
4. Add stopwords for the language
5. Test with sample job descriptions

### 4. Add a New Domain

1. Create domain-specific master CVs
2. Update `cv_map` in config.yaml with new entries
3. Add domain keywords to classification logic
4. Test domain detection with sample jobs

---

## Performance Considerations

### Optimization Strategies

1. **Caching**
   - LLM responses cached by prompt hash
   - Avoids redundant API calls
   - ~90% cache hit rate in typical usage

2. **Lazy Loading**
   - CVs loaded only when needed
   - Section parsing deferred until validation

3. **Parallel Processing**
   - Future: Batch multiple job descriptions
   - Validation rules could run in parallel

4. **Resource Management**
   - Playwright browser instance reused
   - Session pooling for HTTP requests
   - Memory-efficient string handling

### Benchmarks (Estimated)

- Language detection: < 10ms
- Domain classification: < 50ms
- Master CV loading & parsing: < 100ms
- LLM call (Ollama): 5-30 seconds
- Validation: < 500ms
- PDF rendering: 1-3 seconds

**Total time per application: 10-35 seconds** (excluding LLM wait time)

---

## Security Considerations

### Input Validation
- File paths validated to prevent directory traversal
- Job descriptions sanitized before LLM calls
- Configuration values type-checked

### API Key Handling
- API keys passed via environment variables (never in config)
- No logging of sensitive data
- Timeout protection against hung requests

### Output Sanitization
- Markdown escaped to prevent injection
- PDF generation sandboxed in Playwright
- File permissions set appropriately

---

## Testing Strategy

### Test Coverage

1. **Unit Tests**
   - LLM client implementations
   - Text parsing and extraction
   - Validation rules
   - Configuration loading

2. **Integration Tests**
   - End-to-end workflow with mock LLM
   - CV selection logic
   - Resume assembly and output

3. **Mock LLM**
   - Pre-defined responses for testing
   - Allows reproducible validation testing
   - No external API dependency

### Running Tests

```bash
pytest tests/                          # Run all tests
pytest tests/test_engine_mockllm.py   # Integration tests
pytest -v                              # Verbose output
pytest --cov                           # Coverage report
```

---

## Glossary

| Term | Definition |
|------|-----------|
| **Master CV** | Template resume for a specific domain and language |
| **Mutable Sections** | Profile, Technical Skills, Professional Experience (tailored) |
| **Static Sections** | Education, Languages, Certifications (preserved) |
| **Requirement** | Job description parsed into structured requirements |
| **Validation** | Checking that tailored resume maintains factual accuracy |
| **Retry Loop** | Repeated LLM calls with feedback when validation fails |
| **Cache Key** | SHA256 hash of model + temperature + prompt |
| **Section Alias** | Multi-language mapping for resume section headers |
| **Domain Classification** | Determining CV type (fullstack, devops, webdev, other) |
| **Language Detection** | Identifying job description language (EN, FR, DE) |

---

## References

- [Python dataclasses](https://docs.python.org/3.8/library/dataclasses.html)
- [Jinja2 templating](https://jinja.palletsprojects.com/)
- [PyYAML](https://pyyaml.org/)
- [Playwright](https://playwright.dev/)
- [OpenAI API](https://platform.openai.com/docs/api-reference)
