# Planted Tests

This directory contains the test suite for the Planted application.

## Structure

```
tests/
├── __init__.py
├── conftest.py           # Shared fixtures and configuration
├── unit/                 # Unit tests for individual modules
│   ├── __init__.py
│   └── test_sample.py    # Sample test file
└── integration/          # Integration tests for combined functionality
    └── __init__.py
```

## Running Tests

Make sure you have pytest installed:

```bash
pip install pytest pytest-cov
```

### Run all tests:
```bash
pytest
```

### Run with coverage:
```bash
pytest --cov=garden_manager --cov-report=html
```

### Run specific test file:
```bash
pytest tests/unit/test_sample.py
```

### Run tests matching a pattern:
```bash
pytest -k "test_season"
```

## Writing Tests

1. **Unit Tests**: Place in `tests/unit/`
   - Test individual functions and classes
   - Mock external dependencies
   - Focus on single units of functionality

2. **Integration Tests**: Place in `tests/integration/`
   - Test multiple components working together
   - Test database operations
   - Test API endpoints

3. **Fixtures**: Add shared fixtures to `conftest.py`

## Test Coverage Goals

- Aim for 80%+ code coverage
- Prioritize testing critical functionality:
  - Database operations
  - Care scheduling logic
  - Weather integration
  - Plant data management

## Continuous Integration

Tests are automatically run on every push via GitHub Actions.
Check the `.github/workflows/` directory for CI configuration.

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure all tests pass before submitting PR
3. Maintain or improve code coverage
4. Follow existing test patterns and naming conventions
