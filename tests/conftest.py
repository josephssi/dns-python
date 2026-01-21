import sys
from pathlib import Path

# Ensure project `src/` is importable for tests
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
