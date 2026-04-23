# Tests

This directory mirrors the structure of `src/ravioli/` and contains all unit tests for the Ravioli project.

## Running Tests

All commands should be run from the project root (`ravioli/`):

# Run backend tests
```bash
uv run pytest tests/
```

# Run frontend tests
```bash
npm --prefix src/ravioli/frontend test
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
