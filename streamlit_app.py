"""Streamlit Community Cloud entry point redirecting to app.py."""
import sys
from pathlib import Path
import runpy

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Execute main app script
runpy.run_path(str(ROOT_DIR / "app.py"))
