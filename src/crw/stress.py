"""Feature-level sensitivity experiments; these are not causal counterfactuals."""

from __future__ import annotations

from copy import deepcopy
from collections import Counter
from .contracts import ContractError
from .features import FeatureSet
from .policy import Policy
from .scoring import score


STRESSES = [
    {
        "id": "ownership_unknown",
        "feature": "profile.ownership_opacity",
        "operation": "missing",
        "value": None,
    },
    {"id": "geography_increase", "feature": "profile.geography_exposure", "operation": "set", "value": 0.9},
    {"id": "funds_concern", "feature": "profile.source_of_funds_concern", "operation": "set", "value": 0.9},
    {"id": "volume_double", "feature": "txn.30d.expected_volume_ratio", "operation": "multiply", "value": 2},
    {"id": "cash_concentration", "feature": "txn.30d.cash_share", "operation": "set", "value": 0.9},
    {"id": "documentation_gap", "feature": "profile.documentation_gap", "operation": "set", "value": 0.9},
    {"id": "screening_unresolved", "feature": "profile.screening_unresolved", "operation": "set", "value": 1},
    {"id": "profile_stale", "feature": "profile_age_days", "operation": "set", "value": 900},
]


def stress_portfolio(records: list[tuple[str, FeatureSet]], policy: Policy, as_of: str) -> dict:
    if len({cid for cid, _ in records}) != len(records):
        raise ContractError("stress population requires unique customer IDs")
    if len({f.lineage["unit"] for _, f in records}) > 1:
        raise ContractError("stress population requires a consistent amount unit")
    baselines = {cid: score(f, policy, cid, as_of) for cid, f in records}
    experiments = []
    for stress in STRESSES:
        deltas = []
        complete_deltas = []
        availability = Counter()
        migrations = Counter()
        examples = []
        for cid, original in records:
            f = deepcopy(original)
            key = stress["feature"]
            if stress["operation"] == "multiply":
                value = f.values.get(key)
                f.values[key] = value * stress["value"] if value is not None else None
            else:
                f.values[key] = stress["value"]
            f.lineage["feature_perturbation"] = stress["id"]
            revised = score(f, policy, cid, as_of)
            before = baselines[cid]
            delta = revised["provisional_index"] - before["provisional_index"]
            deltas.append(delta)
            availability[(before["score"] is not None, revised["score"] is not None)] += 1
            if before["score"] is not None and revised["score"] is not None:
                complete_deltas.append(revised["score"] - before["score"])
            migrations[(before["band"], revised["band"])] += 1
            if len(examples) < 3:
                examples.append(
                    {
                        "customer_id": cid,
                        "before": before["band"],
                        "after": revised["band"],
                        "provisional_lower_bound_delta": delta,
                        "before_score": before["score"],
                        "after_score": revised["score"],
                        "before_bounds": [before["lower_bound"], before["upper_bound"]],
                        "after_bounds": [revised["lower_bound"], revised["upper_bound"]],
                        "before_gates": before["gates"],
                        "after_gates": revised["gates"],
                    }
                )
        experiments.append(
            {
                **stress,
                "n": len(records),
                "mean_delta": sum(deltas) / len(deltas) if deltas else None,
                "delta_basis": "provisional lower bound; a decrease can reflect missing evidence",
                "complete_paired_n": len(complete_deltas),
                "mean_complete_score_delta": sum(complete_deltas) / len(complete_deltas)
                if complete_deltas
                else None,
                "score_availability": [
                    {"before_complete": a, "after_complete": b, "n": n}
                    for (a, b), n in sorted(availability.items())
                ],
                "max_delta": max(deltas, default=None),
                "min_delta": min(deltas, default=None),
                "migrations": [{"from": a, "to": b, "count": n} for (a, b), n in sorted(migrations.items())],
                "examples": examples,
            }
        )
    return {
        "method": "one-factor-at-a-time deterministic perturbation",
        "experiments": experiments,
        "limitation": "Perturbations hold other computed features fixed and may not be jointly realizable. They measure software sensitivity, not causal effect or real-world risk change.",
    }
