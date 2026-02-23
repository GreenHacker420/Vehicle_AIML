from __future__ import annotations

import sys
from pathlib import Path


# Vercel Python runtime starts from repository root. Add backend directory so
# existing `from app...` imports continue to work without changing app code.
ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402  # pylint: disable=wrong-import-position

