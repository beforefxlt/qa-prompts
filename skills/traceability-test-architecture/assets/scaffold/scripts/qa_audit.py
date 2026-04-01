from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    traceability = root / "traceability.yaml"
    if not traceability.exists():
        print(f"[error] missing {traceability}")
        return 1

    content = traceability.read_text(encoding="utf-8")
    tc_total = len(re.findall(r"(?m)^\\s*-\\s*tc_id:\\s*", content))
    statuses = Counter(re.findall(r"(?m)^\\s*status:\\s*([a-z_]+)\\s*$", content))

    print("QA audit summary")
    print(f"total_tc: {tc_total}")
    print(f"automated: {statuses.get('automated', 0)}")
    print(f"stub: {statuses.get('stub', 0)}")
    print(f"missing: {statuses.get('missing', 0)}")
    print(f"manual: {statuses.get('manual', 0)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
