# Changelog

## 0.2.0 (2026-10-29)

Adds two program kits on top of the 0.1.0 core. Nothing in 0.1.0 was removed; its public interfaces, evidence and documents are unchanged except where noted below.

**Categorical rating rebuild:** `crw.attributes` (value catalog, evidence register, normalization audit, review workbook and validated import, population scoping), `crw.connections` (association and interaction screen with false-discovery control, proxy flag, leg-contribution test), `crw.rules` (categorical model, atomic and compound three-valued rules, simulation), `crw.program` (seven stage gates).

**Change-impact assessment:** `crw.impact` (partitioned streaming join, migration matrices, pinned-party integrity, aggregate-only segments, manifest reconciliation, historical comparison, parity, hash-chained register), `crw.impact_sql` (set-based SQL with scope tables), `crw.impact_report` (fixed-layout Markdown, CSV and HTML), `crw.narrative` (facts pack and numeric grounding guard).

**Supporting material:** `crw attributes ...`, `crw impact ...` and `crw program-demo` commands; reference configurations in `configs/programs`; hand-checkable fixtures in `examples/programs`; playbooks, method notes and workpaper templates; a vendor-neutral prompt pack in `prompts/`; review-pack groups 09 and 10; retained synthetic evidence in `evidence/program-demo-summary.json` and `web/impact-assessment-example.html`.

**Changed:** `scripts/public_boundary_check.py` no longer embeds organization-specific terms. Generic patterns remain public; organization-specific terms are supplied privately through `--private-terms` or `CRW_PRIVATE_TERMS`. Continuous integration now also checks generated program configurations and examples, runs the boundary scan and runs the program demonstration.

## 0.1.0 (2026-10-28)

First public research release: contracts, temporal features, explainable policy index, compound hypotheses, executable case library, supervised challengers, statistical validation, monitoring, SQLite operations reference, offline workbench, governance templates and review packs.

## Retrieval of earlier states

Every release state remains retrievable from version control. The 0.1.0 tree is tagged `wave1-baseline`:

```bash
git show wave1-baseline:README.md
git diff wave1-baseline -- docs/
git checkout wave1-baseline -- path/to/file
```

Material is retired by moving it, never by deleting history: superseded documents are removed from the current tree only when an equivalent or better source exists, and the tag above preserves the prior text.
