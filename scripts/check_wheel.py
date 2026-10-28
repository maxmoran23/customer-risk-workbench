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
    parser.add_argument("--wheel", default="dist/customer_risk_workbench-0.1.0-py3-none-any.whl")
    parser.add_argument("--out", default="evidence/wheel-check.json")
    args = parser.parse_args()
    wheel = Path(args.wheel).resolve()
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
        report = json.loads((temporary / "demo/demo-report.json").read_text())
        html = (temporary / "demo/workbench.html").read_text()
        assert '<script id="workbench-data"' in html and "__REPORT_JSON__" not in html
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
            "limit": "Core package smoke check; browser behavior and optional research dependencies are checked separately.",
        }
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
