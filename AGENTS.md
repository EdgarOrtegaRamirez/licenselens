# LicenseLens - Agent Instructions

## Project Overview
Multi-ecosystem dependency license auditor with conflict detection and compliance reporting.

## Build & Test
```bash
pip install -e ".[dev]"
pytest tests/ -v
ruff check .
```

## Architecture
- `parser/` - Ecosystem-specific dependency parsers (Python, Node, Go, Rust)
- `classifier.py` - License classification and compatibility matrix
- `resolver.py` - License resolution via APIs (PyPI, npm, crates.io)
- `analyzer.py` - Main analysis engine
- `reporter.py` - Report generation (text, markdown, JSON, CSV)
- `cli.py` - Click CLI interface

## Key Design Decisions
- Each ecosystem has its own parser class inheriting from BaseParser
- License compatibility is checked using a compatibility matrix (dict of tuples)
- Offline mode skips API calls and marks all licenses as UNKNOWN
- Reports support 4 output formats for different use cases
- Exit code 1 when issues are found (CI-friendly)

## Adding New Ecosystems
1. Create a new parser in `parser/` inheriting from `BaseParser`
2. Implement `ecosystem`, `file_patterns`, `can_parse`, `parse`
3. Register in `analyzer.py`'s `ALL_PARSERS` list
4. Add resolver function in `resolver.py`
5. Add tests in `tests/test_parser/`

## Adding License Rules
- Add licenses to `KNOWN_LICENSES` dict in `classifier.py`
- Add compatibility entries to `LICENSE_COMPATIBILITY` dict
- Add issue rules in `analyzer.py`'s `_generate_issues` function
