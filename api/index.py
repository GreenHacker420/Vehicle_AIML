from __future__ import annotations

import os
import sys
from pathlib import Path


# Vercel Python runtime: cwd = repository root.
# Add backend/ so `from app...` imports work.
ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"

CWD_BACKEND = Path(os.getcwd()) / "backend"

for p in [str(ROOT_DIR), str(BACKEND_DIR), str(CWD_BACKEND), os.getcwd()]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from app.main import app  
except Exception as exc:
    import traceback
    traceback.print_exc()
    raise

