# LinguaResume Setup Guide

> Complete installation and configuration instructions

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [LLM Configuration](#llm-configuration)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements

- **Python**: 3.8 or higher
- **OS**: Windows, macOS, or Linux
- **RAM**: 4GB (for local Ollama) or 2GB (for OpenAI API)
- **Disk Space**: 500MB (excluding LLM models)

### Optional Requirements

- **GPU**: NVIDIA/AMD GPU for faster local inference (Ollama)
- **Docker**: To run Ollama in a container

### Supported Platforms

| OS | Version | Status |
|---|---------|--------|
| Ubuntu | 20.04 LTS+ | ✅ Tested |
| macOS | 11.0+ | ✅ Tested |
| Windows | 10, 11 | ✅ Tested |
| Debian | 11+ | ✅ Tested |
| Fedora | 35+ | ✅ Tested |

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/linguaresume.git
cd linguaresume
```

### Step 2: Create Virtual Environment

#### Option A: venv (Recommended)

```bash
# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Windows (Command Prompt)
python -m venv .venv
.venv\Scripts\activate.bat
```

#### Option B: conda

```bash
conda create -n linguaresume python=3.10
conda activate linguaresume
```

#### Option C: uv (Fast alternative)

```bash
uv venv linguaresume
source .venv/bin/activate  # or activate on Windows
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies:**
- `pyyaml` - Configuration file parsing
- `jinja2` - Prompt template rendering
- `requests` - HTTP client for LLM APIs
- `markdown` - Markdown to HTML conversion
- `playwright` - Browser automation for PDF
- `pytest` - Testing framework

### Step 4: Install Playwright Browsers

Required for PDF generation:

```bash
playwright install chromium
```

This downloads the Chromium browser for PDF rendering (~300MB).

### Step 5: Verify Installation

```bash
python -c "import linguaresume; print('✓ LinguaResume installed successfully')"
python -m linguaresume --help
```

---

## LLM Configuration

You have three options: local Ollama, OpenAI API, or both.

### Option 1: Local Ollama (Recommended for Development)

Ollama runs LLMs locally on your machine with no API costs.

#### Install Ollama

1. Download from [ollama.ai](https://ollama.ai)
2. Install and launch the application
3. Verify installation:
   ```bash
   ollama --version
   ```

#### Start Ollama

```bash
# macOS/Linux
ollama serve

# Windows
# Use the installed GUI application or:
ollama serve
```

Ollama will start on `http://127.0.0.1:11434`

#### Download a Model

Choose a model based on your hardware:

**Recommended Models (Balanced Performance/Quality):**

```bash
# 9B parameters (~5GB RAM)
ollama pull qwen:9b-chat-v1.5-q8_0
ollama pull mistral:7b-instruct-q8_0
ollama pull neural-chat:7b-v3.3-q8_0

# 7B parameters (~4GB RAM, faster)
ollama pull mistral:7b-instruct-q4_0
ollama pull neural-chat:7b-q4_0

# 3B parameters (~2GB RAM, fastest)
ollama pull phi:2.7b-chat-q8_0
ollama pull dolphin-phi:latest
```

**For better quality (if you have resources):**

```bash
# 70B parameters (~40GB VRAM required)
ollama pull llama2:70b-chat-q4_0

# 13B parameters (~8GB RAM)
ollama pull llama2:13b-chat-q8_0
```

#### Update config.yaml

```yaml
ollama:
  url: "http://127.0.0.1:1234/v1/chat/completions"  # or 11434 for new versions
  model: "qwen:9b-chat-v1.5-q8_0"  # or your chosen model
  timeout: 720
  temperature: 0.3
```

#### Test Connection

```bash
python -c "
from linguaresume.llm.client import OllamaClient
client = OllamaClient('http://127.0.0.1:11434/v1/chat/completions', 'qwen:9b-chat-v1.5-q8_0')
response = client.complete('You are a helpful assistant.', 'Hello!')
print('✓ Ollama connection successful')
print(f'Response: {response[:100]}...')
"
```

### Option 2: OpenAI API (Recommended for Production)

Uses OpenAI's GPT models via API (paid).

#### Get API Key

1. Sign up at [platform.openai.com](https://platform.openai.com)
2. Go to API keys section
3. Create new secret key
4. Copy the key (save it securely)

#### Set Environment Variable

```bash
# Linux/macOS (add to ~/.bashrc or ~/.zshrc for persistence)
export OPENAI_API_KEY="sk-..."

# Windows (PowerShell)
$env:OPENAI_API_KEY="sk-..."

# Windows (Command Prompt)
set OPENAI_API_KEY=sk-...

# Docker/Production (add to .env file)
OPENAI_API_KEY=sk-...
```

#### Update config.yaml

```yaml
ollama:
  # Not used when OPENAI_API_KEY is set
  url: "http://127.0.0.1:11434/v1/chat/completions"
  model: "qwen:9b-chat-v1.5-q8_0"
  timeout: 720
  temperature: 0.3
```

The CLI will automatically detect the API key and use OpenAI.

#### Test Connection

```bash
python -c "
import os
os.environ['OPENAI_API_KEY'] = 'sk-...'
from linguaresume.llm.client import OpenAIClient
client = OpenAIClient(os.environ['OPENAI_API_KEY'], model='gpt-4o-mini')
response = client.complete('You are a helpful assistant.', 'Hello!')
print('✓ OpenAI connection successful')
print(f'Response: {response[:100]}...')
"
```

#### Cost Estimation

| Model | Cost per 1K Tokens | Typical Cost per Resume |
|-------|-------------------|----------------------|
| gpt-4o-mini | $0.00015 (input) | $0.05-0.10 |
| gpt-3.5-turbo | $0.00050 (input) | $0.10-0.20 |
| gpt-4 | $0.03 (input) | $2-5 |

### Option 3: Azure OpenAI

If you're using Azure's OpenAI service:

```bash
export OPENAI_API_KEY="your-azure-key"
export OPENAI_BASE_URL="https://your-resource.openai.azure.com/"
export OPENAI_API_VERSION="2024-02-15-preview"
```

Then in config.yaml:
```yaml
openai:
  base_url: "https://your-resource.openai.azure.com/"
  model: "your-deployment-name"
```

---

## Configuration

### config.yaml Overview

The main configuration file controls all aspects of the system.

#### Full Configuration Template

```yaml
# ============================================================
# LLM Configuration
# ============================================================

ollama:
  # Ollama endpoint (local or remote)
  url: "http://127.0.0.1:1234/v1/chat/completions"
  
  # Model name (see: ollama list)
  model: "qwen/qwen3.5-9b"
  
  # Request timeout in seconds (for long inference)
  timeout: 720
  
  # Temperature: 0.0 = deterministic, 1.0 = creative
  # Use 0.1-0.3 for resume tailoring
  temperature: 0.3

# ============================================================
# Master CV Mapping
# ============================================================

# Maps (language_domain) → CV file path
# Priority: language_specific → domain_only → fallback_cv
cv_map:
  # French CVs (language-specific)
  fr_fullstack: "./cvs/master_fr.md"
  fr_devops: "./cvs/devops_fr.md"
  fr_webdev: "./cvs/web_fr.md"
  fr_other: "./cvs/nontech_master_fr.md"
  
  # German CVs
  de_fullstack: "./cvs/master_de.md"
  de_devops: "./cvs/devops_de.md"
  de_webdev: "./cvs/web_de.md"
  de_other: "./cvs/nontech_master_de.md"
  
  # English/Default CVs (domain-only, used as fallback)
  fullstack: "./cvs/master_en.md"
  devops: "./cvs/devops_en.md"
  webdev: "./cvs/web_en.md"
  other: "./cvs/nontech_master_en.md"

# Fallback CV if all other lookup attempts fail
fallback_cv: "./cvs/master_en.md"

# ============================================================
# Output Configuration
# ============================================================

output:
  # Directory for generated resumes
  subdir: "outputs"
  
  # Maximum retry attempts if validation fails
  max_retries: 3

# ============================================================
# Validation Configuration
# ============================================================

validation:
  # Minimum token-level similarity for bullet points
  # Example: 0.35 means final bullets must have ≥35% token overlap
  bullet_token_overlap_threshold: 0.35
  
  # Minimum fraction of bullets to retain from master
  # Example: 0.60 means if master has 5 bullets, keep ≥3
  bullet_retention_threshold: 0.60

# ============================================================
# Section Headers (Multi-language Aliases)
# ============================================================

# Maps section names to possible header variations
# Allows parsing CVs in different languages
section_aliases:
  profile:
    - "Profil"
    - "Profile"
    - "Professional Profile"
    - "Profil Professionnel"
    - "Résumé"
    - "Resume"
    - "Summary"
  
  technical_skills:
    - "Technische Fähigkeiten"
    - "Technical Skills"
    - "Technical Skills Stack"
    - "Compétences Techniques"
    - "Skills"
  
  professional_experience:
    - "Berufserfahrung"
    - "Professional Experience"
    - "Expérience Professionnelle"
    - "Work Experience"
    - "Experience"
  
  education:
    - "Ausbildung"
    - "Education"
    - "Formation"
  
  languages:
    - "Sprachen"
    - "Languages"
    - "Langues"

# Static section keys (these are NOT tailored)
static_section_keys:
  - "education"
  - "languages"

# Keywords to detect junior-level positions
junior_keywords:
  - "junior"
  - "entry-level"
  - "débutant"
  - "anfänger"
  - "graduate"
  - "recent graduate"

# Enable special handling for junior positions
enable_junior_special_case: true

# ============================================================
# Language-specific Corrections
# ============================================================

# French text replacements (e.g., grammatical fixes)
corrections_fr:
  - search: "avoir fait"
    replace: "avoir réalisé"
  - search: "faire de"
    replace: "réaliser"

# German text replacements
corrections_de:
  - search: "haben gemacht"
    replace: "haben durchgeführt"
  - search: "Fähigkeit"
    replace: "Kompetenz"

# ============================================================
# Stopwords for Keyword Extraction
# ============================================================

# Common words to ignore when extracting keywords
stopwords:
  - "the"
  - "and"
  - "or"
  - "is"
  - "are"
  - "was"
  - "were"
  - "be"
  - "a"
  - "an"
  - "for"
  - "on"
  - "with"
  - "at"
  - "by"
  - "to"
  - "from"
  - "of"
  - "in"
  - "et"
  - "ou"
  - "le"
  - "la"
  - "les"
  - "un"
  - "une"
  - "des"
  - "du"
  - "de"
  - "und"
  - "oder"
  - "der"
  - "die"
  - "das"
  - "dem"
  - "den"
  - "ein"
  - "eine"
  - "einen"
  - "einem"

# ============================================================
# Resume CSS Styling
# ============================================================

# CSS for PDF rendering
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
  
  h3 {
    font-size: 11pt;
    margin-top: 8px;
    margin-bottom: 4px;
  }
  
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0;
  }
  
  table, th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
  }
  
  a {
    color: #0066cc;
    text-decoration: none;
  }
  
  a:hover {
    text-decoration: underline;
  }
  
  ul {
    margin: 4px 0;
    padding-left: 20px;
  }
  
  li {
    margin-bottom: 3px;
  }
```

### Customization Examples

#### Example 1: Stricter Validation

```yaml
validation:
  bullet_token_overlap_threshold: 0.5  # Require 50% match
  bullet_retention_threshold: 0.80     # Keep 80% of bullets

output:
  max_retries: 5  # More attempts to pass validation
```

#### Example 2: Custom Styling

```yaml
resume_css: |
  body {
    font-family: 'Calibri', serif;
    font-size: 11pt;
  }
  
  h2 {
    color: #1a73e8;  # Google Blue
    border-bottom: 3px solid #1a73e8;
  }
```

#### Example 3: Add New Domain

```yaml
cv_map:
  # ... existing mappings ...
  
  # New domain: mobile development
  fr_mobile: "./cvs/mobile_fr.md"
  de_mobile: "./cvs/mobile_de.md"
  mobile: "./cvs/mobile_en.md"

# Add keywords for detection
junior_keywords:
  - "mobile"
  - "ios"
  - "android"
  - "react native"
```

---

## Verification

### Step 1: Test Python Installation

```bash
python --version
# Output: Python 3.8.10 or higher
```

### Step 2: Test Dependencies

```bash
python -c "
import sys
packages = ['yaml', 'jinja2', 'requests', 'markdown', 'playwright', 'pytest']
for pkg in packages:
    try:
        __import__(pkg)
        print(f'✓ {pkg}')
    except ImportError:
        print(f'✗ {pkg} (missing)')
"
```

### Step 3: Test LLM Connection

```bash
# Test Ollama
python -c "
from linguaresume.llm.client import OllamaClient
try:
    client = OllamaClient('http://127.0.0.1:11434/v1/chat/completions', 'mistral:7b')
    print('✓ Ollama connection successful')
except Exception as e:
    print(f'✗ Ollama connection failed: {e}')
"

# Test OpenAI
export OPENAI_API_KEY="sk-..."
python -c "
from linguaresume.llm.client import OpenAIClient
import os
try:
    client = OpenAIClient(os.environ['OPENAI_API_KEY'])
    print('✓ OpenAI connection successful')
except Exception as e:
    print(f'✗ OpenAI connection failed: {e}')
"
```

### Step 4: Test Configuration Loading

```bash
python -c "
from linguaresume.config import Config
config = Config.from_yaml('config.yaml')
print(f'✓ Config loaded')
print(f'  - LLM: {config.ollama.model}')
print(f'  - CVs: {len(config.cv_map)} mapped')
print(f'  - Sections: {len(config.section_aliases)} defined')
"
```

### Step 5: Run Test Suite

```bash
pytest tests/ -v
# Should see: passed, no failures
```

### Step 6: Try a Sample Tailoring

```bash
# Create a test job description
cat > test_job.txt << 'EOF'
Senior Python Developer
We're looking for a Python expert with 5+ years of experience.
Required: Python, Django, REST APIs, PostgreSQL
Nice to have: Docker, Kubernetes, AWS
EOF

# Run tailoring
python -m linguaresume tailor test_job.txt

# Check output
ls -la outputs/
```

---

## Troubleshooting

### Issue 1: "ModuleNotFoundError: No module named 'linguaresume'"

**Cause**: Virtual environment not activated or dependencies not installed

**Solution**:
```bash
# Activate venv
source .venv/bin/activate  # macOS/Linux
.\.venv\Scripts\Activate.ps1  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Issue 2: "Connection refused" - Ollama

**Cause**: Ollama not running or wrong URL in config

**Solution**:
```bash
# Start Ollama
ollama serve

# Verify connection
curl http://127.0.0.1:11434/api/tags

# Update config.yaml if needed
# Default: http://127.0.0.1:11434
# Change 11434 to 1234 if using older Ollama version
```

### Issue 3: "OPENAI_API_KEY not found"

**Cause**: Environment variable not set

**Solution**:
```bash
# Set API key
export OPENAI_API_KEY="sk-your-actual-key"

# Verify
echo $OPENAI_API_KEY  # Should show your key (first 20 chars)

# For Windows PowerShell
$env:OPENAI_API_KEY = "sk-your-actual-key"
```

### Issue 4: "Playwright browser not found"

**Cause**: Chromium not installed for PDF rendering

**Solution**:
```bash
playwright install chromium
# or all browsers
playwright install
```

### Issue 5: "Timeout connecting to LLM"

**Cause**: LLM server slow or unresponsive

**Solution**:
```yaml
# In config.yaml, increase timeout
ollama:
  timeout: 1800  # 30 minutes instead of 12

# Or reduce retry attempts
output:
  max_retries: 2
```

### Issue 6: Validation keeps failing

**Cause**: Validation thresholds too strict, or LLM quality issues

**Solution**:
```yaml
# In config.yaml
validation:
  bullet_token_overlap_threshold: 0.25  # Relax threshold
  bullet_retention_threshold: 0.50

output:
  max_retries: 5  # More retry attempts

# Or use better LLM
ollama:
  model: "qwen:9b-chat-v1.5"  # Better model
  temperature: 0.1  # More deterministic
```

### Issue 7: PDF generation fails

**Cause**: Playwright issue, usually font or rendering

**Solution**:
```bash
# Reinstall Playwright
playwright uninstall
playwright install chromium

# Try with minimal CSS
# Edit config.yaml and simplify resume_css

# Or test manually
python -c "
from linguaresume.pdf.renderer import PDFRenderer
renderer = PDFRenderer()
renderer.render('# Test\n\nHello', 'test.pdf')
"
```

### Issue 8: Out of Memory

**Cause**: LLM model too large for available RAM

**Solution**:
```bash
# Use smaller model
ollama pull mistral:7b-instruct-q4_0
# Update config.yaml:
# model: "mistral:7b-instruct-q4_0"

# Or add quantization (lower quality, less RAM)
ollama pull model-name:7b-q2_K  # 4K quantization (more RAM saving)
```

---

## Performance Tuning

### For Faster Inference

```yaml
# Use smaller model
ollama:
  model: "dolphin-phi:latest"  # 3.8B, very fast
  temperature: 0.1  # More deterministic

# Reduce validation retries
output:
  max_retries: 1  # Fewer retries
```

### For Better Quality

```yaml
# Use larger model
ollama:
  model: "qwen:72b"  # Requires high-end GPU
  temperature: 0.3  # Balanced

# Stricter validation
validation:
  bullet_retention_threshold: 0.75
```

### For Cost Optimization (OpenAI)

```bash
# Use cheaper model
export OPENAI_API_KEY="sk-..."

# In code or CLI:
python -m linguaresume tailor job.txt --model gpt-3.5-turbo
```

---

## Next Steps

1. **Read the main README** for usage examples
2. **Review ARCHITECTURE.md** for technical details
3. **Check API.md** for Python API reference
4. **Run tests**: `pytest tests/ -v`
5. **Try a sample job description** (see Verification, Step 6)

## Additional Resources

- [Ollama Documentation](https://ollama.ai)
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [Playwright Documentation](https://playwright.dev)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)

---

**Happy resume tailoring!** 🚀
