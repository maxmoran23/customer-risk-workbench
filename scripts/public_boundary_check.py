"""Check the explicit public-release allowlist for accidental private material."""

from __future__ import annotations

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
    "institution-specific term": re.compile("morgan" + r"\s+stanley|\becrr\b", re.I),
    "private local path": re.compile(r"/Users/[^/\s]+|C:\\Users\\[^\\\s]+"),
    "private key": re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"),
    "credential pattern": re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9]{30,}|AKIA[A-Z0-9]{16}"),
    "email address": re.compile(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
}


def candidates():
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if not path.is_file() or any(part in EXCLUDED for part in relative.parts) or path.name in IGNORED:
            continue
        if path.suffix in {".pyc", ".sqlite", ".db", ".png", ".pdf", ".zip", ".whl"}:
            continue
        yield path


def check():
    findings = []
    count = 0
    for path in candidates():
        if path.is_symlink():
            findings.append(
                {"path": str(path.relative_to(ROOT)), "issue": "symlink requires explicit review"}
            )
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append({"path": str(path.relative_to(ROOT)), "issue": "unexpected binary file"})
            continue
        count += 1
        if path.name == "public_boundary_check.py":
            continue
        for name, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append({"path": str(path.relative_to(ROOT)), "issue": name})
    return {
        "files_scanned": count,
        "findings": findings,
        "limit": "Pattern scan complements human review; it cannot establish absence of confidential content or detect every secret.",
    }


if __name__ == "__main__":
    import json

    result = check()
    print(json.dumps(result, indent=2))
    sys.exit(bool(result["findings"]))
