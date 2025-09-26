from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is importable so `src` package resolves when tests run individually.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
