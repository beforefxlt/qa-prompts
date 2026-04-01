from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    target = root / "backend" / "tests" / "resilience"
    if not target.exists():
        print(f"[skip] missing {target}")
        return 0
    return subprocess.call(["pytest", str(target)], cwd=root)


if __name__ == "__main__":
    sys.exit(main())
