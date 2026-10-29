"""Compile a small set of self-contained, public-only review attachments."""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PACKS = {
    "01-start-here.md": ["README.md", "docs/reviewer-guide.md", "docs/limitations.md"],
    "02-data-and-implementation.md": [
        "docs/architecture.md",
        "docs/data-contract.md",
        "docs/example-walkthrough.md",
        "templates/data-adapter-review.md",
    ],
    "03-scoring-and-scenarios.md": [
        "docs/scoring-method.md",
        "docs/scenario-design.md",
        "docs/typology-atlas.md",
        "templates/scenario-workpaper.md",
    ],
    "04-development-and-statistics.md": [
        "docs/model-development.md",
        "docs/statistical-methods.md",
        "templates/development-experiment.md",
        "templates/model-card.md",
    ],
    "05-validation-and-sampling.md": [
        "docs/model-validation.md",
        "templates/validation-workpaper.md",
        "templates/sampling-plan.md",
        "templates/findings-and-issues.md",
    ],
    "06-governance-and-regulation.md": [
        "docs/regulatory-map.md",
        "docs/governance.md",
        "templates/component-classification.md",
        "templates/policy-change-review.md",
        "templates/decision-exception.md",
    ],
    "07-adoption-and-ai-assistance.md": [
        "docs/adoption-guide.md",
        "docs/ai-assistance.md",
        "docs/operations.md",
        "templates/adoption-decision.md",
        "templates/monitoring-and-incident.md",
    ],
    "08-evidence-and-reproduction.md": [
        "docs/verification.md",
        "docs/provenance.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
    ],
    "09-attribute-review-program.md": [
        "docs/program-sequencing.md",
        "docs/attribute-review-playbook.md",
        "docs/connections-method.md",
        "docs/rule-design.md",
        "templates/attribute-review-sheet.md",
        "templates/connections-review.md",
        "templates/rule-specification.md",
        "templates/value-reclassification-request.md",
    ],
    "10-impact-assessment-program.md": [
        "docs/impact-assessment-playbook.md",
        "docs/impact-automation-architecture.md",
        "docs/ai-workflows.md",
        "templates/change-manifest.md",
        "templates/impact-assessment-report.md",
        "templates/parity-test-plan.md",
        "prompts/README.md",
    ],
}


def portable_links(content: str, source: str) -> str:
    """Keep copied document links usable when attachments leave the checkout."""

    def replace(match):
        target = match.group(2)
        if ":" in target or target.startswith("#"):
            return match.group(0)
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(source), target))
        route = "tree" if (ROOT / resolved.split("#")[0]).is_dir() else "blob"
        return f"[{match.group(1)}](https://github.com/maxmoran23/customer-risk-workbench/{route}/main/{resolved})"

    return re.sub(r"\[([^\]]+)\]\(([^\s)]+)\)", replace, content)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="dist/review-pack")
    args = p.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"format": "public review attachments", "source_files": {}, "packs": {}}
    for name, files in PACKS.items():
        sections = [
            "# Customer Risk Workbench / " + name.removesuffix(".md").replace("-", " "),
            "Public reference material. Synthetic examples and illustrative policies. No institutional approval or production-performance claim.",
            "Source repository: https://github.com/maxmoran23/customer-risk-workbench\n\nAttachment groups preserve full methods; source code and runnable tests remain in the repository.",
        ]
        for file in files:
            content = (ROOT / file).read_text(encoding="utf-8")
            manifest["source_files"][file] = hashlib.sha256(content.encode()).hexdigest()
            sections.extend(["\n---\n\nSource: `" + file + "`\n", portable_links(content, file)])
        text = "\n\n".join(sections).rstrip() + "\n"
        (out / name).write_text(text, encoding="utf-8", newline="\n")
        manifest["packs"][name] = {
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
            "bytes": len(text.encode()),
            "sources": files,
        }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"Built {len(PACKS)} complete review attachments at {out}")


if __name__ == "__main__":
    main()
