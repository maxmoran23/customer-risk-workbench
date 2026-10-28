"""Verify and explain portable synthetic fixtures using the public workbench APIs."""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path

from crw.contracts import Customer, Transaction
from crw.features import build_features
from crw.io import atomic_json, read_jsonl
from crw.monitoring import monitor_portfolios, population_summary
from crw.patterns import evaluate_patterns
from crw.policy import reference_policy
from crw.scoring import compare_assessments, score

from build_fixtures import build_records

ROOT = Path(__file__).resolve().parent


def verify_equal(actual, expected, field: str) -> None:
    if isinstance(expected, (float, int)) and not isinstance(expected, bool):
        passed = actual is not None and math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-10)
    else:
        passed = actual == expected
    if not passed:
        raise ValueError(f"{field}: expected {expected!r}, received {actual!r}")


def run_walkthrough(fixture_dir: Path = ROOT) -> dict:
    manifest = json.loads((fixture_dir / "fixture-manifest.json").read_text())
    expected = json.loads((fixture_dir / "expected-summary.json").read_text())
    if manifest["data_status"] != "synthetic_only" or manifest["base_unit"] != "SYNTHETIC_UNIT":
        raise ValueError("this walkthrough requires its explicitly declared synthetic unit and fixtures")
    for name, sha256 in manifest["files"].items():
        actual = hashlib.sha256((fixture_dir / name).read_bytes()).hexdigest()
        verify_equal(actual, sha256, f"fixture digest {name}")

    customers = list(read_jsonl(fixture_dir / "customers.jsonl", Customer))
    transactions = list(read_jsonl(fixture_dir / "transactions.jsonl", Transaction))
    generated_customers, generated_events = build_records()
    verify_equal(customers, generated_customers, "constructed customer reproduction")
    verify_equal(transactions, generated_events, "constructed ledger reproduction")
    verify_equal(len(customers), manifest["customers"], "customer count")
    verify_equal(len(transactions), manifest["transactions"], "transaction count")
    policy = reference_policy()
    verify_equal(policy.digest, manifest["policy_hash"], "reference policy hash")
    by_customer = {customer.customer_id: [] for customer in customers}
    for event in transactions:
        by_customer[event.customer_id].append(event)

    assessments, evidence = [], []
    for customer in customers:
        features = build_features(customer, by_customer[customer.customer_id], manifest["as_of"],
                                  base_unit=manifest["base_unit"])
        result = score(features, policy, customer.customer_id, manifest["as_of"])
        wanted = expected["customers"][customer.customer_id]
        verify_equal(result["score"], wanted["score"], customer.customer_id + " complete score")
        verify_equal(result["band"], wanted["band"], customer.customer_id + " band")
        verify_equal(result["review_flags"][0]["state"], wanted["screening_state"], "screening route")
        verify_equal(result["coverage"], 1.0, "complete factor coverage")
        for group in result["groups"]:
            verify_equal(group["points"], wanted["groups"][group["id"]], "group " + group["id"])
        verify_equal(features.values["txn.30d.total"], 6000, "30d amount")
        verify_equal(features.values["txn.30d.growth_ratio"], 1, "current/prior month ratio")
        reversed_features = build_features(customer, reversed(by_customer[customer.customer_id]),
                                           manifest["as_of"], base_unit=manifest["base_unit"])
        replay = score(reversed_features, policy, customer.customer_id, manifest["as_of"])
        verify_equal(replay["assessment_hash"], result["assessment_hash"], "permutation replay")
        patterns = evaluate_patterns(features)
        assessments.append(result)
        evidence.append({
            "customer_id": customer.customer_id, "score": result["score"], "band": result["band"],
            "bounds": [result["lower_bound"], result["upper_bound"]], "coverage": result["coverage"],
            "group_points": {g["id"]: g["points"] for g in result["groups"]},
            "screening_routes": result["review_flags"],
            "true_review_hypotheses": [
                {key: row[key] for key in ("id", "title", "state", "benign_explanation", "next_evidence", "limit")}
                for row in patterns if row["state"] == "TRUE"
            ],
            "assessment_hash": result["assessment_hash"],
        })

    original = customers[0]
    original_profile = dict(original.profile)
    changed = replace(original, profile={**original.profile, "ownership_opacity": None})
    changed_features = build_features(changed, by_customer[changed.customer_id], manifest["as_of"],
                                      base_unit=manifest["base_unit"])
    changed_result = score(changed_features, policy, changed.customer_id, manifest["as_of"])
    verify_equal(original.profile, original_profile, "original profile preserved")
    wanted = expected["missing_ownership"]
    for field in ("score", "band", "lower_bound", "upper_bound"):
        verify_equal(changed_result[field], wanted[field], "missing ownership " + field)
    if wanted["required_gate"] not in changed_result["gates"]:
        raise ValueError("mandatory missing evidence did not require review")
    comparison = compare_assessments(assessments[0], changed_result)

    revised = [changed_result, *assessments[1:]]
    monitoring = monitor_portfolios(assessments, revised, min_n=expected["monitoring"]["minimum_population"])
    verify_equal(monitoring["matched_customers"], expected["monitoring"]["matched_customers"], "matched customers")
    if expected["monitoring"]["required_signal"] not in monitoring["signals"]:
        raise ValueError("three examples were incorrectly treated as sufficient monitoring support")
    return {
        "status": "verified", "data_status": "synthetic_only", "base_unit": manifest["base_unit"],
        "as_of": manifest["as_of"], "fixture_sha256": manifest["files"], "policy_hash": policy.digest,
        "records": {"customers": len(customers), "transactions": len(transactions)},
        "checks": ["fixture file hashes", "exact fixture reconstruction", "strict contract parsing",
                   "hand-calculated group contributions and scores", "separate screening routes",
                   "input-permutation replay", "required-evidence abstention", "population support gate"],
        "customer_assessments": evidence,
        "missing_required_evidence": {
            "customer_id": original.customer_id, "before_score": assessments[0]["score"],
            "after_score": changed_result["score"], "after_band": changed_result["band"],
            "before_bounds": [assessments[0]["lower_bound"], assessments[0]["upper_bound"]],
            "after_bounds": [changed_result["lower_bound"], changed_result["upper_bound"]],
            "gates": changed_result["gates"], "comparison": comparison,
            "interpretation": "The lower bound falls because evidence is missing; risk reduction is not established.",
        },
        "population_summary": population_summary(assessments),
        "monitoring": monitoring,
        "limits": ["Three deliberately constructed examples are not a representative sample.",
                   "A TRUE hypothesis is a review question, not a misconduct conclusion.",
                   "Reference policy parameters are illustrative and lack operational calibration.",
                   "The missing-evidence modification demonstrates software behavior, not a causal counterfactual."],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="Optional JSON evidence output; fixtures remain unchanged")
    args = parser.parse_args()
    result = run_walkthrough()
    if args.out:
        if args.out.resolve().parent == ROOT:
            raise ValueError("write generated evidence outside the committed examples directory")
        atomic_json(args.out, result)
    print(json.dumps({
        "status": result["status"], "records": result["records"], "base_unit": result["base_unit"],
        "assessments": [{"customer_id": r["customer_id"], "score": r["score"], "band": r["band"]}
                        for r in result["customer_assessments"]],
        "missing_required_evidence": result["missing_required_evidence"],
        "monitoring_signals": result["monitoring"]["signals"],
        "checks": result["checks"],
    }, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
