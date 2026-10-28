"""Population diagnostics with explicit joins and crossed change attribution."""

from __future__ import annotations

from collections import Counter
from .contracts import ContractError, number
from .features import FeatureSet, digest
from .policy import Policy
from .scoring import score
from .validation import distribution_drift, migration_matrix, stratified_sample


def validate_assessment(record: dict) -> None:
    if not isinstance(record, dict) or "assessment_hash" not in record:
        raise ContractError("assessment object with content hash required")
    payload = {k: v for k, v in record.items() if k != "assessment_hash"}
    if digest(payload) != record["assessment_hash"]:
        raise ContractError("assessment content hash mismatch")
    for field in ("provisional_index", "lower_bound", "upper_bound"):
        number(record[field], field, maximum=100)
    number(record["coverage"], "coverage", maximum=1)
    if not record["lower_bound"] <= record["provisional_index"] <= record["upper_bound"]:
        raise ContractError("inconsistent assessment bounds")


def _index(records: list[dict]) -> dict:
    if not records:
        raise ContractError("nonempty assessment population required")
    result = {}
    for record in records:
        validate_assessment(record)
        if record["customer_id"] in result:
            raise ContractError(
                "multiple assessments per customer; choose one cutoff and policy before monitoring"
            )
        result[record["customer_id"]] = record
    if len({r["as_of"] for r in records}) != 1 or len({r["policy_hash"] for r in records}) != 1:
        raise ContractError("each monitoring population must use one cutoff and policy")
    if len({r["lineage"]["unit"] for r in records}) != 1:
        raise ContractError("monitoring population contains inconsistent amount units")
    return result


def population_summary(records: list[dict]) -> dict:
    indexed = _index(records)
    return {
        "n": len(indexed),
        "bands": dict(Counter(r["band"] for r in records)),
        "incomplete_scores": sum(r["score"] is None for r in records),
        "mean_coverage": sum(r["coverage"] for r in records) / len(records),
        "review_required": sum(r["band"] == "REVIEW_REQUIRED" for r in records),
        "screening_true": sum(any(f["state"] == "TRUE" for f in r["review_flags"]) for r in records),
        "screening_unknown": sum(any(f["state"] == "UNKNOWN" for f in r["review_flags"]) for r in records),
        "policy_hash": records[0]["policy_hash"],
        "as_of": records[0]["as_of"],
    }


def monitor_portfolios(
    reference: list[dict],
    current: list[dict],
    *,
    min_n: int = 50,
    psi_investigate: float = 0.2,
    coverage_drop_investigate: float = 0.05,
) -> dict:
    if type(min_n) is not int or min_n < 1:
        raise ContractError("min_n must be positive integer")
    number(psi_investigate, "psi threshold")
    number(coverage_drop_investigate, "coverage threshold", maximum=1)
    old, new = _index(reference), _index(current)
    if reference[0]["lineage"]["unit"] != current[0]["lineage"]["unit"]:
        raise ContractError("cannot compare portfolios with different amount units")
    ids = sorted(old.keys() & new.keys())
    ref, cur = population_summary(reference), population_summary(current)
    drift = distribution_drift([r["score"] for r in reference], [r["score"] for r in current])
    coverage_delta = cur["mean_coverage"] - ref["mean_coverage"]
    support = min(len(old), len(new)) >= min_n
    same_policy = ref["policy_hash"] == cur["policy_hash"]
    signals = []
    if not support:
        signals.append("insufficient_population_support")
    if not same_policy:
        signals.append("policy_change_confounds_distribution_comparison")
    if support and drift["psi"]["value"] >= psi_investigate:
        signals.append("distribution_investigation_threshold")
    if coverage_delta <= -coverage_drop_investigate:
        signals.append("coverage_drop_investigation_threshold")
    return {
        "reference": ref,
        "current": cur,
        "matched_customers": len(ids),
        "entrants": len(new.keys() - old.keys()),
        "exits": len(old.keys() - new.keys()),
        "score_drift": drift,
        "coverage_change": coverage_delta,
        "paired_migration": migration_matrix([old[k]["band"] for k in ids], [new[k]["band"] for k in ids])
        if ids
        else None,
        "signals": signals,
        "status": "investigate" if signals else "no_configured_investigation_trigger",
        "settings": {
            "min_n": min_n,
            "psi_investigate": psi_investigate,
            "coverage_drop_investigate": coverage_drop_investigate,
        },
        "limits": [
            "Thresholds are illustrative investigation settings, not statistical significance or regulatory cutoffs.",
            "Complete score drift includes missing as its own bin. Provisional lower bounds are not treated as complete risk scores.",
            "Unpaired distributions reflect population composition; paired migration uses matched customer IDs only.",
            "REVIEW_REQUIRED is an abstention state and is not ordered above HIGH.",
            "No outcome labels are present; these diagnostics do not measure detection effectiveness.",
        ],
    }


def attribute_change(
    before: FeatureSet, after: FeatureSet, before_policy: Policy, after_policy: Policy
) -> dict:
    cid = before.lineage["customer_id"]
    if after.lineage["customer_id"] != cid:
        raise ContractError("change attribution requires one customer")
    if before.lineage["unit"] != after.lineage["unit"]:
        raise ContractError("change attribution requires a consistent amount unit")
    states = {}
    for data_name, features in (("old_data", before), ("new_data", after)):
        for policy_name, policy in (("old_policy", before_policy), ("new_policy", after_policy)):
            states[data_name + "__" + policy_name] = score(features, policy, cid, features.lineage["cutoff"])
    a, b, c, d = [
        states[key]["provisional_index"]
        for key in (
            "old_data__old_policy",
            "new_data__old_policy",
            "old_data__new_policy",
            "new_data__new_policy",
        )
    ]
    return {
        "customer_id": cid,
        "total_provisional_change": d - a,
        "data_effect": ((b - a) + (d - c)) / 2,
        "policy_effect": ((c - a) + (d - b)) / 2,
        "interaction": d - b - c + a,
        "states": states,
        "method": "two-order Shapley allocation of crossed data/policy changes",
        "limit": "Arithmetic attribution, not causality; data effect includes missingness and elapsed-time changes. Inspect score availability and bounds in all four states.",
    }


def review_sample(records: list[dict], per_band: int = 20, seed: int = 7) -> dict:
    _index(records)
    if type(per_band) is not int or per_band < 1:
        raise ContractError("per_band must be positive integer")
    counts = Counter(r["band"] for r in records)
    allocation = {k: min(per_band, n) for k, n in counts.items()}
    rows = [
        {"id": r["customer_id"], "band": r["band"], "assessment_hash": r["assessment_hash"]} for r in records
    ]
    result = stratified_sample(rows, "band", allocation, seed=seed, id_key="id")
    return {
        "population_n": len(records),
        "population_sizes": dict(counts),
        "allocation": allocation,
        "sample": result,
        "seed": seed,
        "limit": "Stratified review sample with retained design weights. Oversampled risk bands do not estimate population error via an unweighted pooled rate.",
    }
