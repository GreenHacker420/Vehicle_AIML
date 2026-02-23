from __future__ import annotations

import os
import sys
from pathlib import Path

# --- Debug: print filesystem info visible in Vercel runtime logs ---
print(f"[vercel-debug] cwd={os.getcwd()}", flush=True)
print(f"[vercel-debug] __file__={__file__}", flush=True)
print(f"[vercel-debug] resolved={Path(__file__).resolve()}", flush=True)

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
CWD_BACKEND = Path(os.getcwd()) / "backend"

print(f"[vercel-debug] ROOT_DIR={ROOT_DIR} exists={ROOT_DIR.exists()}", flush=True)
print(f"[vercel-debug] BACKEND_DIR={BACKEND_DIR} exists={BACKEND_DIR.exists()}", flush=True)
print(f"[vercel-debug] CWD_BACKEND={CWD_BACKEND} exists={CWD_BACKEND.exists()}", flush=True)

# Check model file in various locations
for model_candidate in [
    ROOT_DIR / "model" / "vehicle_maintenance_pipeline.pkl",
    Path(os.getcwd()) / "model" / "vehicle_maintenance_pipeline.pkl",
    BACKEND_DIR.parent / "model" / "vehicle_maintenance_pipeline.pkl",
]:
    print(f"[vercel-debug] model at {model_candidate} exists={model_candidate.exists()}", flush=True)

# Add all candidate directories to sys.path
for p in [str(BACKEND_DIR), str(CWD_BACKEND), str(ROOT_DIR), os.getcwd()]:
    if p not in sys.path:
        sys.path.insert(0, p)

print(f"[vercel-debug] sys.path={sys.path[:6]}", flush=True)

try:
    from app.main import app  # noqa: E402
    print("[vercel-debug] app.main imported successfully", flush=True)
except Exception:
    import traceback
    traceback.print_exc()
    raise
