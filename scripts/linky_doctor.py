#!/usr/bin/env python3
"""Print Linky provider and optional dependency readiness as JSON.

Usage:
    python3 scripts/linky_doctor.py [--strategy references/fetch-strategy.toml]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] in {"-h", "--help"}:
        print(__doc__)
        return 0

    strategy_path = None
    if len(sys.argv) == 3 and sys.argv[1] == "--strategy":
        strategy_path = Path(sys.argv[2])
    elif len(sys.argv) not in {1, 3}:
        print(__doc__, file=sys.stderr)
        return 2

    from linky.doctor import doctor_report

    report = doctor_report(strategy_path)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
