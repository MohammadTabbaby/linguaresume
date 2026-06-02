# LinguaResume Python API Reference

> Guide to using LinguaResume as a Python library in your own code

## Table of Contents

1. [Quick Start](#quick-start)
2. [Core Classes](#core-classes)
3. [LLM Clients](#llm-clients)
4. [Resume Processing](#resume-processing)
5. [Validation](#validation)
6. [Examples](#examples)
7. [Error Handling](#error-handling)

---

## Quick Start

### Basic Example

```python
from linguaresume.config import Config
from linguaresume.llm.client import OllamaClient
from linguaresume.tailoring.engine import TailoringEngine

# Load configuration
config = Config.from_yaml("config.yaml")

# Create LLM client
llm = OllamaClient(
    url=config.ollama.url,
    model=config.ollama.model,
    temperature=config.ollama.temperature
)

# Create tailoring engine
engine = TailoringEngine(config, llm)

# Tailor resume
job_description = open("job_description.txt").read()
tailored_resume = engine.tailor(job_description)

print(tailored_resume)
```

---

## Core Classes

### Config

Load and manage configuration from YAML.

```python
from linguaresume.config import Config

# Load from default config.yaml
config = Config.from_yaml()

# Load from custom path
config = Config.from_yaml("path/to/config.yaml")

# Access configuration values
print(config.ollama.url)              # LLM URL
print(config.ollama.model)            # Model name
print(config.cv_map)                  # CV mapping dict
print(config.fallback_cv)             # Default CV path
print(config.validation.bullet_retention_threshold)  # Validation threshold
```

**Attributes**:
- `ollama` - OllamaConfig
- `cv_map` - Dict[str, str]
- `fallback_cv` - str
- `output` - OutputConfig
- `section_aliases` - Dict[str, List[str]]
- `static_section_keys` - List[str]
- `validation` - ValidationConfig

### Requirement

Job description parsed into structured requirements.

```python
from linguaresume.models import Requirement

requirement = Requirement(
    job_title="Senior DevOps Engineer",
    company="Acme Corp",
    domain="devops",
    must_haves=["Kubernetes", "Docker", "AWS"],
    nice_to_haves=["Terraform", "Helm"],
    soft_skills=["Leadership", "Communication"],
    job_focus="Infrastructure automation"
)

# Access fields
print(requirement.job_title)
print(requirement.must_haves)
print(requirement.soft_skills)
```

### ValidationResult

Result of validation checks.

```python
from linguaresume.models import ValidationResult

# Created internally during validation
result = ValidationResult(
    is_valid=False,
    checks_passed=["companies", "dates"],
    checks_failed=["bullet_retention"],
    error_details={"bullet_retention": "Only 40% retention"}
)

if not result.is_valid:
    print(f"Failed checks: {result.checks_failed}")
```

---

## LLM Clients

### LLMClient (Abstract)

Base class for all LLM providers.

```python
from linguaresume.llm.client import LLMClient

# All clients implement this interface
class CustomLLMClient(LLMClient):
    def complete(self, system: str, user: str) -> str:
        """
        Generate a completion.
        
        Args:
            system: System prompt (role/context)
            user: User prompt (task)
            
        Returns:
            Generated text response
        """
        pass
```

### OllamaClient

Connect to local or remote Ollama instance.

```python
from linguaresume.llm.client import OllamaClient

# Create client
client = OllamaClient(
    url="http://127.0.0.1:11434/v1/chat/completions",
    model="mistral:7b-instruct",
    temperature=0.3,
    timeout=720,
    max_retries=2
)

# Generate completion
system_prompt = "You are a resume writer."
user_prompt = "Rewrite this bullet point for a DevOps role."
response = client.complete(system_prompt, user_prompt)
print(response)
```

**Parameters**:
- `url` (str): Ollama endpoint
- `model` (str): Model name
- `temperature` (float): 0.0-1.0 response randomness
- `timeout` (int): Request timeout in seconds
- `max_retries` (int): Retry attempts on failure
- `cache` (LLMCache, optional): Response cache

### OpenAIClient

Connect to OpenAI API.

```python
import os
from linguaresume.llm.client import OpenAIClient

# Get API key from environment
api_key = os.getenv("OPENAI_API_KEY")

# Create client
client = OpenAIClient(
    api_key=api_key,
    model="gpt-4o-mini",
    temperature=0.3,
    timeout=120,
    max_retries=2
)

# Generate completion
response = client.complete("System prompt", "User prompt")
print(response)
```

**Parameters**:
- `api_key` (str): OpenAI API key
- `model` (str): Model name (gpt-4, gpt-3.5-turbo, etc)
- `temperature` (float): Response randomness
- `timeout` (int): Request timeout in seconds
- `max_retries` (int): Retry attempts
- `base_url` (str, optional): Custom API endpoint (Azure, etc)
- `cache` (LLMCache, optional): Response cache

### MockLLMClient

For testing without calling LLM.

```python
from linguaresume.llm.client import MockLLMClient

# Create mock client
client = MockLLMClient(response="Mock response")

# Always returns same response
response = client.complete("any", "prompt")
assert response == "Mock response"
```

### LLMCache

Cache LLM responses to avoid redundant calls.

```python
from linguaresume.llm.cache import LLMCache

# Create cache
cache = LLMCache(cache_dir="/tmp/llm_cache")

# Get/set values
cache.set("key", "value")
cached = cache.get("key")

# Used automatically by clients
client = OllamaClient(..., cache=cache)
```

---

## Resume Processing

### TailoringEngine

Main orchestration for resume tailoring workflow.

```python
from linguaresume.tailoring.engine import TailoringEngine
from linguaresume.config import Config
from linguaresume.llm.client import OllamaClient

# Setup
config = Config.from_yaml()
llm = OllamaClient(config.ollama.url, config.ollama.model)
engine = TailoringEngine(config, llm)

# Tailor resume
job_description = open("job.txt").read()
tailored = engine.tailor(job_description)

# Returns markdown string
print(tailored)
```

**Methods**:

#### `tailor(job_description: str) -> str`

Main method for resume tailoring.

**Parameters**:
- `job_description` (str): Job description text

**Returns**:
- (str) Tailored resume markdown

**Process**:
1. Detects language and domain
2. Selects appropriate master CV
3. Extracts requirements
4. Generates tailored content
5. Validates output
6. Retries if needed
7. Returns final markdown

**Raises**:
- `ValueError`: Invalid input
- `RuntimeError`: LLM call failure
- `FileNotFoundError`: CV file not found

#### `_classify_domain(master_text: str, job_text: str) -> str`

Classify job into domain category.

**Returns**: `"fullstack"`, `"devops"`, `"webdev"`, or `"other"`

#### `detect_language(text: str) -> str`

Detect text language.

**Returns**: `"en"`, `"fr"`, `"de"`, or default `"en"`

### Parsing Functions

Parse resume content.

```python
from linguaresume.parsing.extractor import (
    load_text,
    extract_companies,
    extract_dates,
    extract_total_months,
    extract_keywords
)

# Load resume file
resume_text = load_text("resume.md")

# Extract information
companies = extract_companies(resume_text)
# Returns: {"Acme Corp", "Tech Inc", ...}

dates = extract_dates(resume_text)
# Returns: {"02/2022", "06/2024", ...}

months = extract_total_months(resume_text)
# Returns: 48.5 (months of experience)

keywords = extract_keywords(resume_text, stopwords={"the", "and"})
# Returns: {"kubernetes", "python", "aws", ...}
```

### Splitter Functions

Parse resume sections.

```python
from linguaresume.parsing.splitter import (
    split_resume_sections,
    build_mutable_bundle,
    build_static_bundle,
    _make_alias_map
)

# Create alias map
alias_map = _make_alias_map(config.section_aliases)

# Parse sections
preamble, sections = split_resume_sections(resume_text, alias_map)
# sections = [("Profile", content), ("Technical Skills", content), ...]

# Build bundles
mutable = build_mutable_bundle(sections, static_keys, alias_map)
# Contains: Profile + Technical Skills + Experience

static = build_static_bundle(sections, static_keys, alias_map)
# Contains: Education + Languages
```

---

## Validation

### Validation Functions

Validate resume accuracy.

```python
from linguaresume.validation import (
    validate_companies,
    validate_dates,
    validate_bullet_retention,
    validate_experience,
    validate_static_sections
)

master_resume = open("master.md").read()
tailored_resume = open("tailored.md").read()

# Individual validators
validate_companies(tailored_resume, extract_companies(master_resume))
# Returns: bool

validate_dates(tailored_resume, extract_dates(master_resume))
# Returns: bool

validate_bullet_retention(master_resume, tailored_resume, threshold=0.60)
# Returns: bool

validate_experience(master_resume, tailored_resume)
# Returns: bool

validate_static_sections(tailored_resume, static_bundle, alias_map, static_keys)
# Returns: bool
```

### TechValidator

Validate technology stack preservation.

```python
from linguaresume.validation.tech import TechValidator

validator = TechValidator()

master_tech = {"Python", "Docker", "Kubernetes", "AWS"}
tailored_tech = {"Python", "Docker", "Kubernetes"}

# Validate that tailored ⊆ master (no new tech added)
is_valid = validator.validate(master_tech, tailored_tech)
# Returns: True

# Invalid example
tailored_tech_invalid = {"Python", "Docker", "Go"}  # Go not in master
is_valid = validator.validate(master_tech, tailored_tech_invalid)
# Returns: False
```

---

## PDF Rendering

### PDFRenderer

Convert markdown to PDF.

```python
from linguaresume.pdf.renderer import PDFRenderer

# Create renderer
renderer = PDFRenderer(css=custom_css)

# Render markdown to PDF
markdown_content = "# My Resume\n\n..."
renderer.render(markdown_content, "output.pdf")

# File created: output.pdf
```

**Parameters**:
- `css` (str, optional): Custom CSS styling

**Methods**:

#### `render(markdown_text: str, output_path: str) -> None`

Convert markdown to PDF.

**Parameters**:
- `markdown_text` (str): Markdown content
- `output_path` (str): Output PDF file path

**Raises**:
- `ValueError`: Invalid markdown
- `IOError`: Cannot write output file

---

## Examples

### Example 1: Complete Workflow

```python
from linguaresume.config import Config
from linguaresume.llm.client import OllamaClient
from linguaresume.tailoring.engine import TailoringEngine
from linguaresume.pdf.renderer import PDFRenderer

# Setup
config = Config.from_yaml()
llm = OllamaClient(
    url=config.ollama.url,
    model=config.ollama.model
)
engine = TailoringEngine(config, llm)

# Load job description
with open("job.txt") as f:
    job_description = f.read()

# Tailor resume
print("Tailoring resume...")
tailored_resume = engine.tailor(job_description)

# Save markdown
with open("tailored_resume.md", "w") as f:
    f.write(tailored_resume)

# Generate PDF
print("Generating PDF...")
renderer = PDFRenderer(css=config.resume_css)
renderer.render(tailored_resume, "tailored_resume.pdf")

print("✓ Complete!")
```

### Example 2: Custom Validation

```python
from linguaresume.parsing.extractor import (
    extract_companies,
    extract_dates,
    extract_total_months
)
from linguaresume.validation import (
    validate_companies,
    validate_dates,
    validate_experience
)

master = open("master.md").read()
tailored = open("tailored.md").read()

# Run custom validation suite
checks = {
    "companies": validate_companies(
        tailored, 
        extract_companies(master)
    ),
    "dates": validate_dates(
        tailored,
        extract_dates(master)
    ),
    "experience": validate_experience(master, tailored),
}

# Report results
for check, passed in checks.items():
    status = "✓" if passed else "✗"
    print(f"{status} {check}")

if all(checks.values()):
    print("✓ All validations passed")
else:
    print("✗ Some validations failed")
```

### Example 3: Using OpenAI Instead of Ollama

```python
import os
from linguaresume.config import Config
from linguaresume.llm.client import OpenAIClient
from linguaresume.tailoring.engine import TailoringEngine

# Load config (uses Ollama settings, but we'll override)
config = Config.from_yaml()

# Create OpenAI client instead
api_key = os.getenv("OPENAI_API_KEY")
llm = OpenAIClient(
    api_key=api_key,
    model="gpt-4o-mini",
    temperature=0.2
)

# Rest of workflow is the same
engine = TailoringEngine(config, llm)
job_description = open("job.txt").read()
tailored = engine.tailor(job_description)
print(tailored)
```

### Example 4: Batch Processing

```python
from linguaresume.config import Config
from linguaresume.llm.client import OllamaClient
from linguaresume.tailoring.engine import TailoringEngine
from pathlib import Path

config = Config.from_yaml()
llm = OllamaClient(config.ollama.url, config.ollama.model)
engine = TailoringEngine(config, llm)

# Process multiple job descriptions
job_files = Path("jobs").glob("*.txt")

for job_file in job_files:
    print(f"Processing {job_file.name}...")
    
    job_desc = job_file.read_text()
    tailored = engine.tailor(job_desc)
    
    output_file = Path("outputs") / f"{job_file.stem}_tailored.md"
    output_file.write_text(tailored)
    
    print(f"  → {output_file}")

print("✓ Batch processing complete")
```

### Example 5: Custom LLM Client

```python
from linguaresume.llm.client import LLMClient

class MyCustomLLMClient(LLMClient):
    """Custom LLM integration."""
    
    def __init__(self, api_endpoint: str, api_key: str):
        self.api_endpoint = api_endpoint
        self.api_key = api_key
    
    def complete(self, system: str, user: str) -> str:
        """
        Make API call to custom LLM service.
        """
        import requests
        
        payload = {
            "system_prompt": system,
            "user_prompt": user,
            "temperature": 0.3
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            self.api_endpoint,
            json=payload,
            headers=headers,
            timeout=120
        )
        
        response.raise_for_status()
        return response.json()["completion"]

# Use it
from linguaresume.tailoring.engine import TailoringEngine
from linguaresume.config import Config

config = Config.from_yaml()
llm = MyCustomLLMClient(
    api_endpoint="https://my-llm.example.com/v1/chat",
    api_key="sk-xxx"
)

engine = TailoringEngine(config, llm)
# ... rest of workflow
```

---

## Error Handling

### Common Exceptions

```python
from linguaresume.tailoring.engine import TailoringEngine

try:
    engine.tailor(job_description)
except FileNotFoundError as e:
    print(f"CV file not found: {e}")
except ValueError as e:
    print(f"Invalid input: {e}")
except RuntimeError as e:
    print(f"LLM call failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("linguaresume")

# Will now see detailed logs
from linguaresume.tailoring.engine import TailoringEngine
engine = TailoringEngine(config, llm)
```

---

## API Stability

### Versioning

- `1.0.x`: Core API stable, minor changes allowed
- `1.x.0`: Minor additions, backward compatible
- `2.0.0`: Major changes, possible breaking changes

### Deprecation Policy

Functions marked as `@deprecated` will:
1. Work normally for current version
2. Show deprecation warning
3. Be removed in next major version

Example:
```python
@deprecated("Use new_function() instead")
def old_function():
    pass
```

---

## Best Practices

### Do

```python
# ✅ Use type hints
from typing import Optional

def process_resume(config: Config, llm: LLMClient) -> Optional[str]:
    pass

# ✅ Handle exceptions
try:
    result = engine.tailor(job_desc)
except Exception as e:
    logger.error(f"Failed: {e}")

# ✅ Close resources
cache = LLMCache(cache_dir="/tmp/cache")
# ... use cache
# Cache automatically saves on exit
```

### Don't

```python
# ❌ Avoid bare except
try:
    result = engine.tailor(job_desc)
except:  # Too broad!
    pass

# ❌ Don't modify config in place without saving
config.ollama.temperature = 0.5
# Changes lost after script ends

# ❌ Don't hardcode API keys
llm = OpenAIClient(api_key="sk-abc123")  # Security risk!

# Instead: Use environment variables
import os
api_key = os.getenv("OPENAI_API_KEY")
```

---

## Getting Help

- **Documentation**: See README, ARCHITECTURE, SETUP guides
- **Examples**: Check examples/ directory
- **Tests**: See tests/ for usage patterns
- **Issues**: Report problems on GitHub

---

**For more examples and patterns, see the tests/ directory and examples/ folder in the repository.**
