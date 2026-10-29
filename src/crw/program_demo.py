"""End-to-end synthetic run of both programs: attribute review and change-impact assessment."""

from __future__ import annotations

import csv
from pathlib import Path
import sqlite3
import time

from .attributes import Catalog, audit_normalization, export_workbook, review_coverage, review_diff, scope_population
from .connections import attribute_associations, evaluate_combination, value_pair_screen
from .impact import (TierScale, append_register, assess_change, baseline_outliers, matrix_long_rows,
                     reconcile_expectations, reconcile_matrices, verify_register)
from .impact_report import render_csv, render_html, render_markdown
from .impact_sql import migration_sql
from .io import atomic_json
from .narrative import check_narrative, facts_pack, prompt_text
from .program import program_status
from .program_reference import (AGGREGATE_SEGMENT, reference_assessment_config, reference_catalog, reference_model,
                                reference_party_roles, reference_rules, reference_tier_scale)
from .rules import CategoricalModel, RuleSet, simulate_rules
from .synthetic_program import (aggregate_counts, change_snapshots, generate_parties, history_catalogs,
                                normalization_rows, role_rows)


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def preview_change(parties: list[dict], model: CategoricalModel, rules: RuleSet | None) -> dict:
    """Pre-deployment estimate: current versus proposed classification on a design-time population."""
    cells: dict[tuple, int] = {}
    for p in parties:
        if p.get("pinned"):
            continue
        before = model.assess(p, rules, "current")["tier"]
        after = model.assess(p, rules, "proposed")["tier"]
        if before != after:
            cells[(before, after)] = cells.get((before, after), 0) + 1
    return {"moved_cells": [{"from": a, "to": b, "count": n} for (a, b), n in sorted(cells.items())],
            "moved": sum(cells.values()), "parties": len(parties)}


def manifest_from_preview(preview: dict, scale: TierScale, change_id: str, band: float = 0.25,
                          population: int | None = None, aggregate: dict | None = None) -> dict:
    """Declare expected movement by destination and direction, bounded around the preview estimate."""
    grouped: dict[tuple, int] = {}
    for cell in preview["moved_cells"]:
        direction = "up" if scale.index[cell["to"]] > scale.index[cell["from"]] else "down"
        grouped[(cell["to"], direction)] = grouped.get((cell["to"], direction), 0) + cell["count"]
    effects = []
    scale_factor = population / preview["parties"] if population else 1.0
    for (to, direction), raw in sorted(grouped.items()):
        n = round(raw * scale_factor)
        # Relative band widened by a Poisson-style allowance so small forecast counts are not overconfident.
        slack = max(band * n, 3 * n ** 0.5 + 3)
        effects.append({
            "id": f"EXP-{direction.upper()}-TO-{to}",
            "segments": ["*"],
            "from": ["*"],
            "to": [to],
            "direction": direction,
            "count": {"min": max(0, int(n - slack)), "max": int(n + slack) + 1},
            "rationale": (f"Pre-deployment preview on a separate design-time sample estimated {raw} of "
                          f"{preview['parties']} parties moving {direction} to {to}; scaled to the assessed population."),
        })
    return {
        "change_id": change_id,
        "release": "synthetic-release",
        "description": "Apply proposed value classifications from the attribute review (synthetic).",
        "change_type": "value_classification",
        "expected_effects": effects,
        "unexplained_tolerance": {"min_count": 1, "min_share": 0.0},
        "expected_population": {
            "entrants": {"min": 0, "max": max(1, round(0.01 * (population or preview["parties"])))},
            "exits": {"min": 0, "max": max(1, round(0.01 * (population or preview["parties"])))},
            "rationale": "Ordinary onboarding and closure between snapshots; this change does not alter population membership.",
        },
        "expected_aggregate": aggregate or {},
    }


def _sql_parity(directory: Path, pre_rows, post_rows, assessment) -> dict:
    db = directory / "impact-parity.sqlite"
    if db.exists():
        db.unlink()
    con = sqlite3.connect(db)
    try:
        for table, rows in (("snap_pre", pre_rows), ("snap_post", post_rows)):
            con.execute(f"CREATE TABLE {table} (party_id TEXT PRIMARY KEY, segment TEXT, tier TEXT, pinned INTEGER)")
            con.executemany(f"INSERT INTO {table} VALUES (?,?,?,?)",
                            [(r["party_id"], r["segment"], r["tier"], int(r["pinned"])) for r in rows])
        statements = migration_sql("snap_pre", "snap_post")
        violations = [row for row in con.execute(statements["checks"]) if row[2]]
        if violations:
            raise ValueError(f"snapshot contract violations in SQL checks: {violations}")
        matched = con.execute(statements["matched"]).fetchall()
    finally:
        con.close()
    db.unlink()
    sql_cells = {(s, a, b): n for s, a, b, n in matched}
    engine_cells = {(r["segment"], r["pre_tier"], r["post_tier"]): r["count"]
                    for r in matrix_long_rows(assessment) if r["count"]}
    return {"engine": "sqlite", "cells_compared": len(set(sql_cells) | set(engine_cells)),
            "identical": sql_cells == engine_cells, "statements": statements,
            "standard_rows": [{"segment": s, "pre_tier": a, "post_tier": b, "count": n} for (s, a, b), n in sorted(sql_cells.items())]}


def run_program_demo(out: str | Path, *, parties_n: int = 20000, seed: int = 11, history_n: int = 6000) -> dict:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    catalog = Catalog(reference_catalog())
    model = CategoricalModel(reference_model(), catalog)
    rules = RuleSet(reference_rules(), catalog, model)
    scale = TierScale(reference_tier_scale())
    for name, value in (("catalog", catalog.to_dict()), ("model", model.to_dict()), ("rules", rules.to_dict()),
                        ("party-roles", reference_party_roles()), ("tier-scale", reference_tier_scale())):
        atomic_json(out / "configs" / f"{name}.json", value)

    parties = generate_parties(catalog, parties_n, seed)
    scoping = scope_population(reference_party_roles(), role_rows(parties, seed))
    normalization = normalization_rows(catalog, parties, seed)
    write_csv(out / "attribute-review" / "normalization-table.csv", normalization,
              ["attribute_id", "source_system", "source_value", "value_id", "party_count"])
    audit = audit_normalization(catalog, normalization)
    workbook = export_workbook(catalog, out / "attribute-review" / "workbook", normalization)
    coverage, diff = review_coverage(catalog), review_diff(catalog)
    attributes = [a for a in catalog.attributes if a != "entity_type"] + ["entity_type"]
    associations = attribute_associations([p["values"] for p in parties], attributes)
    rows = [{**p["values"], "outcome": p["outcome"]} for p in parties]
    screen = value_pair_screen(rows, attributes, catalog=catalog)
    combination = evaluate_combination(rows, {
        "entity_type": ["financial_institution_nonbank"],
        "source_of_funds": ["third_party_unrelated", "unverified"],
        "listed_status": ["unlisted_unregulated_structure"],
    })
    simulation = simulate_rules(parties, model, rules)
    status = program_status({"scoping": scoping, "coverage": coverage, "normalization_audit": audit,
                             "connections": screen, "rule_simulation": simulation})
    for name, value in (("scoping", scoping), ("normalization-audit", audit), ("coverage", coverage),
                        ("review-diff", diff), ("associations", associations), ("pair-screen", screen),
                        ("combination-COMP-01", combination), ("rule-simulation", simulation),
                        ("program-status", status)):
        atomic_json(out / "attribute-review" / f"{name}.json", value)

    impact_dir = out / "impact"
    # The preview uses a separately drawn design-time sample, not the assessed population, so the manifest is a
    # genuine forecast rather than a restatement of the result.
    preview = preview_change(generate_parties(catalog, parties_n, seed + 200, id_prefix="DES"), model, rules)
    aggregate_movement = {AGGREGATE_SEGMENT: {
        "minimum_movers": {"min": 0, "max": 2500},
        "rationale": "Aggregate-only segment: the change is expected to move under 1% of its 250,000 parties; only a lower bound is observable.",
    }}
    manifest = manifest_from_preview(preview, scale, "CHG-DEMO-001", population=parties_n, aggregate=aggregate_movement)
    pre_rows, post_rows = change_snapshots(parties, model, model, rules, seed)
    fields = ["party_id", "segment", "tier", "pinned"]
    write_csv(impact_dir / "snapshot-pre.csv", pre_rows, fields)
    write_csv(impact_dir / "snapshot-post.csv", post_rows, fields)
    config = reference_assessment_config()
    config["aggregates"] = {AGGREGATE_SEGMENT: aggregate_counts(250000, seed, 0.004)}
    assessment = assess_change(impact_dir / "snapshot-pre.csv", impact_dir / "snapshot-post.csv", config, scale)
    expectations = reconcile_expectations(assessment, manifest)

    history = []
    sample = generate_parties(catalog, history_n, seed + 100)
    for i, past in enumerate(history_catalogs(catalog, 8, seed)):
        past_model = CategoricalModel(reference_model(), past)
        past_rules = RuleSet(reference_rules(), past, past_model)
        pre_h, post_h = change_snapshots(sample, past_model, past_model, past_rules, seed + i)
        history_config = reference_assessment_config(f"IA-HIST-{i + 1:03d}")
        history.append(assess_change(pre_h, post_h, history_config, scale, partitions=1))
    baseline = baseline_outliers(history, assessment)
    sql_parity = _sql_parity(impact_dir, pre_rows, post_rows, assessment)
    # The independent "standard" here is the set-based SQL path executed by SQLite, not the engine's own output.
    parity = reconcile_matrices(assessment, sql_parity.pop("standard_rows"))

    pack = facts_pack(assessment, expectations=expectations, baseline=baseline, parity=parity)
    facts = pack["facts"]
    draft = (
        f"Impact assessment {facts['assessment_id']} compared {facts['total.matched']:,} matched parties. "
        f"{facts['total.moved']:,} parties changed tier ({facts['total.moved_share_pct']}%): {facts['total.up']:,} up and "
        f"{facts['total.down']:,} down. {facts['total.excluded_pinned']:,} pinned parties were excluded. "
        f"Expectation reconciliation verdict: {facts['expectations.verdict']}. "
        f"Parity with the standard process: {facts['parity.verdict']}."
    )
    narrative_check = check_narrative(draft, pack, required=["total.moved", "total.matched"])
    register = impact_dir / "assessment-register.jsonl"
    if register.exists():
        register.unlink()
    append_register(register, {"assessment_id": assessment["assessment_id"], "assessment_hash": assessment["assessment_hash"],
                               "recorded_at": "2026-10-29T00:00:00Z",
                               "verdicts": {"expectations": expectations["verdict"], "parity": parity["verdict"]}})
    register_status = verify_register(register)

    annexes = {"manifest": manifest, "expectations": expectations, "baseline": baseline, "parity": parity}
    (impact_dir / "impact-assessment.md").write_text(render_markdown(assessment, **annexes), encoding="utf-8", newline="\n")
    (impact_dir / "impact-assessment.html").write_text(render_html(assessment, **annexes), encoding="utf-8", newline="\n")
    (impact_dir / "impact-matrix-long.csv").write_text(render_csv(assessment), encoding="utf-8", newline="\n")
    (impact_dir / "narrative-prompt.txt").write_text(prompt_text(pack), encoding="utf-8", newline="\n")
    (impact_dir / "narrative-reference-draft.txt").write_text(draft + "\n", encoding="utf-8", newline="\n")
    for name, value in (("assessment", assessment), ("change-manifest", manifest), ("preview", preview),
                        ("expectations", expectations), ("baseline", baseline), ("parity", parity),
                        ("sql-parity", sql_parity), ("facts-pack", pack), ("narrative-check", narrative_check)):
        atomic_json(impact_dir / f"{name}.json", value)

    planted = next((c for c in screen["candidates"] if {c["a"]["value"], c["b"]["value"]} ==
                    {"financial_institution_nonbank", "third_party_unrelated"}), None)
    null_pair = next((c for c in screen["candidates"] if {c["a"]["value"], c["b"]["value"]} ==
                      {"trust", "inheritance_or_gift"}), None)
    summary = {
        "data_status": "synthetic",
        "seed": seed,
        "parties": parties_n,
        "attribute_review": {
            "attributes": len(catalog.attributes),
            "values": coverage["totals"]["values"],
            "classified_share": coverage["totals"]["classified_share"],
            "reviewed_share": coverage["totals"]["reviewed_share"],
            "proposed_changes": diff["counts"],
            "normalization_status": audit["status"],
            "normalization_issue_counts": audit["issue_counts"],
            "rated_population": scoping["rated_population"],
            "scope_counts": scoping["scope_counts"],
            "pairs_screened": screen["pairs_screened"],
            "hypotheses_tested": screen["hypotheses_tested"],
            "grade_counts": screen["grade_counts"],
            "planted_synergy_grade": planted and planted["grade"],
            "planted_null_grade": null_pair and null_pair.get("grade"),
            "rules": {r["rule_id"]: {k: r.get(k) for k in ("true", "unknown", "marginal_tier_changes")}
                      for r in simulation["rules"]},
            "program_stages": {s["stage"]: s["status"] for s in status["stages"]},
            "workbook_files": len(workbook["files"]),
        },
        "impact": {
            "matched": assessment["totals"]["matched"],
            "moved": assessment["totals"]["moved"],
            "up": assessment["totals"]["up"],
            "down": assessment["totals"]["down"],
            "excluded_pinned": assessment["totals"]["excluded_pinned"],
            "integrity_findings": assessment["integrity_findings"],
            "preview_moved": preview["moved"],
            "expectations_verdict": expectations["verdict"],
            "baseline_flags": len(baseline["flags"]),
            "history_assessments": len(history),
            "parity_verdict": parity["verdict"],
            "sql_parity_identical": sql_parity["identical"],
            "narrative_check": narrative_check["status"],
            "register": register_status["status"],
        },
        "elapsed_seconds": round(time.perf_counter() - started, 2),
    }
    atomic_json(out / "summary.json", summary)
    return summary
