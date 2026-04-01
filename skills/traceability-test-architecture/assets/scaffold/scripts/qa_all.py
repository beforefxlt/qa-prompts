from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPTS = [
    "qa_unit.py",
    "qa_contract.py",
    "qa_integration.py",
    "qa_resilience.py",
    "qa_golden.py",
    "qa_e2e.py",
    "qa_audit.py",
]


def main() -> int:
    scripts_dir = Path(__file__).resolve().parent
    failed = False
    for script_name in SCRIPTS:
        script_path = scripts_dir / script_name
        if not script_path.exists():
            print(f"[skip] missing {script_path}")
            continue
        print(f"[run] python {script_name}")
        code = subprocess.call([sys.executable, str(script_path)], cwd=scripts_dir.parents[1])
        if code != 0:
            failed = True
            print(f"[fail] {script_name} exited with {code}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
