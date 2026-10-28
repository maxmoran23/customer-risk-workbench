"""Explainable grouped index with bounded missing-evidence uncertainty."""

from __future__ import annotations

import math
from .contracts import ContractError, identifier, number, utc
from .features import FeatureSet, digest
from .policy import PROFILE_KEYS, Policy


def severity(value: float, factor: dict) -> float:
    number(value, factor["feature"])
    normalized = min(1.0, max(0.0, (value - factor["low"]) / (factor["high"] - factor["low"])))
    return normalized if factor["direction"] == "increasing" else 1 - normalized


def score(features: FeatureSet, policy: Policy, customer_id: str, as_of: str) -> dict:
    identifier(customer_id, "customer_id")
    cutoff = utc(as_of)
    if features.lineage.get("cutoff") != cutoff:
        raise ContractError("feature cutoff does not match requested assessment")
    if features.lineage.get("customer_id") != customer_id:
        raise ContractError("feature customer does not match requested assessment")
    c = policy.to_dict()
    declared = {"profile." + key for key in c.get("profile_keys", PROFILE_KEYS)}
    undeclared = {key for key in features.values if key.startswith("profile.")} - declared
    if undeclared:
        raise ContractError(f"undeclared profile features: {sorted(undeclared)}")
    reasons, missing = [], []
    grouped = {g["id"]: [] for g in c["groups"]}
    required_missing = []
    for factor in c["factors"]:
        name = factor["feature"]
        value = features.values.get(name)
        why = "missing_value" if value is None else None
        if name.startswith("txn."):
            window = name.split(".")[1]
            if features.quality["support"].get(window, 0) < factor["min_support"]:
                why = "insufficient_events"
            if factor["require_full_window"] and not features.quality["complete_windows"].get(window, False):
                why = "incomplete_window"
        if why:
            missing.append(
                {"factor": factor["id"], "feature": name, "reason": why, "required": factor["required"]}
            )
            if factor["required"]:
                required_missing.append(factor["id"])
            normalized = None
        else:
            normalized = severity(value, factor)
        raw = factor["weight"] * normalized if normalized is not None else 0.0
        row = {
            "factor": factor["id"],
            "feature": name,
            "group": factor["group"],
            "value": value,
            "severity": normalized,
            "weight": factor["weight"],
            "raw_points": raw,
            "missing_reason": why,
            "rationale": factor["rationale"],
        }
        reasons.append(row)
        grouped[factor["group"]].append(row)
    groups = []
    for group in c["groups"]:
        rows = grouped[group["id"]]
        known = [r["raw_points"] for r in rows]
        possible = [r["raw_points"] if r["severity"] is not None else r["weight"] for r in rows]
        combine = math.fsum if group["aggregation"] == "sum" else lambda xs: max(xs, default=0.0)
        lower = min(group["cap"], combine(known))
        upper = min(group["cap"], combine(possible))
        groups.append(
            {
                "id": group["id"],
                "aggregation": group["aggregation"],
                "cap": group["cap"],
                "points": lower,
                "lower_bound": lower,
                "upper_bound": upper,
            }
        )
    lower = math.fsum(g["lower_bound"] for g in groups)
    upper = math.fsum(g["upper_bound"] for g in groups)
    complete = not missing
    gates = []
    if required_missing:
        gates.append("required_evidence_missing")
    if c["require_complete_history"] and not features.quality.get("history_complete", False):
        gates.append("history_completeness_not_confirmed")
    if policy.band(lower) != policy.band(upper):
        gates.append("missing_evidence_crosses_band")
    band = "REVIEW_REQUIRED" if gates else policy.band(lower)
    routes = []
    for route in c["routes"]:
        value = features.values.get(route["feature"])
        state = "UNKNOWN" if value is None else ("TRUE" if value >= route["minimum"] else "FALSE")
        routes.append({**route, "state": state, "observed_value": value})
    result = {
        "schema_version": "1.0.0",
        "customer_id": customer_id,
        "as_of": cutoff,
        "policy_id": c["policy_id"],
        "policy_version": c["version"],
        "policy_hash": policy.digest,
        "score": lower if complete and not gates else None,
        "provisional_index": lower,
        "band": band,
        "band_basis": "complete" if complete else "bounded_incomplete_evidence",
        "lower_bound": lower,
        "upper_bound": upper,
        "coverage": (len(reasons) - len(missing)) / len(reasons),
        "missing_features": missing,
        "gates": gates,
        "groups": groups,
        "reasons": reasons,
        "review_flags": routes,
        "lineage": features.lineage,
        "quality": features.quality,
        "interpretation": "Constructed review-priority index. Bounds are arithmetic missing-evidence bounds, not confidence intervals or probabilities.",
    }
    result["assessment_hash"] = digest(result)
    return result


def compare_assessments(before: dict, after: dict) -> dict:
    if before["customer_id"] != after["customer_id"]:
        raise ContractError("assessment comparison requires the same customer")
    old = {g["id"]: g["points"] for g in before["groups"]}
    new = {g["id"]: g["points"] for g in after["groups"]}
    return {
        "customer_id": before["customer_id"],
        "from_band": before["band"],
        "to_band": after["band"],
        "provisional_delta": after["provisional_index"] - before["provisional_index"],
        "group_deltas": {k: new.get(k, 0) - old.get(k, 0) for k in sorted(old.keys() | new.keys())},
        "policy_changed": before["policy_hash"] != after["policy_hash"],
        "data_changed": before["lineage"] != after["lineage"],
        "attribution_limit": "If both policy and data changed, rerun crossed combinations to isolate effects.",
    }
