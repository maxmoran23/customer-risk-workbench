#!/usr/bin/env python3
"""Regenerate scenario metadata from the same registry the executable runner uses."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from crw.scenarios import scenario_catalog


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path(__file__).resolve().parents[1] / "scenarios" / "catalog.json"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the committed catalog differs from the executable registry",
    )
    args = parser.parse_args()
    cases = scenario_catalog()
    data = {
        "schema_version": "1.0.0",
        "source": "src/crw/scenarios.py:scenario_catalog",
        "case_count": len(cases),
        "category_counts": dict(sorted(Counter(row["category"] for row in cases).items())),
        "interpretation": "Executable synthetic cases, not independent typologies or effectiveness observations.",
        "cases": cases,
    }
    text = json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != text:
            raise SystemExit(f"Scenario catalog is stale: regenerate {args.output}")
        print(f"Scenario catalog verified: {len(cases)} cases")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8", newline="\n")
        print(f"Wrote {len(cases)} cases to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
