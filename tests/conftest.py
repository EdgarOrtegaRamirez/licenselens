"""Pytest configuration for licenselens."""

import sys
from pathlib import Path

# Ensure src/ is on sys.path for editable installs
_src = str(Path(__file__).resolve().parent.parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)
