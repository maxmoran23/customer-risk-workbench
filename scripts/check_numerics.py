"""Reproduce seeded statistical comparisons against independent scientific libraries."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
import platform
import random

from scipy import stats
from sklearn import metrics

from crw.io import atomic_json
from crw.validation import binary_metrics, distribution_drift, wilson_interval

ROOT = Path(__file__).resolve().parents[1]
METRICS = ("roc_auc", "average_precision", "brier", "log_loss", "ks_statistic",
           "wasserstein_distance", "wilson_lower", "wilson_upper")


def canonical_hash(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def generate_case(index: int, seed: int) -> dict:
    rng = random.Random(seed)
    n = (2, 3, 5, 10, 25, 50, 100, 250, 500, 1000)[index % 10]
    if index % 20 == 0:
        labels, label_design = [0] * n, "single_class_negative"
    elif index % 20 == 1:
        labels, label_design = [1] * n, "single_class_positive"
    elif index % 20 == 2:
        labels, label_design = [1] + [0] * (n - 1), "one_positive"
    elif index % 20 == 3:
        labels, label_design = [0] + [1] * (n - 1), "one_negative"
    else:
        prevalence = (0.01, 0.05, 0.1, 0.3, 0.5, 0.8, 0.95, 0.99)[index % 8]
        labels = [int(rng.random() < prevalence) for _ in range(n)]
        labels[0], labels[1] = 0, 1
        label_design = "seeded_imbalance_with_both_classes_retained"
    rng.shuffle(labels)
    probability_design = index % 5
    if probability_design == 0:
        probabilities = [0.5] * n
    elif probability_design == 1:
        probabilities = [rng.choice((0.1, 0.5, 0.9)) for _ in labels]
    elif probability_design == 2:
        probabilities = [min(1 - 1e-6, max(1e-6, round(rng.random(), 2))) for _ in labels]
    elif probability_design == 3:
        probabilities = [1 - 1e-10 if label else 1e-10 for label in labels]
    else:
        probabilities = [min(1 - 1e-6, max(1e-6, 0.15 + 0.65 * label + rng.gauss(0, 0.25)))
                         for label in labels]
    reference_n, current_n = rng.randrange(2, 151), rng.randrange(2, 201)
    distribution_design = (index // 5) % 5
    if distribution_design == 0:
        reference, current = [2.0] * reference_n, [2.0] * current_n
    elif distribution_design == 1:
        reference, current = [-1.0] * reference_n, [3.0] * current_n
    elif distribution_design == 2:
        reference = [rng.randrange(-3, 4) for _ in range(reference_n)]
        current = [rng.randrange(-2, 5) for _ in range(current_n)]
    elif distribution_design == 3:
        reference = [rng.gauss(0, 1) for _ in range(reference_n)]
        current = [rng.gauss(0.4, 1.3) for _ in range(current_n)]
    else:
        reference = [rng.expovariate(0.5) for _ in range(reference_n)]
        current = [rng.expovariate(0.25) for _ in range(current_n)]
    return {"case_id": index, "seed": seed, "labels": labels, "probabilities": probabilities,
            "reference": reference, "current": current, "label_design": label_design,
            "probability_design": ("constant_ties", "three_level_ties", "rounded_probability_ties",
                                   "near_certain_correct", "noisy_outcome_related")[probability_design],
            "distribution_design": ("identical_constant", "shifted_constant", "discrete_ties",
                                    "gaussian_shift", "exponential_scale_shift")[distribution_design],
            "confidence": (0.8, 0.9, 0.95, 0.99)[index % 4]}


def run(cases: int = 100, seed: int = 20261028, tolerance: float = 1e-12) -> dict:
    if type(cases) is not int or cases < 1 or type(seed) is not int:
        raise ValueError("cases must be a positive integer and seed an integer")
    if not math.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("tolerance must be finite and positive")
    summary = {name: {"cases_compared": 0, "cases_skipped": 0, "skip_reasons": {},
                      "maximum_absolute_error": 0.0, "worst_case_id": None,
                      "absolute_tolerance": tolerance, "passed": True} for name in METRICS}
    failures, case_manifest, sample_sizes = [], [], []
    design_counts = {name: Counter() for name in ("label_design", "probability_design", "distribution_design")}

    def compare(name: str, actual: float, expected: float, case_id: int):
        entry = summary[name]
        entry["cases_compared"] += 1
        if actual is None or not math.isfinite(actual) or not math.isfinite(expected):
            entry["passed"] = False
            failures.append({"case_id": case_id, "metric": name, "reason": "unexpected undefined or nonfinite result"})
            return
        error = abs(actual - expected)
        if entry["worst_case_id"] is None or error > entry["maximum_absolute_error"]:
            entry["maximum_absolute_error"], entry["worst_case_id"] = error, case_id
        if error > tolerance:
            entry["passed"] = False
            failures.append({"case_id": case_id, "metric": name, "absolute_error": error,
                             "actual": actual, "reference": float(expected)})

    def skip_undefined(name: str, actual: dict, reason: str, case_id: int):
        entry = summary[name]
        entry["cases_skipped"] += 1
        entry["skip_reasons"][reason] = entry["skip_reasons"].get(reason, 0) + 1
        if actual["value"] is not None or not actual["reason"]:
            entry["passed"] = False
            failures.append({"case_id": case_id, "metric": name,
                             "reason": "expected explicit null with reason for an undefined statistic"})

    for index in range(cases):
        case = generate_case(index, seed + index)
        labels, probabilities = case["labels"], case["probabilities"]
        observed = binary_metrics(labels, probabilities)
        if 0 < sum(labels) < len(labels):
            compare("roc_auc", observed["roc_auc"]["value"], metrics.roc_auc_score(labels, probabilities), index)
        else:
            skip_undefined("roc_auc", observed["roc_auc"], "single outcome class", index)
        if sum(labels):
            compare("average_precision", observed["average_precision"]["value"],
                    metrics.average_precision_score(labels, probabilities), index)
        else:
            skip_undefined("average_precision", observed["average_precision"], "no positive outcomes", index)
        compare("brier", observed["brier"]["value"], metrics.brier_score_loss(labels, probabilities), index)
        compare("log_loss", observed["log_loss"]["value"], metrics.log_loss(labels, probabilities, labels=[0, 1]), index)
        drift = distribution_drift(case["reference"], case["current"])
        compare("ks_statistic", drift["ks_statistic"]["value"],
                stats.ks_2samp(case["reference"], case["current"], method="asymp").statistic, index)
        compare("wasserstein_distance", drift["wasserstein_distance"]["value"],
                stats.wasserstein_distance(case["reference"], case["current"]), index)
        observed_interval = wilson_interval(sum(labels), len(labels), case["confidence"])
        reference_interval = stats.binomtest(sum(labels), len(labels)).proportion_ci(
            confidence_level=case["confidence"], method="wilson")
        compare("wilson_lower", observed_interval["lower"], reference_interval.low, index)
        compare("wilson_upper", observed_interval["upper"], reference_interval.high, index)
        sample_sizes.append(len(labels))
        for name in design_counts:
            design_counts[name][case[name]] += 1
        case_manifest.append({"case_id": index, "seed": case["seed"], "input_sha256": canonical_hash(case)})

    return {"schema_version": "crw-numerical-crosscheck-v1", "passed": not failures,
            "scope": "finite-sample numerical agreement only; not model efficacy, interval coverage or production validation",
            "cases": cases, "seed_start": seed, "case_seed_rule": "seed_start + case_id, case_id in [0,cases)",
            "case_manifest_sha256": canonical_hash(case_manifest),
            "n": {"binary_observations_total": sum(sample_sizes), "minimum_case_size": min(sample_sizes),
                  "maximum_case_size": max(sample_sizes)},
            "design_counts": {name: dict(counts) for name, counts in design_counts.items()},
            "metrics": summary, "comparisons": sum(item["cases_compared"] for item in summary.values()),
            "undefined_checks": sum(item["cases_skipped"] for item in summary.values()),
            "maximum_absolute_error": max(item["maximum_absolute_error"] for item in summary.values()),
            "absolute_tolerance": tolerance, "failures": failures,
            "versions": {"python": platform.python_version(), **{name: version(name)
                         for name in ("numpy", "scipy", "scikit-learn")}},
            "source_files": {"implementation": "src/crw/validation.py", "script": "scripts/check_numerics.py"},
            "source_sha256": {name: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
                              for name, relative in (("implementation", "src/crw/validation.py"),
                                                     ("script", "scripts/check_numerics.py"))},
            "reproduce": "PYTHONPATH=src uv run python scripts/check_numerics.py",
            "limitations": ["Only the returned KS statistic is compared; no KS p-value validity claim is made for ties.",
                            "Single-class AUC and no-positive AP return explicit nulls and are counted separately.",
                            "Probability inputs remain strictly inside (0,1), so comparisons use finite log loss.",
                            "Wilson comparisons verify endpoint arithmetic, not repeated-sampling coverage.",
                            "The seeded data are synthetic and do not assess any customer-risk model's effectiveness."]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20261028)
    parser.add_argument("--tolerance", type=float, default=1e-12)
    parser.add_argument("--out", default="evidence/numerical-crosscheck.json")
    args = parser.parse_args()
    report = run(args.cases, args.seed, args.tolerance)
    atomic_json(args.out, report)
    print(json.dumps({"passed": report["passed"], "cases": report["cases"],
                      "comparisons": report["comparisons"], "undefined_checks": report["undefined_checks"],
                      "maximum_absolute_error": report["maximum_absolute_error"], "output": args.out}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
