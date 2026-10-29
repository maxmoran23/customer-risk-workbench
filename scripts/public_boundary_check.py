"""Check the public-release tree for accidental private material.

Generic patterns (local paths, keys, credentials, e-mail addresses) live here. Organization-specific terms do
not: a public denylist would itself disclose what it protects. Supply them privately, one term or regular
expression per line, through ``--private-terms FILE`` or the ``CRW_PRIVATE_TERMS`` environment variable. Keep
that file outside the published tree (``private/`` is ignored by git and by this scan).
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".hypothesis",
    ".ruff_cache",
    "runs",
    "private",
    "input",
    "dist",
    "build",
}
IGNORED = {"PLAN.md", "HANDOFF.md", ".coverage", "coverage.xml"}
PATTERNS = {
    "private local path": re.compile(r"/Users/[^/\s]+|C:\\Users\\[^\\\s]+|/home/[a-z][^/\s]*"),
    "private key": re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"),
    "credential pattern": re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9]{30,}|AKIA[A-Z0-9]{16}"),
    "email address": re.compile(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
}


def private_patterns(path: str | None) -> list[re.Pattern]:
    if not path:
        return []
    terms = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("re:"):
            terms.append(re.compile(line[3:], re.I))
        else:
            terms.append(re.compile(r"(?<![A-Za-z0-9])" + re.escape(line) + r"(?![A-Za-z0-9])", re.I))
    return terms


def candidates():
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if not path.is_file() or any(part in EXCLUDED for part in relative.parts) or path.name in IGNORED:
            continue
        if path.suffix in {".pyc", ".sqlite", ".db", ".png", ".pdf", ".zip", ".whl"}:
            continue
        yield path


def check(terms_path: str | None = None):
    findings = []
    count = 0
    private = private_patterns(terms_path)
    for path in candidates():
        relative = str(path.relative_to(ROOT))
        if path.is_symlink():
            findings.append({"path": relative, "issue": "symlink requires explicit review"})
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append({"path": relative, "issue": "unexpected binary file"})
            continue
        count += 1
        for name, pattern in PATTERNS.items():
            if path.name != "public_boundary_check.py" and pattern.search(text):
                findings.append({"path": relative, "issue": name})
        for index, pattern in enumerate(private):
            if pattern.search(text):
                findings.append({"path": relative, "issue": f"private term #{index + 1}"})
    return {
        "files_scanned": count,
        "private_terms_checked": len(private),
        "findings": findings,
        "limit": "Pattern scan complements human review; it cannot establish absence of confidential content or detect every secret.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-terms", default=os.environ.get("CRW_PRIVATE_TERMS"))
    args = parser.parse_args()
    result = check(args.private_terms)
    print(json.dumps(result, indent=2))
    sys.exit(bool(result["findings"]))
