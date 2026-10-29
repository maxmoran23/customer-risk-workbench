"""Write (or --check) the illustrative program configurations under configs/programs from code."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crw.program_reference import (reference_assessment_config, reference_catalog, reference_model,  # noqa: E402
                                   reference_party_roles, reference_rules, reference_tier_scale)

TARGETS = {
    "catalog.json": reference_catalog,
    "model.json": reference_model,
    "rules.json": reference_rules,
    "party-roles.json": reference_party_roles,
    "tier-scale.json": reference_tier_scale,
    "assessment-config.json": reference_assessment_config,
}


def render(builder) -> str:
    return json.dumps(builder(), indent=2, sort_keys=True) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    directory = ROOT / "configs" / "programs"
    stale = []
    for name, builder in TARGETS.items():
        path = directory / name
        text = render(builder)
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(name)
        else:
            directory.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
    if stale:
        print("stale program configurations: " + ", ".join(stale))
        sys.exit(1)
    print(("checked " if args.check else "wrote ") + f"{len(TARGETS)} program configurations")


if __name__ == "__main__":
    main()
