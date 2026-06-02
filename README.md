# LinguaResume 📄🌍

> **Intelligent Resume Tailoring with LLM-Powered Accuracy**

LinguaResume is an automated resume tailoring system that uses Large Language Models (LLMs) to adapt your CV to specific job descriptions while maintaining strict factual accuracy. It supports **multiple languages** (English, French, German) and **specialized domains** (Full-Stack, DevOps, Web Development, Non-Technical).

## ✨ Features

- 🎯 **Intelligent Resume Tailoring** - Automatically adapts resume content to match job descriptions
- 🌐 **Multi-Language Support** - Native support for English, French, and German
- 🏢 **Domain-Specific CVs** - Separate master resumes optimized for different career paths
- ✅ **Strict Validation** - Prevents LLM hallucination with comprehensive fact-checking:
  - Company names and employment dates preserved
  - Experience duration consistency verified
  - Bullet point retention validated
  - Technical skills not artificially expanded
  - Static sections (Education, Languages) untouched
- 🔄 **Intelligent Retries** - Failed validations trigger LLM refinement with detailed feedback
- 💾 **Response Caching** - Eliminates duplicate LLM calls for cost efficiency
- 📄 **PDF Export** - Generates professional PDF documents directly from markdown
- 🔌 **Flexible LLM Integration** - Works with Ollama (local/remote) or OpenAI
- 🚀 **Command-Line Interface** - Easy-to-use CLI for all operations

## 🎬 Quick Start

### Prerequisites

- Python 3.8+
- LLM (Ollama running locally, or OpenAI API key)
- Required dependencies (see Installation)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd linguaresume
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\Activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your LLM**
   
   Edit `config.yaml` to point to your LLM:
   
   ```yaml
   # For local Ollama
   ollama:
     url: "http://127.0.0.1:1234/v1/chat/completions"
     model: "qwen/qwen3.5-9b"
     temperature: 0.3
     timeout: 720
   ```
   
   Or set environment variables for OpenAI:
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

### Basic Usage

#### 1. Tailor Your Resume to a Job Description

```bash
python -m linguaresume tailor job_description.txt
```

This will:
- Auto-detect the job language and domain
- Select the appropriate master CV
- Generate a tailored markdown resume
- Export to PDF
- Save outputs to `outputs/<job_name>/`

#### 2. Validate an Existing Resume

```bash
python -m linguaresume validate <resume.md> <job_description.txt>
```

Checks:
- ✓ Company names consistency
- ✓ Date ranges accuracy
- ✓ Bullet point retention
- ✓ Experience duration
- ✓ Technical skills preservation

#### 3. Generate PDF from Markdown

```bash
python -m linguaresume pdf <resume.md> -o <output.pdf>
```

#### 4. Translate Resume Sections

```bash
python -m linguaresume translate <resume.md> --target-lang de
```

## 📋 Configuration

### File Structure

```
linguaresume/
├── config.yaml              # Main configuration
├── requirements.txt         # Python dependencies
├── cvs/                     # Master CV templates
│   ├── master_en.md        # Full-Stack CV (English)
│   ├── master_fr.md        # Full-Stack CV (French)
│   ├── master_de.md        # Full-Stack CV (German)
│   ├── devops_en.md        # DevOps CV (English)
│   ├── web_en.md           # Web Dev CV (English)
│   └── ...                 # (and corresponding FR/DE versions)
├── linguaresume/           # Main package
│   ├── cli.py             # CLI entry point
│   ├── config.py          # Configuration loader
│   ├── models.py          # Data models
│   ├── llm/               # LLM clients & prompts
│   ├── parsing/           # Resume parsing utilities
│   ├── tailoring/         # Main tailoring engine
│   ├── validation/        # Validation rules
│   └── pdf/               # PDF rendering
├── tests/                  # Unit and integration tests
└── outputs/                # Generated resumes (per job)
```

### config.yaml Parameters

#### LLM Configuration
```yaml
ollama:
  url: "http://127.0.0.1:1234/v1/chat/completions"  # Ollama endpoint
  model: "qwen/qwen3.5-9b"                            # Model name
  timeout: 720                                        # Request timeout (seconds)
  temperature: 0.3                                    # Response creativity (0.0-1.0)
```

#### Validation Thresholds
```yaml
validation:
  bullet_token_overlap_threshold: 0.35  # Min 35% token similarity for bullets
  bullet_retention_threshold: 0.60      # Min 60% of bullets must be retained
```

#### CV Selection Mapping
```yaml
cv_map:
  # Language-specific (priority order: language_domain → domain → fallback)
  fr_fullstack: "./cvs/master_fr.md"
  de_webdev: "./cvs/web_de.md"
  # ... other mappings
  fallback_cv: "./cvs/master_en.md"
```

#### Section Aliases (Multi-language Support)
```yaml
section_aliases:
  profile:
    - "Profil"           # German
    - "Profile"          # English
    - "Profil Professionnel"  # French
  # ... other sections
```

## 🔍 How It Works

### Workflow Diagram

```
┌─────────────────────┐
│ Job Description     │
└──────────┬──────────┘
           │
    ┌──────▼──────────┐
    │ Language        │
    │ Detection       │ (Detects: EN, FR, DE)
    └──────┬──────────┘
           │
    ┌──────▼──────────────┐
    │ Domain             │
    │ Classification     │ (Detects: fullstack, devops, webdev, other)
    └──────┬──────────────┘
           │
    ┌──────▼─────────────────────────┐
    │ Load Master CV                  │
    │ (language × domain selection)   │
    └──────┬─────────────────────────┘
           │
    ┌──────▼──────────────────────────┐
    │ Parse Resume                     │
    │ (Split mutable vs static sections)
    └──────┬──────────────────────────┘
           │
    ┌──────▼──────────────────────────┐
    │ Extract Requirements from Job    │
    │ (must-haves, nice-to-haves)      │
    └──────┬──────────────────────────┘
           │
    ┌──────▼──────────────────────────┐
    │ LLM Tailoring Prompt             │
    │ (requirements + source content)  │
    └──────┬──────────────────────────┘
           │
    ┌──────▼──────────────────────────┐
    │ Call LLM                         │
    │ (Ollama or OpenAI)               │
    └──────┬──────────────────────────┘
           │
    ┌──────▼────────────────┐
    │ Validate Output        │
    │ ✓ Companies           │
    │ ✓ Dates               │
    │ ✓ Bullets             │
    │ ✓ Experience Duration │
    │ ✓ Tech Stack          │
    └──────┬────────────────┘
           │
      ┌────▼─────────┐
      │   Failed?    │
      └────┬─────────┘
           │
    ┌──────▼──────────────────────┐
    │ No → Generate Output & PDF   │
    │      Save to outputs/        │
    └──────────────────────────────┘
           │
    ┌──────▼──────────────────────┐
    │ Yes → Retry with Feedback   │
    │      (max 3 attempts)       │
    └──────────────────────────────┘
```

### Key Components

#### 1. **Language Detection**
- Pattern-based detection using common words in each language
- Detects: English, French, German
- Fallback: English

#### 2. **Domain Classification**
Automatically classifies the job as:
- **fullstack** - Full-Stack Developer positions
- **devops** - DevOps & Cloud Engineering roles
- **webdev** - Web Development (frontend-focused)
- **other** - Non-technical positions

#### 3. **Master CV Selection**
```
Job Language (FR) + Domain (devops) 
  → Lookup cv_map["fr_devops"]
  → If not found → cv_map["devops"]
  → If not found → fallback_cv
```

#### 4. **Resume Parsing**
- **Mutable Sections**: Profile, Technical Skills, Professional Experience
- **Static Sections**: Education, Languages, Certifications
- Only mutable sections are tailored; static sections are preserved

#### 5. **LLM Tailoring**
Generates optimized resume content that:
- Matches job requirements
- Uses required terminology and skills
- Maintains first-person narrative style
- Stays within language-specific tone guidelines
- Preserves factual accuracy

#### 6. **Multi-Pass Validation**
If any validation fails, the system:
1. Extracts specific errors (e.g., "Company 'Acme Corp' missing")
2. Generates detailed feedback for the LLM
3. Retries with max 3 attempts
4. Escalates if all attempts fail

#### 7. **Output Generation**
- **Markdown**: Human-readable tailored resume
- **PDF**: Professional-looking formatted document
- **Job Title Translation**: Translates title to match job language

## 📖 Usage Examples

### Example 1: Tailor for a French DevOps Role

```bash
# Job description file: job_description.txt
# Contains French job posting for DevOps engineer

python -m linguaresume tailor job_description.txt

# Output:
# ✓ Detected language: French
# ✓ Classified domain: devops
# ✓ Selected CV: cvs/devops_fr.md
# ✓ Generated: outputs/devops_engineer_role/Mohamed_Tababi_CV.md
# ✓ Generated: outputs/devops_engineer_role/Mohamed_Tababi_CV.pdf
```

### Example 2: Validate a Custom Resume

```bash
python -m linguaresume validate my_resume.md job_posting.txt

# Validation Results:
# ✓ Companies: 3/3 validated
# ✓ Dates: All preserved
# ✓ Bullet retention: 85% ✓
# ✓ Experience: 5.5 years (unchanged)
# ✓ Static sections: Verified
```

### Example 3: Generate PDF with Custom Output

```bash
python -m linguaresume pdf tailored_resume.md -o my_resume.pdf --css custom.css
```

### Example 4: Translate Static Sections

```bash
python -m linguaresume translate master_en.md --target-lang de
# Outputs: Education and Languages sections in German
# Keeps proper nouns unchanged
```

## 🛠️ Architecture Overview

For detailed technical architecture, see [ARCHITECTURE.md](./ARCHITECTURE.md).

### Module Breakdown

| Module | Responsibility |
|--------|-----------------|
| **`llm/`** | LLM client abstraction, caching, prompt templates |
| **`parsing/`** | Resume content extraction (companies, dates, keywords) |
| **`tailoring/`** | Main orchestration and workflow logic |
| **`validation/`** | Strict validation rules and checks |
| **`pdf/`** | Markdown to PDF rendering via Playwright |
| **`cli.py`** | Command-line interface and argument handling |

## 🔌 Supported LLMs

### Local Ollama
```yaml
ollama:
  url: "http://127.0.0.1:1234/v1/chat/completions"
  model: "qwen/qwen3.5-9b"  # or any other Ollama model
```

### OpenAI (GPT-4, GPT-3.5, etc.)
```bash
export OPENAI_API_KEY="sk-..."
# CLI will automatically use OpenAI if key is set
```

### Custom LLM Providers
Extend `LLMClient` in `linguaresume/llm/client.py` for other providers.

## 🧪 Testing

Run the test suite:
```bash
pytest tests/
```

Key test files:
- `tests/test_cv_selection.py` - CV selection and language/domain detection
- `tests/test_engine_mockllm.py` - End-to-end workflow with mock LLM

## 📚 Master CVs

The system includes 12 pre-built master CVs:

### English CVs
- `master_en.md` - Full-Stack Engineer (comprehensive)
- `devops_en.md` - DevOps & Cloud Engineer
- `web_en.md` - Web Developer
- `nontech_master_en.md` - IT Support / Non-Technical

### French CVs
- `master_fr.md` - Ingénieur Full-Stack
- `devops_fr.md` - Ingénieur DevOps & Cloud
- `web_fr.md` - Développeur Web
- `nontech_master_fr.md` - Support IT

### German CVs
- `master_de.md` - Full-Stack Ingenieur
- `devops_de.md` - DevOps & Cloud Ingenieur
- `web_de.md` - Webentwickler
- `nontech_master_de.md` - IT-Support

Each CV includes:
- Optimized profile/summary for the domain
- Domain-specific technical skills table
- Relevant professional experience examples
- Educational credentials
- Language proficiencies

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/your-feature`)
3. **Make your changes** with clear commit messages
4. **Add tests** for new functionality
5. **Run tests** before submitting (`pytest tests/`)
6. **Submit a pull request** with a detailed description

### Areas for Contribution
- Additional language support (Spanish, Italian, etc.)
- New domain-specific CVs
- Enhanced validation rules
- Performance optimizations
- Documentation improvements
- Bug fixes and edge cases

## 📝 License

This project is provided as-is for resume tailoring and career development purposes.

## 🆘 Troubleshooting

### Issue: "Connection refused" when calling LLM

**Solution**: Ensure Ollama is running:
```bash
ollama serve  # Start Ollama
```

### Issue: "OpenAI API key not found"

**Solution**: Set the environment variable:
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

### Issue: PDF generation fails

**Solution**: Ensure Playwright is installed:
```bash
playwright install
```

### Issue: Resume validation keeps failing

**Solution**: 
- Reduce `bullet_retention_threshold` in `config.yaml` (default: 0.60)
- Increase `max_retries` in output config (default: 3)
- Check LLM temperature (lower = more factual)

## 📖 Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Technical architecture details
- [SETUP.md](./SETUP.md) - Detailed setup and installation
- [CONFIG.md](./CONFIG.md) - Configuration reference
- [API.md](./API.md) - Python API reference

## 🎯 Roadmap

- [ ] Web UI dashboard for resume management
- [ ] Batch processing for multiple job applications
- [ ] A/B testing different prompt strategies
- [ ] Integration with LinkedIn and Indeed
- [ ] Real-time resume preview during tailoring
- [ ] Support for additional languages
- [ ] Advanced analytics and success metrics

## 📧 Support

For issues, questions, or feature requests, please open an issue on the repository.

---

**Made with ❤️ for better job applications**
