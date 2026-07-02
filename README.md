# LicenseLens

Multi-ecosystem dependency license auditor with conflict detection and compliance reporting.

## Features

- **Multi-ecosystem**: Python (pyproject.toml, requirements.txt, setup.cfg), Node.js (package.json), Go (go.mod), Rust (Cargo.toml)
- **License detection**: Automatic license resolution via PyPI, npm, and crates.io APIs
- **License classification**: Categorizes licenses as permissive, weak copyleft, strong copyleft, or network copyleft
- **Conflict detection**: Identifies incompatible license combinations using a compatibility graph
- **Compliance reporting**: Text, Markdown, JSON, and CSV output formats
- **Offline mode**: Works without network access (skips API calls)

## Quick Start

```bash
# Install
pip install -e .

# Audit current directory
licenselens audit .

# Audit with specific output format
licenselens audit . --format markdown --output report.md

# Audit offline (skip API calls)
licenselens audit . --offline

# Audit specific ecosystems only
licenselens audit . --ecosystem python --ecosystem node

# Detect ecosystems in a project
licenselens detect .

# Get info about a license
licenselens info MIT

# List all known licenses
licenselens licenses
```

## Supported Ecosystems

| Ecosystem | Files Parsed |
|-----------|-------------|
| Python    | pyproject.toml, setup.cfg, requirements.txt |
| Node.js   | package.json |
| Go        | go.mod |
| Rust      | Cargo.toml |

## License Categories

| Category | Icon | Examples |
|----------|------|----------|
| Permissive | ✅ | MIT, Apache-2.0, BSD, ISC |
| Weak Copyleft | ⚠️ | LGPL, MPL-2.0, EPL |
| Strong Copyleft | 🔴 | GPL-2.0, GPL-3.0 |
| Network Copyleft | 🚨 | AGPL-3.0, SSPL |
| Unknown | ❓ | Non-standard licenses |

## Architecture

```
licenselens/
├── src/licenselens/
│   ├── models.py      # Data models (Dependency, License, etc.)
│   ├── parser/        # Ecosystem-specific parsers
│   │   ├── base.py    # Base parser interface
│   │   ├── python.py  # pyproject.toml, requirements.txt, setup.cfg
│   │   ├── node.py    # package.json
│   │   ├── go.py      # go.mod
│   │   └── rust.py    # Cargo.toml
│   ├── classifier.py  # License classification & compatibility matrix
│   ├── resolver.py    # License resolution via APIs
│   ├── analyzer.py    # Main analysis engine
│   ├── reporter.py    # Report generation (text, markdown, JSON, CSV)
│   └── cli.py         # CLI interface
└── tests/             # Test suite (81 tests)
```

## How It Works

1. **Detection**: Automatically detects which ecosystems are present in a project
2. **Parsing**: Parses dependency files using ecosystem-specific parsers
3. **Resolution**: Resolves license information via PyPI/npm/crates.io APIs (or offline mode)
4. **Classification**: Classifies licenses into categories (permissive, copyleft, etc.)
5. **Conflict Detection**: Checks all license pairs for compatibility issues
6. **Reporting**: Generates reports in text, Markdown, JSON, or CSV formats

## Compatibility Matrix

The tool maintains a compatibility matrix of known license interactions:

- ✅ **MIT + Apache-2.0**: Compatible
- ✅ **MIT + GPL-2.0**: Compatible (can relicense)
- ❌ **Apache-2.0 + GPL-2.0**: Incompatible (patent clause conflict)
- ❌ **GPL-2.0 + GPL-3.0**: Incompatible (different versions)
- 🚨 **AGPL-3.0 + SSPL**: Incompatible

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
ruff check .
```

## License

MIT
