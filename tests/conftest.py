import sys
from pathlib import Path

# Ensure project root is importable in tests (for `fast_routers`, `models`, `main`, etc.)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
