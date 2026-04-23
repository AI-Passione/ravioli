# Tests

This directory mirrors the structure of `src/ravioli/` and contains all unit tests for the Ravioli project.

## Running Tests

All commands should be run from the project root (`ravioli/`):

```bash
# Run all tests
uv run pytest tests/

# Run with verbose output
uv run pytest tests/ -v

# Run a specific test file
uv run pytest tests/ravioli/backend/core/test_dbt.py

# Run a specific test function
uv run pytest tests/ravioli/backend/core/test_dbt.py::test_run_dbt_command_success

# Run with coverage report
uv run pytest tests/ --cov=src/ravioli
```

## Directory Structure

```
tests/
└── ravioli/
    ├── ai/                  # Tests for src/ravioli/ai
    ├── backend/
    │   └── core/
    │       └── test_dbt.py  # Tests for src/ravioli/backend/core/dbt.py
    └── frontend/            # Tests for src/ravioli/frontend
```

## Adding New Tests

- Mirror the source path: `src/ravioli/backend/core/foo.py` → `tests/ravioli/backend/core/test_foo.py`
- Name test files with the `test_` prefix
- Name test functions with the `test_` prefix
