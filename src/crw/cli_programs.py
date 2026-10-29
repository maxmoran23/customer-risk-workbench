"""Command line for the attribute-review and impact-assessment programs (``crw attributes``, ``crw impact``)."""

from __future__ import annotations

import json
from pathlib import Path

from .attributes import (Catalog, audit_normalization, export_workbook, import_inventory, read_csv_rows,
                         review_coverage, review_diff, scope_population)
from .connections import attribute_associations, evaluate_combination, value_pair_screen
from .contracts import ContractError
from .impact import (TierScale, append_register, assess_change, baseline_outliers, reconcile_expectations,
                     reconcile_matrices, verify_register)
from .impact_report import render_csv, render_html, render_markdown
from .impact_sql import migration_sql
from .io import atomic_json
from .narrative import check_narrative, facts_pack, prompt_text
from .program import program_status
from .program_reference import (reference_assessment_config, reference_catalog, reference_model,
                                reference_party_roles, reference_rules, reference_tier_scale)
from .rules import CategoricalModel, RuleSet, simulate_rules


def _json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _jsonl(path):
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def _catalog(args):
    return Catalog.load(args.catalog) if args.catalog else Catalog(reference_catalog())


def _model(args, catalog):
    return CategoricalModel.load(args.model, catalog) if args.model else CategoricalModel(reference_model(), catalog)


def _rules(args, catalog, model):
    return RuleSet.load(args.rules, catalog, model) if args.rules else RuleSet(reference_rules(), catalog, model)


def _scale(args):
    return TierScale(_json(args.scale) if args.scale else reference_tier_scale())


def a_validate(args):
    catalog = _catalog(args)
    coverage = review_coverage(catalog)
    if args.out:
        atomic_json(args.out, coverage)
        atomic_json(Path(args.out).with_name(Path(args.out).stem + "-diff.json"), review_diff(catalog))
    return {"catalog_digest": catalog.digest, "coverage": coverage["totals"],
            "proposed_changes": review_diff(catalog)["counts"], "out": args.out}


def a_audit(args):
    result = audit_normalization(_catalog(args), read_csv_rows(args.table), args.similarity)
    atomic_json(args.out, result)
    return {"out": args.out, "status": result["status"], "issue_counts": result["issue_counts"]}


def a_workbook(args):
    rows = read_csv_rows(args.normalization) if args.normalization else None
    return export_workbook(_catalog(args), args.out, rows)


def a_import(args):
    catalog = _catalog(args)
    paths = sorted(Path(args.inventory).glob("*-inventory.csv")) if Path(args.inventory).is_dir() else [Path(args.inventory)]
    paths = [p for p in paths if p.name != "all-values-inventory.csv"] or paths
    rows = [row for p in paths for row in read_csv_rows(p)]
    updated, log = import_inventory(catalog, rows)
    atomic_json(args.out, updated.to_dict())
    atomic_json(Path(args.out).with_suffix(".changes.json"), log)
    return {"out": args.out, "changed_values": len(log), "catalog_digest": updated.digest}


def a_connections(args):
    catalog = _catalog(args)
    parties = _jsonl(args.parties)
    attributes = args.attributes or list(catalog.attributes)
    rows = [{**p["values"], "outcome": p.get("outcome")} for p in parties]
    result = {
        "associations": attribute_associations([p["values"] for p in parties], attributes),
        "pairs": value_pair_screen(rows, attributes, min_support=args.min_support, min_events=args.min_events,
                                   alpha=args.alpha, catalog=catalog),
    }
    if args.combination:
        result["combination"] = evaluate_combination(rows, _json(args.combination))
    atomic_json(args.out, result)
    return {"out": args.out, "outcome_status": result["pairs"]["outcome_status"],
            "grade_counts": result["pairs"]["grade_counts"]}


def a_rules(args):
    catalog = _catalog(args)
    model = _model(args, catalog)
    result = simulate_rules(_jsonl(args.parties), model, _rules(args, catalog, model), args.stage)
    atomic_json(args.out, result)
    return {"out": args.out, "with_rules": result["tier_distribution_with_rules"],
            "without_rules": result["tier_distribution_without_rules"]}


def a_scope(args):
    config = _json(args.config) if args.config else reference_party_roles()
    result = scope_population(config, read_csv_rows(args.roles))
    atomic_json(args.out, result)
    return {"out": args.out, "rated_population": result["rated_population"], "scope_counts": result["scope_counts"]}


def a_status(args):
    artifacts = {}
    for key in ("scoping", "coverage", "normalization_audit", "connections", "rule_simulation"):
        path = getattr(args, key)
        if path:
            value = _json(path)
            artifacts[key] = value["pairs"] if key == "connections" and "pairs" in value else value
    artifacts["calibration_reference"] = args.calibration_reference
    artifacts["validation_reference"] = args.validation_reference
    return program_status(artifacts, _json(args.criteria) if args.criteria else None)


def i_assess(args):
    scale = _scale(args)
    config = _json(args.config) if args.config else reference_assessment_config()
    assessment = assess_change(args.pre, args.post, config, scale, partitions=args.partitions)
    annexes = {}
    if args.manifest:
        annexes["manifest"] = _json(args.manifest)
        annexes["expectations"] = reconcile_expectations(assessment, annexes["manifest"])
    if args.history:
        annexes["baseline"] = baseline_outliers([_json(p) for p in args.history], assessment,
                                                min_history=args.min_history, z_threshold=args.z_threshold)
    if args.standard:
        annexes["parity"] = reconcile_matrices(assessment, read_csv_rows(args.standard),
                                               tolerance_abs=args.tolerance_abs, tolerance_rel=args.tolerance_rel)
    if args.register and not args.recorded_at:
        raise ContractError("--register requires --recorded-at (UTC timestamp of the assessment record)")
    out = Path(args.out)
    atomic_json(out / "assessment.json", assessment)
    for key, value in annexes.items():
        atomic_json(out / f"{key}.json", value)
    (out / "impact-assessment.md").write_text(render_markdown(assessment, **annexes), encoding="utf-8", newline="\n")
    (out / "impact-assessment.html").write_text(render_html(assessment, **annexes), encoding="utf-8", newline="\n")
    (out / "impact-matrix-long.csv").write_text(render_csv(assessment), encoding="utf-8", newline="\n")
    pack = facts_pack(assessment, expectations=annexes.get("expectations"), baseline=annexes.get("baseline"),
                      parity=annexes.get("parity"))
    atomic_json(out / "facts-pack.json", pack)
    (out / "narrative-prompt.txt").write_text(prompt_text(pack), encoding="utf-8", newline="\n")
    if args.register:
        append_register(args.register, {
            "assessment_id": assessment["assessment_id"], "assessment_hash": assessment["assessment_hash"],
            "recorded_at": args.recorded_at,
            "verdicts": {k: annexes[k]["verdict"] for k in ("expectations", "parity") if k in annexes}})
    result = {"out": str(out), "matched": assessment["totals"]["matched"], "moved": assessment["totals"]["moved"],
              "integrity_findings": assessment["integrity_findings"],
              "verdicts": {k: v.get("verdict") for k, v in annexes.items() if isinstance(v, dict) and "verdict" in v}}
    failing = [k for k, v in result["verdicts"].items() if v in {"requires_explanation", "MISMATCH"}]
    if args.strict and (failing or assessment["integrity_findings"]):
        print(json.dumps(result, indent=2, sort_keys=True))
        raise ContractError(f"strict mode: verdicts requiring attention {failing}, integrity {assessment['integrity_findings']}")
    return result


def i_sql(args):
    statements = migration_sql(args.pre_table, args.post_table, id_col=args.id_col, segment_col=args.segment_col,
                               tier_col=args.tier_col, pinned_col=args.pinned_col or None,
                               scope_table=args.scope_table, exclude_pinned=not args.include_pinned)
    text = "\n\n".join(f"-- {name}\n{sql};" for name, sql in statements.items() if name != "notes")
    text += "\n\n" + "\n".join(f"-- {note}" for note in statements["notes"]) + "\n"
    Path(args.out).write_text(text, encoding="utf-8", newline="\n")
    return {"out": args.out, "statements": [k for k in statements if k != "notes"]}


def i_narrative(args):
    pack = _json(args.facts)
    result = check_narrative(Path(args.draft).read_text(encoding="utf-8"), pack, required=args.require)
    if result["status"] != "grounded":
        if args.out:
            atomic_json(args.out, result)
        raise ContractError(f"narrative rejected: {len(result['unsupported_numbers'])} unsupported number(s), "
                            f"missing {result['missing_required_facts']}")
    return result


def i_register(args):
    result = verify_register(args.register, _json(args.anchor) if args.anchor else None)
    if result["status"] != "intact":
        raise ContractError(f"register broken: {result['problems']}")
    return result


def program_demo(args):
    from .program_demo import run_program_demo

    return run_program_demo(args.out, parties_n=args.parties, seed=args.seed)


def register(subs) -> None:
    attrs = subs.add_parser("attributes", help="Attribute review: catalog, normalization, workbooks, connections, rules")
    a = attrs.add_subparsers(dest="attributes_command", required=True)

    def common(p, catalog=True):
        if catalog:
            p.add_argument("--catalog", help="Catalog JSON (default: illustrative reference catalog)")
        return p

    p = common(a.add_parser("validate", help="Validate a catalog and summarize review state"))
    p.add_argument("--out", help="Write the full coverage report (input to `attributes status --coverage`) and a diff")
    p.set_defaults(func=a_validate)
    p = common(a.add_parser("audit", help="Audit a source-to-normalized mapping table (CSV)"))
    p.add_argument("--table", required=True)
    p.add_argument("--similarity", type=float, default=0.8)
    p.add_argument("--out", default="runs/normalization-audit.json")
    p.set_defaults(func=a_audit)
    p = common(a.add_parser("workbook", help="Write per-attribute review sheets and CSV inventories"))
    p.add_argument("--normalization", help="Optional mapping table CSV to show source values and counts")
    p.add_argument("--out", default="runs/attribute-workbook")
    p.set_defaults(func=a_workbook)
    p = common(a.add_parser("import", help="Validate reviewer edits from CSV inventories into a new catalog"))
    p.add_argument("--inventory", required=True, help="Inventory CSV or workbook directory")
    p.add_argument("--out", required=True)
    p.set_defaults(func=a_import)
    p = common(a.add_parser("connections", help="Cross-attribute association and synergy screen"))
    p.add_argument("--parties", required=True, help="Parties JSONL (party_id, entity_type, values, outcome)")
    p.add_argument("--attributes", nargs="*")
    p.add_argument("--min-support", type=int, default=30)
    p.add_argument("--min-events", type=int, default=5)
    p.add_argument("--alpha", type=float, default=0.05)
    p.add_argument("--combination", help="JSON object of attribute -> allowed values to test leg contribution")
    p.add_argument("--out", default="runs/connections.json")
    p.set_defaults(func=a_connections)
    p = common(a.add_parser("rules", help="Simulate atomic and compound rules on a population"))
    p.add_argument("--model")
    p.add_argument("--rules")
    p.add_argument("--parties", required=True)
    p.add_argument("--stage", choices=["current", "proposed"], default="proposed")
    p.add_argument("--out", default="runs/rule-simulation.json")
    p.set_defaults(func=a_rules)
    p = a.add_parser("scope", help="Resolve party roles to rating scope")
    p.add_argument("--config")
    p.add_argument("--roles", required=True, help="CSV: party_id, role_code, entity_type")
    p.add_argument("--out", default="runs/scoping.json")
    p.set_defaults(func=a_scope)
    p = a.add_parser("status", help="Stage-gate status from produced artifacts")
    for key in ("scoping", "coverage", "normalization_audit", "connections", "rule_simulation"):
        p.add_argument("--" + key.replace("_", "-"))
    p.add_argument("--calibration-reference")
    p.add_argument("--validation-reference")
    p.add_argument("--criteria", help="JSON object overriding gate criteria")
    p.set_defaults(func=a_status)

    imp = subs.add_parser("impact", help="Change-impact assessment: migration matrices, reconciliation, SQL, narrative guard")
    i = imp.add_subparsers(dest="impact_command", required=True)
    p = i.add_parser("assess", help="Assess pre/post tier snapshots and render the standard report")
    p.add_argument("--pre", required=True)
    p.add_argument("--post", required=True)
    p.add_argument("--config")
    p.add_argument("--scale")
    p.add_argument("--manifest")
    p.add_argument("--history", nargs="*")
    p.add_argument("--min-history", type=int, default=5)
    p.add_argument("--z-threshold", type=float, default=3.5)
    p.add_argument("--standard", help="Existing-process matrix CSV: segment, pre_tier, post_tier, count")
    p.add_argument("--tolerance-abs", type=int, default=0)
    p.add_argument("--tolerance-rel", type=float, default=0.0)
    p.add_argument("--strict", action="store_true", help="Exit nonzero on requires_explanation, MISMATCH or integrity findings")
    p.add_argument("--partitions", type=int, default=16)
    p.add_argument("--register")
    p.add_argument("--recorded-at", help="UTC timestamp recorded in the register entry; required with --register")
    p.add_argument("--out", default="runs/impact")
    p.set_defaults(func=i_assess)
    p = i.add_parser("sql", help="Write set-based SQL for the migration matrix")
    p.add_argument("--pre-table", required=True)
    p.add_argument("--post-table", required=True)
    p.add_argument("--id-col", default="party_id")
    p.add_argument("--segment-col", default="segment")
    p.add_argument("--tier-col", default="tier")
    p.add_argument("--pinned-col", default="pinned")
    p.add_argument("--scope-table")
    p.add_argument("--include-pinned", action="store_true", help="Count pinned parties instead of excluding them")
    p.add_argument("--out", default="runs/impact-matrix.sql")
    p.set_defaults(func=i_sql)
    p = i.add_parser("narrative-check", help="Reject drafted narratives containing numbers not in the facts pack")
    p.add_argument("--facts", required=True)
    p.add_argument("--draft", required=True)
    p.add_argument("--require", nargs="*")
    p.add_argument("--out")
    p.set_defaults(func=i_narrative)
    p = i.add_parser("verify-register", help="Verify the hash chain of an assessment register")
    p.add_argument("--register", required=True)
    p.add_argument("--anchor", help="JSON {entries, last_entry_hash} kept outside the register to detect truncation")
    p.set_defaults(func=i_register)

    p = subs.add_parser("program-demo", help="Synthetic end-to-end run of the attribute-review and impact programs")
    p.add_argument("--parties", type=int, default=20000)
    p.add_argument("--seed", type=int, default=11)
    p.add_argument("--out", default="runs/program-demo")
    p.set_defaults(func=program_demo)
