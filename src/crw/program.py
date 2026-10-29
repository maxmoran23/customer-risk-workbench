"""Stage gates for a categorical rating-model rebuild.

Later stages consume earlier artifacts, so a later stage is reported as blocked until every prerequisite meets
its exit criteria. Exit criteria are configurable; defaults are illustrative and strict on purpose.
"""

from __future__ import annotations

from .contracts import ContractError, number

STAGES = (
    ("population_scoping", (), "Rated population defined: every role code resolves to a scope class."),
    ("entity_segmentation", ("population_scoping",), "Every rated party carries one recognized entity type."),
    ("value_classification", ("entity_segmentation",),
     "Every normalized value classified; overrides evidenced; normalization audit free of blocking issues."),
    ("connections_review", ("value_classification",),
     "Cross-attribute screen run and its outcome-label status recorded."),
    ("rule_design", ("value_classification", "connections_review"),
     "Atomic and compound rules validated against the catalog and simulated on the population."),
    ("weighting_and_calibration", ("rule_design",),
     "Attribute weights and tier thresholds fixed with a referenced calibration analysis."),
    ("output_validation", ("weighting_and_calibration",),
     "Independent validation and change-impact evidence referenced for the tier output."),
)

DEFAULT_CRITERIA = {
    "max_unresolved_scope_share": 0.0,
    "max_conflicting_entity_parties": 0,
    "min_classified_share": 1.0,
    "min_reviewed_share": 1.0,
    "max_open_proposals": 0,
    "max_rule_unknown_share": 0.25,
}


def _need(artifact: dict, keys: tuple, name: str) -> None:
    missing = [k for k in keys if k not in artifact]
    if missing:
        raise ContractError(f"{name} artifact is missing {missing}; regenerate it with the current tooling")


def _check(stage: str, artifacts: dict, criteria: dict) -> tuple[str, list[str], dict]:
    blockers: list[str] = []
    metrics: dict = {}
    if stage == "population_scoping":
        scope = artifacts.get("scoping")
        if scope is None:
            return "not_started", ["no scoping report"], metrics
        _need(scope, ("unresolved_share", "unmapped_role_codes", "conflicting_entity_type_parties"), "scoping")
        metrics = {"unresolved_share": scope["unresolved_share"], "unmapped_role_codes": len(scope["unmapped_role_codes"])}
        if (scope["unresolved_share"] or 0) > criteria["max_unresolved_scope_share"]:
            blockers.append("parties without a resolvable scope exceed the threshold")
        if scope["unmapped_role_codes"]:
            blockers.append("unmapped role codes need a scope decision")
    elif stage == "entity_segmentation":
        scope = artifacts.get("scoping")
        if scope is None:
            return "not_started", ["no scoping report"], metrics
        metrics = {"conflicting_entity_type_parties": scope["conflicting_entity_type_parties"]}
        if scope["conflicting_entity_type_parties"] > criteria["max_conflicting_entity_parties"]:
            blockers.append("parties with conflicting entity types")
    elif stage == "value_classification":
        coverage, audit = artifacts.get("coverage"), artifacts.get("normalization_audit")
        if coverage is None:
            return "not_started", ["no review coverage report"], metrics
        _need(coverage, ("totals",), "coverage")
        t = coverage["totals"]
        _need(t, ("classified_share", "reviewed_share", "overrides", "overrides_evidenced"), "coverage totals")
        metrics = {"classified_share": t["classified_share"], "reviewed_share": t["reviewed_share"],
                   "overrides": t["overrides"], "overrides_evidenced": t["overrides_evidenced"]}
        if t["classified_share"] < criteria["min_classified_share"]:
            blockers.append("unclassified normalized values remain")
        if t["reviewed_share"] < criteria["min_reviewed_share"]:
            blockers.append("values not yet reviewed")
        metrics["open_proposals"] = t.get("open_proposals", 0)
        if metrics["open_proposals"] > criteria["max_open_proposals"]:
            blockers.append("proposed or challenged values await a decision")
        if t["overrides_evidenced"] < t["overrides"]:
            blockers.append("override values without evidence")
        if audit is None:
            blockers.append("no normalization audit")
        else:
            metrics["normalization_status"] = audit["status"]
            if audit["status"] == "blocking_issues":
                blockers.append("normalization audit has blocking issues")
    elif stage == "connections_review":
        report = artifacts.get("connections")
        if report is None:
            return "not_started", ["no connections screen"], metrics
        _need(report, ("outcome_status", "pairs_screened"), "connections")
        metrics = {"outcome_status": report["outcome_status"], "pairs_screened": report["pairs_screened"]}
    elif stage == "rule_design":
        simulation = artifacts.get("rule_simulation")
        if simulation is None:
            return "not_started", ["no rule simulation"], metrics
        _need(simulation, ("parties", "rules"), "rule simulation")
        n = simulation["parties"]
        worst = max((r["unknown"] / n for r in simulation["rules"]), default=0.0) if n else 0.0
        metrics = {"rules": len(simulation["rules"]), "max_unknown_share": worst,
                   "draft_rules": sum(r["status"] == "draft" for r in simulation["rules"])}
        if worst > criteria["max_rule_unknown_share"]:
            blockers.append("a rule is UNKNOWN for too much of the population")
        if metrics["draft_rules"]:
            blockers.append("draft rules remain")
    elif stage == "weighting_and_calibration":
        reference = artifacts.get("calibration_reference")
        if not reference:
            return "not_started", ["no calibration analysis referenced"], metrics
        metrics = {"calibration_reference": reference}
    elif stage == "output_validation":
        reference = artifacts.get("validation_reference")
        if not reference:
            return "not_started", ["no validation evidence referenced"], metrics
        metrics = {"validation_reference": reference}
    return ("complete" if not blockers else "in_progress"), blockers, metrics


def program_status(artifacts: dict, criteria: dict | None = None) -> dict:
    merged = dict(DEFAULT_CRITERIA)
    for key, value in (criteria or {}).items():
        if key not in DEFAULT_CRITERIA:
            raise ContractError(f"unknown criterion {key}")
        number(value, key)
        merged[key] = value
    states: dict[str, str] = {}
    rows = []
    for stage, prerequisites, exit_criteria in STAGES:
        status, blockers, metrics = _check(stage, artifacts, merged)
        waiting = [p for p in prerequisites if states.get(p) != "complete"]
        if waiting and status != "not_started":
            blockers = [f"prerequisite incomplete: {p}" for p in waiting] + blockers
            status = "blocked"
        elif waiting:
            status = "blocked"
            blockers = [f"prerequisite incomplete: {p}" for p in waiting] + blockers
        states[stage] = status
        rows.append({"stage": stage, "status": status, "prerequisites": list(prerequisites),
                     "exit_criteria": exit_criteria, "blockers": blockers, "metrics": metrics})
    next_stage = next((r["stage"] for r in rows if r["status"] != "complete"), None)
    return {
        "stages": rows,
        "next_actionable": next_stage,
        "criteria": merged,
        "limit": "Gate status reflects supplied artifacts and configured thresholds; it is a planning control, not an approval.",
    }
