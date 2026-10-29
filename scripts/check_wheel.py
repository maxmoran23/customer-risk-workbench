"""Exercise an installed wheel outside the checkout with no optional dependencies."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import venv

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheel", help="Wheel path; default is the single wheel in dist/ for the current version")
    parser.add_argument("--out", default="evidence/wheel-check.json")
    args = parser.parse_args()
    if args.wheel:
        wheel = Path(args.wheel).resolve()
    else:
        found = sorted((ROOT / "dist").glob("customer_risk_workbench-*-py3-none-any.whl"))
        if len(found) != 1:
            raise SystemExit(f"expected exactly one wheel in dist/, found {len(found)}")
        wheel = found[0]
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    with tempfile.TemporaryDirectory(prefix="crw-wheel-verification-") as folder:
        temporary = Path(folder)
        venv.EnvBuilder(with_pip=True).create(temporary / "environment")
        executable = temporary / "environment" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

        def run(*arguments):
            return subprocess.run(
                [str(executable), *arguments],
                cwd=temporary,
                env=environment,
                capture_output=True,
                text=True,
                check=True,
            ).stdout

        run("-m", "pip", "install", "--no-index", "--no-deps", str(wheel))
        installed = json.loads(
            run(
                "-c",
                'import importlib.metadata,json; print(json.dumps(sorted(d.metadata["Name"] for d in importlib.metadata.distributions())))',
            )
        )
        assert "numpy" not in installed and "scikit-learn" not in installed
        output = json.loads(
            run("-m", "crw", "demo", "--customers", "12", "--transactions", "80", "--out", "demo")
        )
        assert output["replay_identical"] and output["scenarios"] == {"total": 96, "passed": 96, "failed": 0}
        report = json.loads((temporary / "demo/demo-report.json").read_text(encoding="utf-8"))
        html = (temporary / "demo/workbench.html").read_text(encoding="utf-8")
        assert '<script id="workbench-data"' in html and "__REPORT_JSON__" not in html
        program = json.loads(run("-m", "crw", "program-demo", "--parties", "2000", "--out", "program"))
        assert program["impact"]["sql_parity_identical"] and program["impact"]["parity_verdict"] == "EXACT_MATCH"
        assert program["impact"]["narrative_check"] == "grounded"
        result = {
            "status": "passed",
            "wheel": wheel.name,
            "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
            "python": run("-c", "import platform; print(platform.python_version())").strip(),
            "installation": "fresh virtual environment, no-index wheel install, no optional dependencies",
            "execution": "temporary working directory outside source checkout; PYTHONPATH removed",
            "installed_distributions": installed,
            "customers": report["meta"]["customers"],
            "transactions": report["meta"]["transactions"],
            "scenario_results": output["scenarios"],
            "chunk_replay_identical": output["replay_identical"],
            "standalone_html_written": True,
            "program_demo": {"parties": program["parties"], "parity": program["impact"]["parity_verdict"],
                             "sql_parity_identical": program["impact"]["sql_parity_identical"],
                             "narrative_check": program["impact"]["narrative_check"]},
            "limit": "Core package smoke check; browser behavior and optional research dependencies are checked separately.",
        }
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
