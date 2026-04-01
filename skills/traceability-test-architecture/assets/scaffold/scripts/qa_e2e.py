from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    frontend = root / "frontend"
    if not frontend.exists():
        print(f"[skip] missing {frontend}")
        return 0
    return subprocess.call(["npx", "playwright", "test"], cwd=frontend)


if __name__ == "__main__":
    sys.exit(main())
