"""Write (or --check) the small program fixtures in examples/programs used by the README walkthrough."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crw.attributes import Catalog  # noqa: E402
from crw.impact import TierScale, assess_change, matrix_long_rows  # noqa: E402
from crw.program_reference import reference_catalog, reference_tier_scale  # noqa: E402
from crw.synthetic_program import generate_parties  # noqa: E402

OUT = ROOT / "examples" / "programs"
FIELDS = ["party_id", "segment", "tier", "pinned"]
PRE = [
    ("EX-01", "SEGMENT_A", "LOW", 0), ("EX-02", "SEGMENT_A", "LOW", 0), ("EX-03", "SEGMENT_A", "MODERATE", 0),
    ("EX-04", "SEGMENT_A", "HIGH", 0), ("EX-05", "SEGMENT_A", "VERY_HIGH", 1), ("EX-06", "SEGMENT_B", "LOW", 0),
    ("EX-07", "SEGMENT_B", "MODERATE", 0), ("EX-08", "SEGMENT_B", "MODERATE", 0), ("EX-09", "SEGMENT_B", "HIGH", 0),
    ("EX-10", "SEGMENT_B", "LOW", 0),
]
POST = [
    ("EX-01", "SEGMENT_A", "LOW", 0), ("EX-02", "SEGMENT_A", "MODERATE", 0), ("EX-03", "SEGMENT_A", "MODERATE", 0),
    ("EX-04", "SEGMENT_A", "VERY_HIGH", 0), ("EX-05", "SEGMENT_A", "VERY_HIGH", 1), ("EX-06", "SEGMENT_B", "LOW", 0),
    ("EX-07", "SEGMENT_B", "LOW", 0), ("EX-08", "SEGMENT_B", "MODERATE", 0), ("EX-09", "SEGMENT_B", "HIGH", 0),
    ("EX-11", "SEGMENT_B", "HIGH", 0),
]
CONFIG = {
    "assessment_id": "IA-EXAMPLE-01",
    "description": "Ten-party hand-checkable example: two up, one down, one pinned exclusion, one exit, one entrant.",
    "pre_label": "example before", "post_label": "example after", "exclude_pinned": True,
    "segments": {"SEGMENT_A": {"mode": "paired"}, "SEGMENT_B": {"mode": "paired"}},
}
MANIFEST = {
    "change_id": "CHG-EXAMPLE-01", "release": "example", "description": "Illustrative reclassification.",
    "change_type": "value_classification",
    "expected_effects": [
        {"id": "EXP-UP", "segments": ["SEGMENT_A"], "from": ["*"], "to": ["*"], "direction": "up",
         "count": {"min": 2, "max": 2}, "rationale": "Two parties hold the escalated value."},
        {"id": "EXP-DOWN", "segments": ["*"], "from": ["MODERATE"], "to": ["LOW"], "direction": "down",
         "count": {"min": 1, "max": 1}, "rationale": "One party holds the de-escalated value."},
    ],
    "expected_population": {"entrants": {"min": 0, "max": 1}, "exits": {"min": 0, "max": 1},
                            "rationale": "Ordinary onboarding and closure between snapshots."},
}


def csv_text(rows) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(FIELDS)
    writer.writerows(rows)
    return buffer.getvalue()


def files() -> dict[str, str]:
    dicts = lambda rows: [dict(zip(FIELDS, (a, b, c, str(d)))) for a, b, c, d in rows]  # noqa: E731
    assessment = assess_change(dicts(PRE), dicts(POST), CONFIG, TierScale(reference_tier_scale()), partitions=1)
    standard = "segment,pre_tier,post_tier,count\n" + "".join(
        f"{r['segment']},{r['pre_tier']},{r['post_tier']},{r['count']}\n" for r in matrix_long_rows(assessment))
    parties = generate_parties(Catalog(reference_catalog()), 300, 5)
    return {
        "snapshot-pre.csv": csv_text(PRE),
        "snapshot-post.csv": csv_text(POST),
        "assessment-config.json": json.dumps(CONFIG, indent=2, sort_keys=True) + "\n",
        "change-manifest.json": json.dumps(MANIFEST, indent=2, sort_keys=True) + "\n",
        "standard-matrix.csv": standard,
        "parties-sample.jsonl": "".join(json.dumps(p, sort_keys=True) + "\n" for p in parties),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale = []
    for name, text in files().items():
        path = OUT / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(name)
        else:
            OUT.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
    if stale:
        print("stale examples: " + ", ".join(stale))
        sys.exit(1)
    print(("checked " if args.check else "wrote ") + "program examples")


if __name__ == "__main__":
    main()
