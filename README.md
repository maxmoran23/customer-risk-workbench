# Customer Risk Workbench

**An executable, public reference suite for customer risk assessment, model research, and technical challenge.** Start with normalized customer and transaction records; reconstruct retained evidence available at an assessment cutoff; inspect a configurable risk index; test scenarios, alternative models, uncertainty, and operational behavior.

This is original open-source research software by Max Moran, developed with AI assistance. All bundled customers, transactions, labels, and operating policies are synthetic or illustrative. It has not undergone institutional independent validation and does not claim real-world detection effectiveness, regulatory approval, or production readiness.

## Start here

| Reader | First stop | What to inspect next |
| --- | --- | --- |
| Review the working product | Download the repository and open [`web/workbench.html`](web/workbench.html) in a browser | Customer review, executable cases, model research, sensitivity lab |
| Understand the method | [Scoring method](docs/scoring-method.md) and [reviewer guide](docs/reviewer-guide.md) | [Data contract](docs/data-contract.md), [development protocol](docs/model-development.md) |
| Run a small transparent example | [Three-customer walkthrough](docs/example-walkthrough.md) | Hand-reconciled contributions, required-evidence removal, replay and monitoring |
| Challenge the mathematics | [Statistical methods and APIs](docs/statistical-methods.md) | [Tests](tests), [research evidence](evidence/research.json), [verification](docs/verification.md) |
| Evaluate adaptation | [Adoption guide](docs/adoption-guide.md) | [Worked templates](templates), [AI-assisted adaptation](docs/ai-assistance.md) |
| Transfer a compact reading pack | [Eight attachment groups](review-pack) | Full source remains organized by responsibility below |

The HTML runs offline: no login, installation, external fonts, telemetry, AI API, or hosted service is required. It contains selected synthetic examples and retained research evidence. GitHub displays HTML source; download/open the file to use the interface.

## What is implemented

| Capability | Working implementation | Evidence / boundary |
| --- | --- | --- |
| Canonical input and lineage | Strict JSONL/CSV adapters, UTC event/availability times, normalized units, content hashes | Invalid, missing, duplicate, late, and conflicting records tested |
| Temporal features | 160 reference features across 11 windows: 1/7/30/90/180/365 days, observed lifetime, last 4/10/25/50 events | [Generated feature catalog](configs/features.json); retained history and denominators explicit |
| Explainable policy index | 23 illustrative factors across six sum/max groups; configurable normalization, weights, caps and bands | Missing evidence produces bounds and can force review; index is not a probability |
| Compound hypotheses | 20 declarative patterns with TRUE/FALSE/UNKNOWN logic | Benign alternatives and next evidence included; matches add no hidden points |
| Executable case library | 96 named cases with expected and observed behavior | [Case catalog](scenarios/catalog.json); arithmetic, temporal edges, missingness, counterexamples and invariants |
| Supervised challengers | Prevalence baseline, standardized logistic regression, monotonic histogram gradient boosting | Training-only preprocessing, matured labels, temporal and customer separation |
| Robustness experiments | Three seeds across four refitted regimes; separate fixed-model perturbations | Frozen parameters and thresholds, paired records, probability/label/workload changes |
| Statistical validation | Tied AUC/AP, Brier/log loss, calibration, intervals, sampling, paired bootstrap, segment support | Undefined metrics explicit; synthetic labels generated independently of policy scores |
| Monitoring and attribution | PSI/KS/effect diagnostics, matched-ID migrations, entrants/exits, score availability, crossed data/policy decomposition | No universal drift cutoff; arithmetic attribution is not causality |
| Operational reference | Real SQLite, atomic ingest, immutable content IDs, snapshot reads, complete-run export, append-only review records | Local single-writer implementation; authentication and production operations remain adopter work |
| Review interface | Eight offline views with explanations, search, comparisons and evidence export | Selected examples labeled; complete portfolio statistics separate |
| Governance and adoption | Current-source regulatory map, worked model/validation/adapter/decision templates, compact review packs | No fabricated sign-off or employer-specific content |

The current verification record, exact test counts, measured timings, source hashes and limitations are in [the evidence dossier](docs/verification.md). The case count is not a count of independently validated financial-crime typologies.

## Run it

Python 3.11 or later supports the core. Python 3.12 is the pinned reference research environment. From a downloaded or cloned checkout:

```bash
python -m pip install '.[dev,research]'
python -m pytest
python -m crw demo --customers 1000 --transactions 80 --research --out runs/my-demo
```

Open `runs/my-demo/workbench.html`. The command generates 1,000 synthetic customers and 80,000 transactions, ingests a real SQLite database, scores twice with different chunk sizes, executes the case library, runs research experiments, and writes the standalone interface. Use a fresh output directory when changing seed or population parameters; existing event identifiers reject conflicting content.

For a dependency-locked environment with [uv](https://docs.astral.sh/uv/):

```bash
uv sync --frozen --all-extras --python 3.12
uv run python -m pytest
uv run crw demo --research --out runs/locked-demo
```

For a core-only install, use `python -m pip install .` and omit `--research`. Core scoring, SQLite, scenarios, monitoring and HTML rendering require no third-party runtime libraries. Research uses the optional numerical dependencies. Shell-specific virtual-environment activation is not required when using these commands through the chosen Python environment; follow local software installation policy.

## Inspect a pipeline step

```bash
python -m crw generate --customers 1000 --transactions 80 --out runs/input
python -m crw ingest --db runs/portfolio.sqlite --customers runs/input/customers.jsonl --transactions runs/input/transactions.jsonl
python -m crw score --db runs/portfolio.sqlite --as-of 2026-10-01T00:00:00Z --out runs/assessments.jsonl
python -m crw scenarios --out runs/scenarios.json
python -m crw research --rows 3000 --seeds 7 19 41 --out runs/research.json
python -m crw benchmark --customers 100000 --transactions 10 --out runs/benchmark.json
```

See [operations](docs/operations.md) for repeatable execution, monitoring and sampling APIs, failure behavior, packaging, and platform limits.

## How to challenge it

Start by removing required evidence from a customer and verify that the final score becomes null. Add a transaction unavailable at the historical cutoff and verify that the calculation does not change. Increase overlapping-window evidence and inspect the max-group cap. Change both data and policy and use the four crossed calculations to attribute the movement. In research, compare the same frozen model before and after feature masking; preserve its failures in the report.

Regression is a useful transparent benchmark. Complexity is justified only when independent evaluation supports a worthwhile improvement. A unique score for every customer is not a goal: different customers may share an index while retaining different evidence and explanations.

## Repository map

```text
src/crw/       Typed contracts, features, policy, patterns, storage, research and diagnostics
configs/       Versioned illustrative policy, schemas, feature and pattern catalogs
examples/      Three-customer fixtures and executable end-to-end walkthrough
scenarios/     Named executable-case catalog and extension guide
tests/         Independent arithmetic, boundary, statistical and real-database tests
docs/          Technical methods, source registry, governance and reviewer routes
templates/     Twelve worked adoption and review workpapers
evidence/      Generated results, benchmarks, verification and source-hash manifest
web/           Standalone offline workbench
review-pack/   Eight complete Markdown attachment groups and source manifest
scripts/       Reproduction, packaging and public-boundary checks
```

## Current guidance and use boundary

The public regulatory map uses the April 2026 interagency model-risk guidance; it identifies SR 11-7 and SR 21-8 as superseded and distinguishes component classification from governance responsibilities. No regulator prescribes this suite's weights, feature count, score bands or example review thresholds. [Current source map](docs/regulatory-map.md), [Federal Reserve SR 26-2](https://www.federalreserve.gov/supervisionreg/srletters/sr2602.htm).

Institution-specific data mapping, risk appetite, outcome definitions, calibration, validation, authorization, and deployment belong in the adopter's approved environment. Public resources should not be interpreted as authorization to import software or data into an institution. The suite does not perform sanctions clearance, determine SAR filing, establish misconduct, or autonomously approve/close relationships.

[MIT license](LICENSE) · [Security](SECURITY.md) · [Provenance](docs/provenance.md) · [Contributing](CONTRIBUTING.md)
