# AGENTS.md - Development Guidelines for Agentic Coding

## Build/Lint/Test Commands

### Build Commands
- `python -m pip install -e .` - Install package in development mode
- `python setup.py build` - Build the package

### Test Commands
- `python -m pytest` - Run all tests
- `python -m pytest tests/test_specific.py::TestClass::test_method` - Run single test
- `python -m pytest --cov=package_name` - Run tests with coverage
- `python -m pytest -v` - Run tests with verbose output

### Lint and Format Commands
- `ruff check .` - Check code with ruff linter
- `ruff format .` - Format code with ruff
- `black .` - Format code with black
- `mypy .` - Type check with mypy

### Development Setup
- `pip install -r requirements-dev.txt` - Install development dependencies
- `pre-commit install` - Install pre-commit hooks

## Code Style Guidelines

### Imports
- Use absolute imports over relative imports
- Group imports: standard library, third-party, local modules
- Sort imports alphabetically within groups
- Use `from __future__ import annotations` for type hints in Python 3.7+

```python
# Good
from __future__ import annotations

import asyncio
import json
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
```

### Formatting
- Use 4 spaces for indentation
- Line length: 88 characters (Black default)
- Use double quotes for strings, single quotes for characters
- Use trailing commas in multi-line structures

### Types and Typing
- Use type hints for all function parameters and return values
- Use `typing` module imports for complex types
- Use `Union` sparingly, prefer `|` syntax in Python 3.10+
- Use `NotRequired` for optional TypedDict fields

```python
from typing import Any, Dict, Optional

def process_data(data: Dict[str, Any]) -> Optional[str]:
    # Implementation
    pass
```

### Naming Conventions
- Classes: PascalCase
- Functions/methods: snake_case
- Constants: UPPER_CASE
- Private methods: _leading_underscore
- Protected methods: __double_leading_underscore

### Error Handling
- Use specific exceptions over generic `Exception`
- Provide meaningful error messages
- Use context managers for resource management
- Log errors appropriately with proper log levels

```python
try:
    result = api_call()
except ConnectionError as err:
    _LOGGER.error("Failed to connect to API: %s", err)
    return None
except ValueError as err:
    _LOGGER.warning("Invalid data received: %s", err)
    return None
```

### Async/Await
- Use async/await for I/O operations
- Prefer async context managers
- Use `asyncio.gather()` for concurrent operations
- Avoid blocking operations in async functions

### Home Assistant Integration Specific
- Follow HA entity naming patterns
- Use proper entity categories and device classes
- Implement proper state updates and availability
- Handle configuration entry updates gracefully

### Security
- Never log sensitive information (passwords, tokens, keys)
- Use proper validation for user inputs
- Implement proper timeouts for network requests
- Follow principle of least privilege

### Testing
- Write unit tests for all public functions
- Use fixtures for common test setup
- Mock external dependencies
- Test error conditions and edge cases
- Aim for >80% code coverage

### Documentation
- Use docstrings for all public functions/classes
- Follow Google/NumPy docstring format
- Document parameters, return values, and exceptions
- Keep README and documentation up to date

## Project Structure
```
custom_components/integration_name/
├── __init__.py          # Integration setup
├── config_flow.py       # Configuration flow
├── const.py            # Constants
├── sensor.py           # Sensor entities
├── switch.py           # Switch entities (if needed)
├── manifest.json       # Integration manifest
└── services.yaml       # Service definitions (if needed)
```

## Git Workflow
- Use conventional commits
- Create feature branches from main
- Squash commits before merging
- Use pull requests for code review
- Keep commits atomic and focused