"""Bind public release files to SHA-256 without including local run data."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = (
    ".github",
    "src",
    "configs",
    "scenarios",
    "tests",
    "docs",
    "templates",
    "evidence",
    "web",
    "examples",
    "review-pack",
    "scripts",
)
FILES = (
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "README.md",
    "SECURITY.md",
    "pyproject.toml",
    "uv.lock",
)
TARGET = ROOT / "evidence/source-manifest.json"


def manifest():
    paths = [ROOT / name for name in FILES]
    paths.extend(
        path
        for directory in DIRECTORIES
        for path in (ROOT / directory).rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )
    return {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
        if path != TARGET
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    observed = manifest()
    if args.check:
        expected = json.loads(TARGET.read_text(encoding="utf-8"))["files"]
        changed = sorted(
            name for name in expected.keys() | observed.keys() if expected.get(name) != observed.get(name)
        )
        if changed:
            raise SystemExit("Release file mismatch: " + ", ".join(changed))
        print(f"{len(observed)} public file hashes match")
    else:
        TARGET.write_text(
            json.dumps(
                {
                    "algorithm": "SHA-256",
                    "scope": "Explicit public files; excludes this manifest, local runs, dependencies and Git internals",
                    "files": observed,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(f"Wrote {len(observed)} public file hashes")


if __name__ == "__main__":
    main()
