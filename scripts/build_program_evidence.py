"""Run the synthetic program demonstration and retain its summary and rendered report as public evidence."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from crw.program_demo import run_program_demo  # noqa: E402


def main():
    out = ROOT / "runs" / "program-evidence"
    summary = run_program_demo(out)
    assert summary["impact"]["sql_parity_identical"] and summary["impact"]["parity_verdict"] == "EXACT_MATCH"
    assert summary["impact"]["narrative_check"] == "grounded" and summary["impact"]["register"] == "intact"
    assert summary["attribute_review"]["planted_synergy_grade"] == "supported_synergy"
    assert summary["attribute_review"]["planted_null_grade"] != "supported_synergy"
    retained = {k: v for k, v in summary.items() if k != "elapsed_seconds"}
    retained["elapsed_seconds_observed"] = summary["elapsed_seconds"]
    (ROOT / "evidence" / "program-demo-summary.json").write_text(
        json.dumps(retained, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    shutil.copyfile(out / "impact" / "impact-assessment.html", ROOT / "web" / "impact-assessment-example.html")
    print(f"Retained program evidence: {summary['impact']['matched']} matched parties, "
          f"{summary['attribute_review']['pairs_screened']} pairs screened")


if __name__ == "__main__":
    main()
