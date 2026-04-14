from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
CWD_BACKEND = Path(os.getcwd()) / "backend"

# Add all candidate directories to sys.path so the backend package is importable
# both locally and inside the Vercel serverless runtime.
for p in [str(BACKEND_DIR), str(CWD_BACKEND), str(ROOT_DIR), os.getcwd()]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from app.main import app  # noqa: E402
except Exception:
    import traceback
    traceback.print_exc()
    raise
