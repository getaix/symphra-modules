# Development Guide

## Development Environment Setup

### Environment Requirements

- Python 3.11+
- uv (recommended) or pip
- Git

### Install Development Dependencies

```bash
# Clone project
git clone https://github.com/getaix/symphra-modules.git
cd symphra-modules

# Install with uv (recommended)
uv sync --dev

# Or with pip
pip install -e .[dev]
```

### Development Tools

The project uses the following development tools:

- **Black**: Code formatting
- **isort**: Import sorting
- **mypy**: Static type checking
- **ruff**: Code checking and fixing
- **pytest**: Unit testing
- **coverage**: Test coverage

## Code Standards

### Type Annotations

The project requires 100% type coverage with strict mypy configuration:

```python
from typing import Optional, Dict, List

def process_data(data: Dict[str, Any]) -> Optional[List[str]]:
    """Process data and return result list."""
    if not data:
        return None
    return [item.upper() for item in data.values()]
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_total(items: List[Dict[str, float]]) -> float:
    """Calculate item total price.

    Args:
        items: List of items containing price information

    Returns:
        Total price

    Raises:
        ValueError: When item price is invalid

    Example:
        >>> calculate_total([{"price": 10.0}, {"price": 20.0}])
        30.0
    """
    return sum(item["price"] for item in items)
```

### Naming Conventions

- Classes: `PascalCase`
- Functions and variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private members: prefix `_`

## Project Structure

```
src/symphra_modules/
├── __init__.py          # Package initialization
├── abc.py              # Abstract base classes
├── config.py           # Configuration management
├── events/             # Event system
├── exceptions.py       # Exception definitions
├── loader/             # Module loaders
├── manager.py          # Module manager
├── registry.py         # Module registry
├── resolver/           # Dependency resolver
└── utils/              # Utility functions

tests/                  # Test files
├── unit/              # Unit tests
├── integration/       # Integration tests
└── fixtures/          # Test fixtures

docs/                  # Documentation
├── guide/            # User guides
├── api/              # API documentation
└── examples/         # Examples

examples/              # Usage examples
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/new-feature
```

### 2. Write Code

Follow these principles:

- **SOLID principles**: Single responsibility, open-closed, etc.
- **DRY principle**: Don't repeat yourself
- **KISS principle**: Keep it simple

### 3. Write Tests

Write comprehensive tests for new features:

```python
# tests/unit/test_new_feature.py
import pytest
from symphra_modules import NewFeature

class TestNewFeature:
    def test_basic_functionality(self):
        feature = NewFeature()
        result = feature.process("input")
        assert result == "expected_output"

    def test_edge_cases(self):
        feature = NewFeature()
        with pytest.raises(ValueError):
            feature.process(None)
```

### 4. Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_new_feature.py

# With coverage report
pytest --cov=symphra_modules --cov-report=html
```

### 5. Code Checking

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/

# Code checking
ruff check src/ tests/

# Auto fix
ruff fix src/ tests/
```

### 6. Commit Code

```bash
git add .
git commit -m "feat: add new feature

- Add NewFeature class
- Implement process method
- Add comprehensive tests
- Update documentation"
```

## Contribution Guidelines

### Commit Message Format

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Fix
- `docs`: Documentation update
- `style`: Code style adjustment
- `refactor`: Refactoring
- `test`: Test related
- `chore`: Build/tool related

### Pull Request Process

1. Fork project
2. Create feature branch
3. Submit changes
4. Push branch
5. Create Pull Request
6. Wait for code review
7. Merge changes

## Debugging Tips

### Logging

Use structured logging:

```python
import logging

logger = logging.getLogger(__name__)

def process_data(data):
    logger.debug("Processing data: %s", data)
    try:
        result = do_processing(data)
        logger.info("Data processed successfully")
        return result
    except Exception as e:
        logger.error("Failed to process data: %s", e)
        raise
```

### Debugging Async Code

```python
import asyncio

async def debug_async_function():
    print("Starting async function")
    await asyncio.sleep(1)
    print("Async function completed")

# Run with debug mode
asyncio.run(debug_async_function(), debug=True)
```

## Performance Optimization

### Performance Analysis

```python
import cProfile
import pstats

def profile_function():
    # Code to analyze
    pass

profiler = cProfile.Profile()
profiler.enable()
profile_function()
profiler.disable()

stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats()
```

### Memory Optimization

- Use `__slots__` to reduce memory usage
- Avoid circular references
- Use weak references for caching

```python
class OptimizedClass:
    __slots__ = ('name', 'value')

    def __init__(self, name, value):
        self.name = name
        self.value = value
```

## Testing Strategy

### Unit Testing

Test individual components:

```python
def test_module_lifecycle():
    module = TestModule()
    assert module.state == ModuleState.NOT_INSTALLED

    module.install()
    assert module.state == ModuleState.INSTALLED

    module.start()
    assert module.state == ModuleState.STARTED
```

### Integration Testing

Test component interactions:

```python
def test_module_dependencies():
    manager = ModuleManager()

    # Load modules with dependencies
    await manager.load_from_directory("./test_modules")

    # Verify dependency resolution
    await manager.start_all()

    # Verify all modules started correctly
    assert all(module.is_started for module in manager.get_modules())
```

### Async Testing

```python
import pytest_asyncio

@pytest.mark.asyncio
async def test_async_module():
    module = AsyncModule()
    await module.start()
    assert module.is_started
    await module.stop()
    assert not module.is_started
```

## Release Process

### Version Management

Use semantic versioning:

- `MAJOR.MINOR.PATCH`
- `MAJOR`: Incompatible API changes
- `MINOR`: Backward compatible feature additions
- `PATCH`: Backward compatible fixes

### Release Steps

1. Update version number
2. Update changelog
3. Create release tag
4. Build distribution package
5. Upload to PyPI

```bash
# Update version
uv version patch

# Build
uv build

# Publish
uv publish
```

## Common Issues

### Import Errors

```python
# Error: Relative import issues in executable scripts
from ..utils import helper  # May fail in executable scripts

# Correct: Use absolute imports
from symphra_modules.utils import helper
```

### Async/Sync Mixing

```python
# Error: Mixing async def and def
class MixedModule(BaseModule):
    async def start(self):  # async
        pass

    def stop(self):  # sync
        pass  # This may cause issues

# Correct: Keep consistent
class AsyncModule(BaseModule):
    async def start(self):
        pass

    async def stop(self):
        pass
```

### Circular Dependencies

```python
# Error: Circular dependencies
# module_a.py depends on module_b
# module_b.py depends on module_a

# Correct: Refactor to avoid cycles
# Use event system or extract common code to independent modules
```

## Resource Links

- [Python Official Documentation](https://docs.python.org/3/)
- [Typing Module Documentation](https://docs.python.org/3/library/typing.html)
- [AsyncIO Documentation](https://docs.python.org/3/library/asyncio.html)
- [Pytest Documentation](https://docs.pytest.org/)
- [MyPy Documentation](https://mypy.readthedocs.io/)