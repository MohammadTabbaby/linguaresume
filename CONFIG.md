# LinguaResume Configuration Reference

> Detailed configuration options and advanced customization

## Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [LLM Configuration](#llm-configuration)
3. [CV Mapping](#cv-mapping)
4. [Validation Settings](#validation-settings)
5. [Output Configuration](#output-configuration)
6. [Section Aliases](#section-aliases)
7. [Text Corrections](#text-corrections)
8. [Styling (CSS)](#styling-css)
9. [Advanced Options](#advanced-options)
10. [Examples](#examples)

---

## Configuration Overview

LinguaResume uses a single YAML configuration file: `config.yaml`

### Configuration Loading Hierarchy

1. **Default**: `config.yaml` in project root
2. **Custom**: Pass path as argument: `--config /path/to/custom.yaml`
3. **Environment**: Override specific values with env vars
4. **CLI Arguments**: Command-line flags (highest priority)

### Configuration Structure

```yaml
# Section 1: LLM Provider
ollama: { ... }

# Section 2: Master CV Mapping
cv_map: { ... }
fallback_cv: "..."

# Section 3: Output
output: { ... }

# Section 4: Validation
validation: { ... }

# Section 5: Resume Structure
section_aliases: { ... }
static_section_keys: [...]

# Section 6: Special Handling
junior_keywords: [...]
enable_junior_special_case: true

# Section 7: Text Processing
corrections_fr: [...]
corrections_de: [...]
stopwords: [...]

# Section 8: Styling
resume_css: "..."
```

---

## LLM Configuration

### Ollama Configuration

```yaml
ollama:
  url: "http://127.0.0.1:1234/v1/chat/completions"
  model: "qwen/qwen3.5-9b"
  timeout: 720
  temperature: 0.3
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | `http://127.0.0.1:1234/v1/chat/completions` | Ollama API endpoint (local or remote) |
| `model` | string | `qwen/qwen3.5-9b` | Model name (see `ollama list`) |
| `timeout` | integer | `720` | Request timeout in seconds (12 min) |
| `temperature` | float | `0.3` | Response randomness (0.0-1.0) |

#### Environment Variables

```bash
# Override via env vars
export OLLAMA_URL="http://192.168.1.100:11434/v1/chat/completions"
export OLLAMA_MODEL="mistral:7b-instruct"
export OLLAMA_TIMEOUT="1800"
export OLLAMA_TEMPERATURE="0.1"
```

#### URL Examples

```yaml
# Default (localhost)
url: "http://127.0.0.1:1234/v1/chat/completions"

# Newer Ollama versions (check your setup)
url: "http://127.0.0.1:11434/v1/chat/completions"

# Remote Ollama (Docker/Cloud)
url: "http://ollama.example.com:11434/v1/chat/completions"

# Behind reverse proxy (Nginx)
url: "http://proxy.example.com/ollama/v1/chat/completions"
```

#### Model Selection

**Recommended for Resume Tailoring:**

| Model | Size | VRAM | Speed | Quality | Notes |
|-------|------|------|-------|---------|-------|
| `mistral:7b-instruct-q4_0` | 4B | 4GB | Fast | Good | Best balance |
| `qwen:9b-chat-v1.5-q8_0` | 5.5GB | 6GB | Balanced | Excellent | Multilingual |
| `neural-chat:7b-q4_0` | 4B | 4GB | Very Fast | Good | Fast inference |
| `phi:2.7b` | 1.6GB | 2GB | Very Fast | Fair | Minimal hardware |
| `llama2:13b-chat-q8_0` | 7.4GB | 8GB | Slower | Excellent | Higher quality |

**Pull models:**
```bash
ollama pull mistral:7b-instruct-q4_0
ollama pull qwen:9b-chat-v1.5
ollama pull neural-chat:7b
```

#### Temperature Tuning

| Temperature | Output | Use Case |
|-------------|--------|----------|
| 0.0 | Deterministic | Resume tailoring (preferred) |
| 0.1 | Very focused | Factual accuracy priority |
| 0.3 | Balanced | Default (good mix) |
| 0.5 | Varied | Creative options |
| 0.8 | Creative | Brainstorming |
| 1.0 | Random | Testing only |

**Recommendation**: `0.1-0.3` for resume work (more consistent results)

### OpenAI Configuration

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-4o-mini"
export OPENAI_BASE_URL="https://api.openai.com/v1"
```

#### Environment Variables

| Variable | Default | Example |
|----------|---------|---------|
| `OPENAI_API_KEY` | - | `sk-proj-...` |
| `OPENAI_MODEL` | `gpt-4o-mini` | `gpt-4`, `gpt-3.5-turbo` |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Azure: `https://your-resource.openai.azure.com/` |
| `OPENAI_TIMEOUT` | `120` | `300` (seconds) |

#### Model Comparison

| Model | Cost/1K tokens | Quality | Speed | Recommended |
|-------|----------------|---------|-------|-------------|
| `gpt-4o` | $0.005 | Excellent | Moderate | ✅ Best quality |
| `gpt-4o-mini` | $0.00015 | Very Good | Fast | ✅ Best value |
| `gpt-4-turbo` | $0.01 | Excellent | Slow | For complex tasks |
| `gpt-3.5-turbo` | $0.0005 | Good | Fast | Budget option |

---

## CV Mapping

### Overview

Maps job characteristics (language, domain) to master CV files.

```yaml
cv_map:
  # Priority 1: Language + Domain (language-specific)
  fr_fullstack: "./cvs/master_fr.md"
  de_devops: "./cvs/devops_de.md"
  
  # Priority 2: Domain only (English fallback)
  fullstack: "./cvs/master_en.md"
  devops: "./cvs/devops_en.md"
  
  # Priority 3: Ultimate fallback
  fallback_cv: "./cvs/master_en.md"
```

### Lookup Algorithm

```
Job Language: FR
Job Domain: DEVOPS
  ↓
1. cv_map["fr_devops"] → ./cvs/devops_fr.md ✓ Found!
   Return this CV
   
Job Language: ES (Spanish - not supported)
Job Domain: FULLSTACK
  ↓
1. cv_map["es_fullstack"] → Not found ✗
2. cv_map["fullstack"] → ./cvs/master_en.md ✓ Found!
   Return this CV
```

### Available Domains

| Domain | Type | Examples |
|--------|------|----------|
| `fullstack` | Full-Stack Engineer | Backend + Frontend + DevOps |
| `devops` | DevOps/Cloud Engineer | Kubernetes, CI/CD, Infrastructure |
| `webdev` | Web Developer | Frontend-focused |
| `other` | Non-Technical | IT Support, Project Manager |

### Language Support

| Code | Language | Status |
|------|----------|--------|
| `en` | English | ✅ Full |
| `fr` | French | ✅ Full |
| `de` | German | ✅ Full |
| `es` | Spanish | ❌ Not included (fallback to English) |
| `it` | Italian | ❌ Not included (fallback to English) |

### Adding New Domains

1. Create master CVs:
   ```
   cvs/newdomain_en.md
   cvs/newdomain_fr.md
   cvs/newdomain_de.md
   ```

2. Update config:
   ```yaml
   cv_map:
     fr_newdomain: "./cvs/newdomain_fr.md"
     de_newdomain: "./cvs/newdomain_de.md"
     newdomain: "./cvs/newdomain_en.md"
   ```

3. Update domain classification in `linguaresume/tailoring/engine.py`:
   ```python
   def _classify_domain(self, master_text, job_text):
       # Add keywords for new domain
       domain_keywords = {
           "newdomain": ["keyword1", "keyword2", ...]
       }
   ```

---

## Validation Settings

### Bullet Token Overlap Threshold

```yaml
validation:
  bullet_token_overlap_threshold: 0.35
```

**Definition**: Minimum fraction of tokens (words) in original bullet that must appear in tailored version.

**Example**:
```
Master bullet:
"Implemented microservices architecture using Docker and Kubernetes"
(words: implemented, microservices, architecture, docker, kubernetes = 5 significant tokens)

Tailored bullet:
"Engineered microservices with Docker and Kubernetes containers"
(words: engineered, microservices, docker, kubernetes = 4 significant tokens)

Overlap: 4/5 = 80% ✓ (exceeds 0.35 threshold)
```

**Tuning**:
- **Stricter** (0.5-0.8): Requires more content preservation
- **Looser** (0.1-0.3): Allows more aggressive rewording
- **Default** (0.35): Balanced approach

### Bullet Retention Threshold

```yaml
validation:
  bullet_retention_threshold: 0.60
```

**Definition**: Minimum fraction of bullet points to retain from master resume per employer.

**Example**:
```
Master CV - Employer: Acme Corp (4 bullets)
- Managed team of 5 engineers
- Led microservices migration
- Improved deployment speed by 40%
- Mentored junior developers

Tailored CV - Employer: Acme Corp (3 bullets)
- Managed team and led architecture changes
- Improved deployment speed by 40%
- Mentored engineers

Retention: 3/4 = 75% ✓ (exceeds 0.60 threshold)
```

**Tuning**:
- **Stricter** (0.7-0.9): Force LLM to keep most bullets
- **Looser** (0.3-0.5): Allow aggressive consolidation
- **Default** (0.60): Reasonable balance

### Validation Configuration Example

```yaml
# Strict validation
validation:
  bullet_token_overlap_threshold: 0.5
  bullet_retention_threshold: 0.75

output:
  max_retries: 5  # More attempts to pass

# Loose validation
validation:
  bullet_token_overlap_threshold: 0.2
  bullet_retention_threshold: 0.40

output:
  max_retries: 1  # Fewer retries
```

---

## Output Configuration

```yaml
output:
  subdir: "outputs"
  max_retries: 3
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `subdir` | string | `outputs` | Directory for generated resumes |
| `max_retries` | integer | `3` | Max retry attempts if validation fails |

### Output Structure

```
outputs/
├── job_name_1/
│   ├── CV.md
│   ├── CV.pdf
│   ├── letter.md
│   └── letter.pdf
├── job_name_2/
│   ├── CV.md
│   ├── CV.pdf
│   └── ...
└── ...
```

### Job Name Generation

Job name derived from:
1. Job title (if provided)
2. Job description filename
3. Timestamp (if both unavailable)

Examples:
```
input: job_description.txt
  → outputs/job_description/

input: "Senior DevOps Engineer"
  → outputs/senior_devops_engineer/

input: 2024-06-02-job.txt
  → outputs/2024_06_02_job/
```

### Custom Output Directory

```bash
# Via CLI
python -m linguaresume tailor job.txt --output /custom/path

# Or in code
from linguaresume.config import Config
config = Config.from_yaml("config.yaml")
config.output.subdir = "/custom/path"
```

---

## Section Aliases

### Purpose

Enable parsing of resumes in multiple languages by mapping header variations.

```yaml
section_aliases:
  profile:
    - "Profil"           # German
    - "Profile"          # English
    - "Professional Profile"
    - "Profil Professionnel"  # French
    - "Résumé"
```

### Complete Section Aliases

```yaml
section_aliases:
  # PROFILE SECTION
  profile:
    - "Profil"
    - "Profile"
    - "Professional Profile"
    - "Profil Professionnel"
    - "Résumé"
    - "Resume"
    - "Summary"
  
  # TECHNICAL SKILLS
  technical_skills:
    - "Technische Fähigkeiten"
    - "Technical Skills"
    - "Technical Skills Stack"
    - "Compétences Techniques"
    - "Compétences"
    - "Skills"
    - "Fähigkeiten"
  
  # PROFESSIONAL EXPERIENCE
  professional_experience:
    - "Berufserfahrung"
    - "Professional Experience"
    - "Expérience Professionnelle"
    - "Experience"
    - "Work Experience"
    - "Travail"
    - "Erfahrung"
  
  # EDUCATION
  education:
    - "Ausbildung"
    - "Education"
    - "Formation"
    - "Éducation"
    - "Degree"
  
  # LANGUAGES
  languages:
    - "Sprachen"
    - "Languages"
    - "Langues"
    - "Sprachkenntnisse"
    - "Linguistic Skills"

  # CERTIFICATIONS (optional)
  certifications:
    - "Zertifizierungen"
    - "Certifications"
    - "Certifications Professionnelles"
    - "Credentials"
```

### Static vs Mutable Sections

```yaml
static_section_keys:
  - "education"
  - "languages"
  - "certifications"

# Everything else is mutable:
# - profile
# - technical_skills
# - professional_experience
```

**Static Sections**: Preserved exactly during tailoring
**Mutable Sections**: Rewritten to match job requirements

### Adding New Section Aliases

```yaml
section_aliases:
  # Existing sections...
  
  # Add new section
  projects:
    - "Projekte"
    - "Projects"
    - "Key Projects"
    - "Projets"
```

---

## Text Corrections

### French Corrections

```yaml
corrections_fr:
  - search: "avoir fait"
    replace: "avoir réalisé"
  - search: "faire de"
    replace: "réaliser"
  - search: "très important"
    replace: "primordial"
```

**Purpose**: Fix grammar, word choice, or improve language quality after LLM generation.

**Format**:
```yaml
corrections_X:
  - search: "original text"
    replace: "corrected text"
```

### German Corrections

```yaml
corrections_de:
  - search: "haben gemacht"
    replace: "haben durchgeführt"
  - search: "Fähigkeit"
    replace: "Kompetenz"
  - search: "sehr"
    replace: "äußerst"
```

### English Corrections

```yaml
corrections_en: []  # Usually not needed
```

### Using Regex

```yaml
corrections_fr:
  # Simple text replacement
  - search: "avoir fait"
    replace: "avoir réalisé"
  
  # Regex (future enhancement)
  # - search: "\\b(very|quite) (good|nice)\\b"
  #   replace: "excellent"
```

---

## Styling (CSS)

### Resume CSS

```yaml
resume_css: |
  body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 10pt;
    line-height: 1.4;
    margin: 0.5in;
    color: #333;
  }
  
  h1 {
    font-size: 18pt;
    margin-top: 0;
    margin-bottom: 5px;
  }
  
  h2 {
    font-size: 12pt;
    border-bottom: 2px solid #333;
    padding-bottom: 5px;
    margin-top: 12px;
    margin-bottom: 8px;
  }
  
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0;
  }
  
  table, th, td {
    border: 1px solid #ddd;
    padding: 8px;
  }
  
  a {
    color: #0066cc;
  }
```

### Style Presets

#### Modern Blue

```yaml
resume_css: |
  body {
    font-family: 'Helvetica Neue', sans-serif;
    font-size: 10pt;
    margin: 0.75in;
  }
  
  h2 {
    color: #0066cc;
    border-bottom: 3px solid #0066cc;
  }
```

#### Classic Black & White

```yaml
resume_css: |
  body {
    font-family: 'Times New Roman', serif;
    font-size: 11pt;
    margin: 0.5in;
  }
  
  h2 {
    border-bottom: 2px solid #000;
  }
```

#### Minimalist

```yaml
resume_css: |
  body {
    font-family: 'Monaco', monospace;
    font-size: 9pt;
    margin: 0.5in;
    line-height: 1.3;
  }
  
  h2 {
    border: none;
    border-top: 1px solid #000;
  }
  
  table {
    border: none;
  }
  
  td {
    border: none;
  }
```

### Custom Styling Example

```yaml
resume_css: |
  /* Custom fonts */
  @import url('https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap');
  
  body {
    font-family: 'Lato', sans-serif;
    font-size: 10pt;
    margin: 0.6in 0.8in;
    color: #2c3e50;
  }
  
  /* Header styling */
  h1 {
    font-size: 20pt;
    font-weight: 700;
    margin: 0;
    color: #2c3e50;
  }
  
  /* Section headers */
  h2 {
    font-size: 12pt;
    font-weight: 700;
    color: #fff;
    background-color: #34495e;
    padding: 5px 10px;
    margin: 10px 0 5px 0;
  }
  
  /* Subsections */
  h3 {
    font-size: 11pt;
    font-weight: 700;
    margin: 5px 0 2px 0;
  }
  
  /* Tables for skills */
  table {
    width: 100%;
    margin: 8px 0;
  }
  
  td {
    padding: 6px;
    border: 1px solid #ecf0f1;
  }
  
  /* Links */
  a {
    color: #3498db;
    text-decoration: none;
  }
  
  a:hover {
    text-decoration: underline;
  }
  
  /* Lists */
  ul {
    margin: 4px 0;
    padding-left: 18px;
  }
  
  li {
    margin-bottom: 2px;
  }
```

---

## Advanced Options

### Junior Position Handling

```yaml
junior_keywords:
  - "junior"
  - "entry-level"
  - "débutant"
  - "anfänger"
  - "graduate"
  - "recent graduate"

enable_junior_special_case: true
```

**When enabled**: 
- Detects junior-level positions
- May adjust tailoring strategy
- Could emphasize learning and growth

### Stopwords

```yaml
stopwords:
  # English
  - "the"
  - "and"
  - "for"
  # French
  - "le"
  - "la"
  - "et"
  # German
  - "der"
  - "die"
  - "und"
```

**Purpose**: Ignore common words in keyword extraction to focus on significant terms.

### Cache Configuration

```yaml
# Not directly in config.yaml, but in code:
# from linguaresume.llm.cache import LLMCache
# cache = LLMCache(cache_dir="/tmp/llm_cache")
```

---

## Examples

### Configuration 1: Production (OpenAI + Strict)

```yaml
# Use premium API for quality, strict validation
ollama:
  url: "http://127.0.0.1:11434/v1/chat/completions"
  model: "fallback"
  timeout: 120
  temperature: 0.1

cv_map:
  fr_fullstack: "./cvs/master_fr.md"
  de_devops: "./cvs/devops_de.md"
  fullstack: "./cvs/master_en.md"
  devops: "./cvs/devops_en.md"
  webdev: "./cvs/web_en.md"
  other: "./cvs/nontech_master_en.md"
  fallback_cv: "./cvs/master_en.md"

output:
  subdir: "outputs"
  max_retries: 5

validation:
  bullet_token_overlap_threshold: 0.5
  bullet_retention_threshold: 0.75
```

**Environment**:
```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-4o-mini"
```

### Configuration 2: Development (Ollama + Loose)

```yaml
ollama:
  url: "http://127.0.0.1:11434/v1/chat/completions"
  model: "mistral:7b-instruct-q4_0"
  timeout: 1800
  temperature: 0.3

cv_map:
  fullstack: "./cvs/master_en.md"
  fallback_cv: "./cvs/master_en.md"

output:
  subdir: "outputs"
  max_retries: 2

validation:
  bullet_token_overlap_threshold: 0.25
  bullet_retention_threshold: 0.50
```

### Configuration 3: Minimal (Single Model)

```yaml
ollama:
  url: "http://localhost:11434/v1/chat/completions"
  model: "neural-chat:7b"
  timeout: 720
  temperature: 0.3

cv_map:
  fallback_cv: "./cvs/master_en.md"

output:
  subdir: "outputs"
  max_retries: 3

validation:
  bullet_token_overlap_threshold: 0.35
  bullet_retention_threshold: 0.60
```

---

## Environment Variable Reference

Complete list of overrideable environment variables:

```bash
# LLM Configuration
OLLAMA_URL="http://127.0.0.1:11434/v1/chat/completions"
OLLAMA_MODEL="qwen:9b-chat-v1.5"
OLLAMA_TIMEOUT="720"
OLLAMA_TEMPERATURE="0.3"

# OpenAI Configuration
OPENAI_API_KEY="sk-..."
OPENAI_MODEL="gpt-4o-mini"
OPENAI_BASE_URL="https://api.openai.com/v1"
OPENAI_TIMEOUT="120"

# Application Configuration
LINGUARESUME_CONFIG="./config.yaml"
LINGUARESUME_OUTPUT_DIR="./outputs"
LINGUARESUME_LOGLEVEL="INFO"
```

---

## Configuration Validation

Check your configuration:

```bash
python -c "
from linguaresume.config import Config
try:
    config = Config.from_yaml('config.yaml')
    print('✓ Configuration valid')
    print(f'  LLM: {config.ollama.model}')
    print(f'  CVs: {len(config.cv_map)} mappings')
    print(f'  Validation thresholds: {config.validation.bullet_retention_threshold}')
except Exception as e:
    print(f'✗ Configuration error: {e}')
"
```

---

## Quick Reference Cheat Sheet

```yaml
# ✅ MINIMUM VIABLE CONFIG
ollama:
  url: "http://127.0.0.1:11434/v1/chat/completions"
  model: "mistral:7b-instruct"
  temperature: 0.3
  timeout: 720

cv_map:
  fallback_cv: "./cvs/master_en.md"

output:
  subdir: "outputs"
  max_retries: 3

validation:
  bullet_token_overlap_threshold: 0.35
  bullet_retention_threshold: 0.60

section_aliases:
  profile:
    - "Profile"
    - "Summary"

static_section_keys:
  - "education"
  - "languages"
```

---

**For questions or issues, see [SETUP.md](SETUP.md#troubleshooting) Troubleshooting section.**
