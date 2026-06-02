# Contributing to LinguaResume

> Guidelines for contributing code, documentation, and improvements

## Code of Conduct

- Be respectful and professional
- Welcome diverse perspectives
- Focus on constructive feedback
- Help others learn and grow

## Getting Started

### Prerequisites

- Python 3.8+
- Git
- Virtual environment setup (see SETUP.md)

### Development Environment

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/linguaresume.git
   cd linguaresume
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set up development environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Install pre-commit hooks (optional)**
   ```bash
   pre-commit install
   ```

---

## Development Workflow

### 1. Making Changes

#### Code Style

- **Python**: Follow PEP 8
- **Naming**: Use descriptive names
  - Functions: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
- **Type Hints**: Add type annotations where possible
- **Docstrings**: Use triple-quoted strings for modules, classes, and functions

#### Example Function

```python
def validate_companies(final_md: str, master_companies: Set[str], 
                      translating: bool = False) -> bool:
    """
    Validate that all master companies are present in final markdown.
    
    Args:
        final_md: Final markdown content to validate
        master_companies: Set of company names from master CV
        translating: If True, allow missing companies during translation
        
    Returns:
        True if validation passes, False otherwise
        
    Raises:
        ValueError: If markdown is malformed
    """
    # Implementation...
```

#### Code Organization

```
linguaresume/
├── module_name/
│   ├── __init__.py          # Public API
│   ├── implementation.py    # Main logic
│   └── helpers.py          # Utility functions
└── __init__.py
```

### 2. Testing

#### Run Tests

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/test_engine_mockllm.py

# With coverage
pytest --cov=linguaresume tests/

# Verbose output
pytest -v tests/

# Stop at first failure
pytest -x tests/
```

#### Writing Tests

```python
# tests/test_my_feature.py
import pytest
from linguaresume.module_name import my_function

class TestMyFeature:
    """Test cases for my_feature."""
    
    def test_basic_functionality(self):
        """Test basic case."""
        result = my_function("input")
        assert result == "expected_output"
    
    def test_edge_case(self):
        """Test edge case."""
        result = my_function("")
        assert result is None
    
    @pytest.mark.skip(reason="Not implemented yet")
    def test_future_feature(self):
        """Test for feature not yet implemented."""
        pass
```

#### Test Coverage

Aim for >80% code coverage:

```bash
pytest --cov=linguaresume --cov-report=html tests/
# Opens: htmlcov/index.html
```

### 3. Documentation

#### Code Comments

```python
# Use for non-obvious logic
# BAD:
x = y + 1  # Add one

# GOOD:
# Increment to account for 0-based indexing
array_length = element_count + 1
```

#### Docstrings

```python
"""Module docstring describing purpose."""

class MyClass:
    """Class description with main purpose."""
    
    def __init__(self, param1: str, param2: int):
        """Initialize with parameters."""
        self.param1 = param1
        self.param2 = param2
    
    def do_something(self) -> bool:
        """
        Do something meaningful.
        
        Returns:
            True if successful
        """
        pass
```

### 4. Commit Guidelines

```bash
# Good commit messages
git commit -m "Fix: Handle empty CV files gracefully"
git commit -m "Feature: Add Spanish language support"
git commit -m "Docs: Update README installation steps"
git commit -m "Refactor: Simplify validation logic"
git commit -m "Test: Add edge case tests for date parsing"

# Bad commit messages
git commit -m "Fix bug"
git commit -m "asdf"
git commit -m "updates"
```

**Commit Message Format**:
```
<type>: <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style (formatting, semicolons, etc)
- `refactor`: Code refactoring without new features
- `perf`: Performance improvements
- `test`: Test additions/modifications
- `ci`: CI/CD configuration

Example:
```
feat: Add support for multiple languages in section aliases

- Extend section_aliases to handle German, French, and English variants
- Update parser to normalize header names before matching
- Add tests for multi-language CV parsing

Fixes #123
Closes #456
```

---

## Pull Request Process

### Before Submitting

1. **Update your branch**
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Run tests**
   ```bash
   pytest tests/ -v
   ```

3. **Check code style**
   ```bash
   # Optional: auto-format with black
   pip install black
   black linguaresume/
   ```

4. **Update documentation**
   - Update README if behavior changed
   - Add docstrings to new functions
   - Update CHANGELOG

### Creating a Pull Request

1. **Push your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create PR on GitHub**
   - Title: Clear, concise description
   - Description: What changed and why
   - Reference issues: "Fixes #123"

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Fixes #(issue number)

## Testing
- [ ] Added tests
- [ ] All tests pass
- [ ] Code coverage maintained

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have updated documentation
- [ ] I have added tests
- [ ] No new warnings generated
```

### Responding to Reviews

- Be respectful and open to feedback
- Make requested changes on the same branch
- Mark conversations as resolved when complete
- Push additional commits (don't force push)

---

## Adding New Features

### Feature: New Language Support

1. **Create master CVs**
   ```
   cvs/master_XX.md        (where XX is language code)
   cvs/devops_XX.md
   cvs/web_XX.md
   cvs/nontech_master_XX.md
   ```

2. **Update config.yaml**
   ```yaml
   cv_map:
     xx_fullstack: "./cvs/master_XX.md"
     xx_devops: "./cvs/devops_XX.md"
     # ... etc
   ```

3. **Update section_aliases**
   ```yaml
   section_aliases:
     profile:
       - "Existing translations"
       - "New XX translation"
   ```

4. **Update language detection**
   ```python
   # In linguaresume/tailoring/engine.py
   def detect_language(text: str) -> str:
       # Add XX-specific keywords
       xx_words = {"word1", "word2", ...}
   ```

5. **Add tests**
   ```python
   def test_language_detection_xx():
       text = "Sample text in language XX"
       assert detect_language(text) == "xx"
   ```

### Feature: New Validation Rule

1. **Create validation module**
   ```python
   # linguaresume/validation/new_rule.py
   def validate_new_rule(master_md: str, final_md: str) -> bool:
       """Validate new_rule."""
       # Implementation
   ```

2. **Register in engine**
   ```python
   # linguaresume/tailoring/engine.py
   def _validate_and_retry(...):
       validators = [
           (validate_companies, "companies"),
           (validate_new_rule, "new_rule"),  # Add here
       ]
   ```

3. **Add tests**
   ```python
   def test_validate_new_rule():
       master = "..."
       final = "..."
       assert validate_new_rule(master, final) == True
   ```

### Feature: New LLM Provider

1. **Implement client**
   ```python
   # In linguaresume/llm/client.py
   class NewProviderClient(LLMClient):
       def __init__(self, api_key: str, **kwargs):
           self.api_key = api_key
       
       def complete(self, system: str, user: str) -> str:
           # Implementation
   ```

2. **Register in CLI**
   ```python
   # In linguaresume/cli.py
   def _build_llm_client(cfg, api_key=None):
       if os.getenv("NEW_PROVIDER_KEY"):
           return NewProviderClient(os.getenv("NEW_PROVIDER_KEY"))
   ```

3. **Add tests**
   ```python
   def test_new_provider_client():
       client = NewProviderClient("test-key")
       response = client.complete("system", "user")
       assert isinstance(response, str)
   ```

---

## Issue Templates

### Bug Report

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. ...
2. ...

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment**
- OS: [e.g. Ubuntu 20.04]
- Python: [e.g. 3.10.2]
- LLM: [Ollama/OpenAI]
- Model: [e.g. mistral:7b]

**Additional context**
Add any other context.
```

### Feature Request

```markdown
**Is your feature request related to a problem?**
Description of the problem.

**Describe the solution**
Your proposed solution.

**Describe alternatives**
Alternative approaches.

**Additional context**
Add any other context.
```

---

## Coding Standards

### Imports

```python
# Order: standard library, third-party, local
import os
import sys
from typing import Dict, List, Optional

import requests
import yaml

from linguaresume.config import Config
from linguaresume.llm.client import LLMClient
```

### Type Hints

```python
# All public functions should have type hints
def process_cv(cv_path: str, config: Config) -> str:
    """Process a CV file."""
    pass

# Use Optional for nullable types
def get_value(data: Dict[str, str], key: str) -> Optional[str]:
    """Get value from dict."""
    return data.get(key)

# Use Union for multiple types
from typing import Union
def parse_value(value: Union[str, int]) -> bool:
    """Parse value."""
    pass
```

### Error Handling

```python
# Good: Specific exceptions
try:
    config = Config.from_yaml(path)
except FileNotFoundError:
    logger.error(f"Config file not found: {path}")
except yaml.YAMLError as e:
    logger.error(f"Invalid YAML: {e}")

# Bad: Bare except
try:
    config = Config.from_yaml(path)
except:
    pass
```

### Logging

```python
import logging

logger = logging.getLogger("linguaresume")

# Use appropriate log levels
logger.debug("Detailed debugging info")
logger.info("General information")
logger.warning("Something unexpected")
logger.error("Something failed")
```

---

## Performance Guidelines

### Optimization Checklist

- [ ] Use caching for repeated operations
- [ ] Avoid unnecessary file I/O
- [ ] Use generators for large datasets
- [ ] Profile before optimizing
- [ ] Document performance trade-offs

### Benchmarking

```python
import time

start = time.time()
result = my_function()
duration = time.time() - start
print(f"Took {duration:.2f} seconds")
```

---

## Security Guidelines

- ✅ **Validate** user input
- ✅ **Sanitize** before using in commands
- ✅ **Escape** special characters
- ❌ **Don't** hardcode secrets in code
- ❌ **Don't** log sensitive data
- ❌ **Don't** use `eval()` or `exec()`

### Environment Variables

```python
import os

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")
```

---

## Documentation Standards

### README Sections

- [x] Project description
- [x] Features
- [x] Installation
- [x] Quick start
- [x] Usage examples
- [x] Architecture overview
- [x] Contributing
- [x] License

### Code Documentation

- Module docstring at top
- Class docstring below class definition
- Function docstring before implementation
- Complex logic comments
- Type hints for all public functions

---

## Release Process

### Version Numbering

Follow Semantic Versioning: `MAJOR.MINOR.PATCH`
- `MAJOR`: Breaking changes
- `MINOR`: New features (backward compatible)
- `PATCH`: Bug fixes

### Release Checklist

- [ ] All tests pass
- [ ] Update CHANGELOG.md
- [ ] Update version in `__init__.py`
- [ ] Update README if needed
- [ ] Create git tag
- [ ] Build and test distribution
- [ ] Push to repository
- [ ] Create GitHub release

---

## Getting Help

### Resources

- **Issues**: GitHub Issues for bugs/features
- **Discussions**: GitHub Discussions for questions
- **Documentation**: See README.md, ARCHITECTURE.md, SETUP.md
- **Code Examples**: See tests/ directory

### Asking Questions

- Search existing issues first
- Provide minimal reproducible example
- Include Python version, OS, error messages
- Attach log output if applicable

---

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Credited in release notes
- Added to GitHub contributors page

Thank you for contributing! 🎉

---

## Additional Resources

- [PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**Questions? Open an issue or start a discussion on GitHub!**
