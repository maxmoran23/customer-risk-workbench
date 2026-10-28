"""Summarize retained test and demonstration evidence without local paths."""

from __future__ import annotations

import json
from pathlib import Path
import platform
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / name).read_text())


def main():
    suite = ET.parse(ROOT / "runs/pytest.xml").getroot().find("testsuite")
    coverage = read("runs/coverage.json")
    demo = read("evidence/demo-summary.json")
    research = read("evidence/research.json")
    numerical = read("evidence/numerical-crosscheck.json")
    scenarios = read("evidence/scenario-results.json")
    wheel = read("evidence/wheel-check.json")
    result = {
        "release_version": "0.1.0",
        "verified_date": "2026-10-28",
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "research_versions": numerical["versions"],
        },
        "automated_tests": {k: int(suite.attrib[k]) for k in ["tests", "failures", "errors", "skipped"]},
        "statement_coverage": coverage["totals"],
        "coverage_by_module": {name: value["summary"] for name, value in coverage["files"].items()},
        "scenarios": {k: scenarios[k] for k in ["total", "passed", "failed"]},
        "demo": demo,
        "research": {
            "customers_per_experiment": research["customers_per_experiment"],
            "seeds": research["seeds"],
            "refitted_experiments": len(research["experiments"]),
            "frozen_model_seed_combinations": sum(len(s["models"]) for s in research["frozen_model_stress"]),
            "frozen_stress_comparisons": sum(
                len(m["scenarios"]) for s in research["frozen_model_stress"] for m in s["models"].values()
            ),
        },
        "numerical_crosscheck": {
            k: numerical[k]
            for k in [
                "cases",
                "comparisons",
                "undefined_checks",
                "maximum_absolute_error",
                "absolute_tolerance",
                "passed",
            ]
        },
        "wheel_check": wheel,
        "browser_spot_check": {
            "application": "Safari",
            "scope": [
                "overview renders retained counts",
                "customer search and selection",
                "missing-ownership stress details",
                "threshold control changes displayed boundary",
                "research metrics and fixed-model section",
            ],
            "limit": "Manual selected desktop interactions; no exhaustive cross-browser, mobile or accessibility certification.",
        },
        "review": {
            "type": "AI-assisted implementation and document review",
            "closed_findings": [
                "historical batch population eligibility",
                "standalone concurrent snapshot consistency",
                "amount-unit lineage",
                "duplicate stress baseline identifiers",
                "missing-evidence stress display semantics",
            ],
            "scope_limit": "Bounded reviews and executable regressions; not institutional independent validation.",
        },
        "limits": [
            "Synthetic evidence cannot establish real-world detection effectiveness.",
            "Statement coverage counts executed Python statements; it is not behavioral completeness and does not cover browser rendering.",
            "Benchmarks were observed on a development machine with concurrent activity; they are not controlled capacity estimates.",
            "Local evidence and external CI status are separate; see the repository Actions history for remote execution.",
        ],
    }
    assert result["automated_tests"]["failures"] == result["automated_tests"]["errors"] == 0
    assert scenarios["failed"] == 0 and numerical["passed"] and wheel["status"] == "passed"
    (ROOT / "evidence/verification.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"Recorded {result['automated_tests']['tests']} tests and {scenarios['total']} executable cases")


if __name__ == "__main__":
    main()
