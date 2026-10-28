"""Optional, local supervised-research experiments; all bundled outcomes are synthetic.

There is no dependency on policy scoring. No fitted Python object is deserialized.
The logistic model is exported as inspectable numeric JSON; tree metadata describes
an experiment and cannot be used as an executable model artifact.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
from importlib.metadata import version
import json
import math
import platform
import random
from statistics import mean
from typing import Any

from .validation import (
    binary_metrics,
    calibration_bins,
    paired_bootstrap_delta,
    permutation_importance,
    segment_metrics,
)

FEATURE_ORDER = (
    "jurisdiction_exposure", "ownership_opacity", "velocity_change", "flow_through",
    "counterparty_turnover", "account_age_scaled", "business_complexity", "activity_seasonality",
)
LIMITATIONS = [
    "Synthetic stochastic outcomes are not evidence of real customer risk prediction.",
    "Outcome labels represent an invented event, not criminal conduct, SAR filing, or a sanctions disposition.",
    "Feature definitions, horizon, parameters, thresholds, costs, and support gates are illustrative.",
    "Threshold selection is performed on calibration data; probability recalibration is not performed.",
    "Temporal and entity separation tests unseen customers; it does not establish performance for existing customers.",
    "Bootstrap intervals condition on fitted models and omit training, label and selection uncertainty.",
    "Demonstrated discrimination does not establish fairness, regulatory compliance, or production readiness.",
]


def _time(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp must be an ISO 8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid ISO 8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _stamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be finite numeric")
    return float(value)


def _sigmoid(value: float) -> float:
    return 1 / (1 + math.exp(-value)) if value >= 0 else math.exp(value) / (1 + math.exp(value))


def generate_research_rows(n: int = 3000, seed: int = 7, label_noise: float = 0.0,
                           prevalence_shift: float = 0.0, repeat_snapshots: int = 1) -> list[dict]:
    """Generate independent customer latent states, noisy measurements and stochastic outcomes.

    n counts customers, not rows. Repeated snapshots share latent state and must
    therefore remain grouped during splitting and resampling.
    """
    if type(n) is not int or n < 1 or type(repeat_snapshots) is not int or not 1 <= repeat_snapshots <= 12:
        raise ValueError("n must be positive; repeat_snapshots must be an integer in [1,12]")
    noise = _number(label_noise, "label_noise")
    shift = _number(prevalence_shift, "prevalence_shift")
    if not 0 <= noise <= 0.5 or not -10 <= shift <= 10:
        raise ValueError("label_noise must be in [0,0.5]; prevalence_shift must be in [-10,10]")
    rng = random.Random(seed)
    epoch = datetime(2024, 1, 1, tzinfo=timezone.utc)
    rows = []
    for customer in range(n):
        latent, opacity, complexity = rng.gauss(0, 1), rng.gauss(0, 1), rng.random()
        age = rng.random()
        segment = rng.choice(("retail", "small_business", "corporate"))
        day = rng.randrange(360)
        for snapshot in range(repeat_snapshots):
            timestamp = epoch + timedelta(days=day + 7 * snapshot, hours=rng.randrange(24))
            seasonal = math.sin(2 * math.pi * (timestamp - epoch).days / 90)
            local_state = latent + rng.gauss(0, 0.25)
            features = {
                "jurisdiction_exposure": _sigmoid(0.85 * local_state + rng.gauss(0, 1)),
                "ownership_opacity": _sigmoid(opacity + rng.gauss(0, 0.65)),
                "velocity_change": _sigmoid(local_state + 0.3 * seasonal + rng.gauss(0, 0.65)),
                "flow_through": _sigmoid(0.8 * local_state + 0.3 * opacity + rng.gauss(0, 0.75)),
                "counterparty_turnover": _sigmoid(0.7 * local_state + rng.gauss(0, 1)),
                "account_age_scaled": age,
                "business_complexity": complexity,
                "activity_seasonality": (seasonal + 1) / 2,
            }
            # The unobserved event process precedes label noise and is independent of the policy engine.
            latent_log_odds = (-2.2 + 1.4 * local_state + 0.6 * opacity + 0.7 * complexity
                               - 0.5 * age + 0.5 * (local_state > 0.7 and opacity > 0.4)
                               + 0.15 * (timestamp - epoch).days / 360 + shift)
            label = int(rng.random() < _sigmoid(latent_log_odds))
            if rng.random() < noise:
                label = 1 - label
            for name in FEATURE_ORDER:
                if rng.random() < 0.025:
                    features[name] = None
            observed = timestamp + timedelta(days=30)
            available = observed + timedelta(days=rng.randrange(1, 15))
            rows.append({"customer_id": f"RESEARCH-{customer:07d}", "as_of": _stamp(timestamp),
                         "feature_available_at": _stamp(timestamp - timedelta(hours=1)),
                         "outcome_observed_at": _stamp(observed), "outcome_available_at": _stamp(available),
                         "segment": segment, "label": label, "features": features})
    return rows


def temporal_entity_split(rows: Sequence[Mapping], train_end: str, calibration_end: str, holdout_end: str,
                          maturity_days: int = 30, embargo_days: int = 0) -> dict:
    """Purge customers crossing time partitions; require outcome availability by each cutoff."""
    endpoints = [_time(train_end), _time(calibration_end), _time(holdout_end)]
    if not endpoints[0] < endpoints[1] < endpoints[2]:
        raise ValueError("partition endpoints must be strictly increasing")
    if type(maturity_days) is not int or maturity_days < 1 or type(embargo_days) is not int or embargo_days < 0:
        raise ValueError("maturity_days must be positive and embargo_days nonnegative integers")
    if not rows:
        raise ValueError("research rows cannot be empty")
    names = ("train", "calibration", "holdout")
    assigned, memberships, excluded = [], defaultdict(set), Counter()
    seen = set()
    for raw in rows:
        row = dict(raw)
        customer = row.get("customer_id")
        if not isinstance(customer, str) or not customer:
            raise ValueError("customer_id must be a nonempty string")
        if type(row.get("label")) is not int or row["label"] not in (0, 1):
            raise ValueError("research label must be integer 0 or 1")
        cutoff = _time(row["as_of"])
        available = _time(row["feature_available_at"])
        observed = _time(row["outcome_observed_at"])
        outcome_available = _time(row["outcome_available_at"])
        if available > cutoff:
            raise ValueError("feature available after assessment cutoff: temporal leakage")
        if observed < cutoff or outcome_available < observed:
            raise ValueError("invalid outcome chronology")
        if (customer, cutoff) in seen:
            raise ValueError("duplicate customer assessment timestamp")
        seen.add((customer, cutoff))
        if not isinstance(row.get("features"), Mapping) or not row["features"]:
            raise ValueError("features must be a nonempty mapping")
        for name, value in row["features"].items():
            if not isinstance(name, str) or not name:
                raise ValueError("feature names must be nonempty strings")
            if value is not None:
                _number(value, f"feature {name}")
        if not isinstance(row.get("segment"), str) or not row["segment"]:
            raise ValueError("segment must be a nonempty string")
        partition = next((i for i, end in enumerate(endpoints) if cutoff < end), None)
        if partition is None:
            excluded["outside_observation_period"] += 1
            continue
        memberships[customer].add(partition)
        assigned.append((row, partition, cutoff, observed, outcome_available))
    crossing = {customer for customer, partitions in memberships.items() if len(partitions) > 1}
    partitions = {name: [] for name in names}
    for row, partition, cutoff, observed, outcome_available in assigned:
        if row["customer_id"] in crossing:
            excluded["customer_crosses_partitions"] += 1
        elif observed < cutoff + timedelta(days=maturity_days):
            excluded["insufficient_outcome_horizon"] += 1
        elif outcome_available > endpoints[partition]:
            excluded["outcome_unavailable_at_partition_cutoff"] += 1
        elif any(abs((cutoff - end).total_seconds()) < embargo_days * 86400 for end in endpoints[:2]):
            excluded["boundary_embargo"] += 1
        else:
            partitions[names[partition]].append(row)
    for name in names:
        partitions[name].sort(key=lambda row: (_time(row["as_of"]), row["customer_id"]))
    ids = {name: set(row["customer_id"] for row in partitions[name]) for name in names}
    assert all(not ids[a] & ids[b] for a, b in (("train", "calibration"), ("train", "holdout"),
                                             ("calibration", "holdout")))
    manifest = {"cutoffs": dict(zip(names, map(_stamp, endpoints))), "maturity_days": maturity_days,
                "embargo_days": embargo_days, "input_rows": len(rows), "excluded_rows": dict(excluded),
                "purged_customers": len(crossing), "row_counts": {k: len(v) for k, v in partitions.items()},
                "customer_counts": {k: len(v) for k, v in ids.items()},
                "positive_counts": {k: sum(row["label"] for row in v) for k, v in partitions.items()},
                "customer_overlap": 0,
                "rule": "all observations of any customer spanning time partitions are purged"}
    return {**partitions, "manifest": manifest}


def choose_threshold(y_true: Sequence[int], probabilities: Sequence[float], max_review_rate: float = 0.2,
                     false_negative_cost: float = 4.0, false_positive_cost: float = 1.0) -> dict:
    """Select a capacity-constrained empirical cost threshold on calibration data only."""
    binary_metrics(y_true, probabilities)
    capacity = _number(max_review_rate, "max_review_rate")
    fn_cost, fp_cost = _number(false_negative_cost, "false_negative_cost"), _number(false_positive_cost, "false_positive_cost")
    if not 0 <= capacity <= 1 or fn_cost < 0 or fp_cost < 0 or fn_cost + fp_cost == 0:
        raise ValueError("capacity must be in [0,1] and costs nonnegative with a positive total")
    # Threshold 1 supports reviewing nobody except predictions exactly equal to 1.
    candidates = sorted(set([0.0, 1.0, *probabilities]), reverse=True)
    by_probability = defaultdict(lambda: [0, 0])
    for label, probability in zip(y_true, probabilities):
        by_probability[probability][label] += 1
    positives, negatives = sum(y_true), len(y_true) - sum(y_true)
    tp = fp = 0
    feasible = []
    for threshold in candidates:
        new_negative, new_positive = by_probability[threshold]
        tp += new_positive
        fp += new_negative
        counts = {"tp": tp, "fp": fp, "fn": positives - tp, "tn": negatives - fp}
        reviewed = tp + fp
        if reviewed / len(y_true) <= capacity + 1e-12:
            cost = counts["fn"] * fn_cost + counts["fp"] * fp_cost
            feasible.append((cost, reviewed, -threshold, counts))
    if not feasible:
        raise ValueError("no threshold in [0,1] satisfies capacity; exact-one probabilities exceed capacity")
    cost, reviewed, negative_threshold, counts = min(feasible, key=lambda c: c[:3])
    return {"threshold": -negative_threshold, "calibration_cost": cost, "calibration_n": len(y_true),
            "calibration_review_rate": reviewed / len(y_true), "max_review_rate": capacity,
            "false_negative_cost": fn_cost, "false_positive_cost": fp_cost, "confusion": counts,
            "tie_break": "minimum cost, then fewer reviews, then higher threshold",
            "limitations": "illustrative capacity and costs; tied predictions are never split"}


def _research_dependencies():
    try:
        import numpy as np
        from sklearn.ensemble import HistGradientBoostingClassifier
        from sklearn.impute import SimpleImputer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
        from threadpoolctl import threadpool_limits
    except ImportError as exc:
        raise RuntimeError("Install customer-risk-workbench[research] to run supervised experiments") from exc
    return np, HistGradientBoostingClassifier, SimpleImputer, LogisticRegression, Pipeline, StandardScaler, threadpool_limits


def _matrix(rows: Sequence[Mapping], features: Sequence[str], np):
    if not rows:
        raise ValueError("each research partition must contain observations")
    result = []
    for row in rows:
        if set(row["features"]) != set(features):
            raise ValueError("feature names must exactly match the declared feature order")
        result.append([float("nan") if row["features"][name] is None else
                       _number(row["features"][name], name) for name in features])
    return np.asarray(result, dtype=float)


def _json_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def predict_logistic_json(model: Mapping, feature_rows: Sequence[Mapping]) -> list[float]:
    """Score inspectable JSON coefficients with exact trained feature ordering; no pickle loader."""
    if model.get("format") != "crw-logistic-json-v1":
        raise ValueError("unsupported numeric model format")
    names = model["feature_order"]
    indicators = model["missing_indicator_indices"]
    medians, means, scales = model["imputation_medians"], model["scaler_mean"], model["scaler_scale"]
    coefficients = model["coefficients"]
    if (not names or len(names) != len(set(names)) or len(medians) != len(names)
            or any(type(i) is not int or i < 0 or i >= len(names) for i in indicators)
            or len(indicators) != len(set(indicators))
            or len(means) != len(names) + len(indicators) or len(scales) != len(means)
            or len(coefficients) != len(means)):
        raise ValueError("inconsistent model dimensions")
    for value in [*medians, *means, *scales, *coefficients, model["intercept"]]:
        _number(value, "model coefficient")
    if any(scale <= 0 for scale in scales):
        raise ValueError("scaler scales must be positive")
    result = []
    for row in feature_rows:
        if set(row) != set(names):
            raise ValueError("feature names must exactly match model feature order")
        missing = [row[name] is None for name in names]
        values = [medians[i] if missing[i] else _number(row[name], name) for i, name in enumerate(names)]
        values += [float(missing[i]) for i in indicators]
        log_odds = model["intercept"] + sum(coef * (value - center) / scale
                                          for coef, value, center, scale in zip(coefficients, values, means, scales))
        result.append(_sigmoid(log_odds))
    return result


def evaluate_frozen_stress(predict: Callable[[list[dict]], Sequence[float]], rows: Sequence[Mapping],
                           training_metadata: Mapping, threshold_selection: Mapping,
                           scenarios: Sequence[Mapping], seed: int = 7) -> dict:
    """Evaluate a fixed predictor and threshold on paired, declared holdout interventions.

    Feature interventions retain baseline labels; these are measurement/input
    sensitivity experiments, not causal outcome simulations. Labels can also be
    independently corrupted to examine evaluation sensitivity to outcome error.
    """
    if not rows or not scenarios:
        raise ValueError("frozen stress requires observations and scenarios")
    identities = [row["customer_id"] for row in rows]
    if any(not isinstance(identifier, str) or not identifier for identifier in identities) or len(set(identities)) != len(rows):
        raise ValueError("frozen stress requires one observation per unique customer ID")
    feature_rows = [dict(row["features"]) for row in rows]
    feature_names = set(feature_rows[0])
    if not feature_names or any(set(row) != feature_names for row in feature_rows):
        raise ValueError("all frozen-stress records must have identical declared feature names")
    for row in feature_rows:
        for value in row.values():
            if value is not None:
                _number(value, "stress feature")
    labels = [row["label"] for row in rows]
    threshold = threshold_selection["threshold"]
    metadata_before = _json_digest(training_metadata)
    threshold_before = _json_digest(threshold_selection)
    source_before = _json_digest(rows)
    predictions = list(predict(deepcopy(feature_rows)))
    baseline = binary_metrics(labels, predictions, threshold)
    cases, seen_names = [], set()
    for raw_specification in scenarios:
        specification = deepcopy(dict(raw_specification))
        allowed = {"name", "feature_offsets", "clip_bounds", "mask_features", "mask_probability", "label_noise"}
        if set(specification) - allowed:
            raise ValueError("unknown frozen stress scenario fields")
        name = specification.get("name")
        if not isinstance(name, str) or not name or name in seen_names:
            raise ValueError("stress scenario names must be unique nonempty strings")
        seen_names.add(name)
        offsets = specification.get("feature_offsets", {})
        bounds = specification.get("clip_bounds", {})
        masks = specification.get("mask_features", [])
        mask_probability = _number(specification.get("mask_probability", 1.0), "mask_probability")
        noise = _number(specification.get("label_noise", 0.0), "label_noise")
        if not isinstance(offsets, Mapping) or not isinstance(bounds, Mapping) or not isinstance(masks, list):
            raise ValueError("feature_offsets/clip_bounds must be mappings and mask_features a list")
        if set(offsets) - feature_names or set(masks) - feature_names or set(bounds) - set(offsets):
            raise ValueError("interventions must reference declared features; bounds require an offset")
        if len(masks) != len(set(masks)) or not 0 <= noise <= 1 or not 0 <= mask_probability <= 1:
            raise ValueError("mask features must be unique; noise and masking probabilities must be in [0,1]")
        for feature, delta in offsets.items():
            _number(delta, f"offset {feature}")
            if feature in bounds:
                limits = bounds[feature]
                if not isinstance(limits, (list, tuple)) or len(limits) != 2:
                    raise ValueError("clip bounds must contain two finite increasing values")
                if _number(limits[0], "lower bound") >= _number(limits[1], "upper bound"):
                    raise ValueError("clip bounds must be increasing")
        derived_seed = int(hashlib.sha256(f"{seed}:{name}".encode()).hexdigest()[:16], 16)
        mask_rng = random.Random(derived_seed)
        label_rng = random.Random(derived_seed ^ 0x5A17)
        changed_features, changed_labels = deepcopy(feature_rows), list(labels)
        changed_cells = flips = 0
        for index, features in enumerate(changed_features):
            for feature, delta in offsets.items():
                if features[feature] is not None:
                    value = features[feature] + delta
                    if feature in bounds:
                        value = min(bounds[feature][1], max(bounds[feature][0], value))
                    features[feature] = _number(value, "perturbed feature")
            for feature in masks:
                if mask_rng.random() < mask_probability:
                    features[feature] = None
            changed_cells += sum(features[key] != feature_rows[index][key] for key in feature_names)
            if label_rng.random() < noise:
                changed_labels[index] = 1 - changed_labels[index]
                flips += 1
        stressed_probabilities = list(predict(deepcopy(changed_features)))
        metrics = binary_metrics(changed_labels, stressed_probabilities, threshold)
        deltas = {}
        for metric in ("roc_auc", "average_precision", "brier", "log_loss", "recall", "precision", "review_rate"):
            first, second = baseline[metric]["value"], metrics[metric]["value"]
            deltas[metric] = {"value": second - first if first is not None and second is not None else None,
                              "reason": None if first is not None and second is not None
                              else "baseline or stressed metric is undefined"}
        paired_changes = [abs(a - b) for a, b in zip(predictions, stressed_probabilities)]
        before_count = baseline["confusion"]["tp"] + baseline["confusion"]["fp"]
        after_count = metrics["confusion"]["tp"] + metrics["confusion"]["fp"]
        cases.append({"name": name, "specification": specification, "intervention_seed": derived_seed,
                      "metrics": metrics, "metric_deltas": deltas,
                      "workload": {"baseline_review_count": before_count, "stressed_review_count": after_count,
                                   "review_count_delta": after_count - before_count,
                                   "baseline_review_rate": baseline["review_rate"]["value"],
                                   "stressed_review_rate": metrics["review_rate"]["value"]},
                      "paired_changes": {"changed_feature_cells": changed_cells, "label_flips": flips,
                                         "observed_label_flip_rate": flips / len(rows),
                                         "mean_absolute_probability_change": mean(paired_changes),
                                         "maximum_absolute_probability_change": max(paired_changes)},
                      "probabilities_in_customer_order": stressed_probabilities,
                      "labels_in_customer_order": changed_labels,
                      "customer_order_sha256": _json_digest(identities),
                      "interpretation": "fixed-label input sensitivity and/or independently randomized label corruption; not causal"})
    metadata_after, threshold_after, source_after = (_json_digest(training_metadata), _json_digest(threshold_selection),
                                                    _json_digest(rows))
    if metadata_before != metadata_after or threshold_before != threshold_after or source_before != source_after:
        raise RuntimeError("frozen evaluation mutated metadata, threshold selection or source observations")
    return {"customer_ids": identities, "customer_order_sha256": _json_digest(identities), "n": len(rows),
            "baseline_metrics": baseline, "baseline_probabilities": predictions, "baseline_labels": labels,
            "threshold": threshold, "scenarios": cases,
            "integrity": {"training_data_sha256": training_metadata.get("training_data_sha256"),
                          "training_metadata_sha256_before": metadata_before,
                          "training_metadata_sha256_after": metadata_after,
                          "threshold_selection_sha256_before": threshold_before,
                          "threshold_selection_sha256_after": threshold_after,
                          "source_rows_sha256_before": source_before, "source_rows_sha256_after": source_after,
                          "preprocessing_refit": False, "model_refit": False, "threshold_reselected": False},
            "limitations": ["Predictor fitting is the caller's responsibility; this evaluator invokes prediction only.",
                            "Feature offsets retain original outcomes and do not simulate causal outcome changes.",
                            "Label corruption represents a measurement-error sensitivity, not a changed crime process.",
                            "All scenarios reuse the same holdout and are descriptive, without multiple-testing claims."]}


def fit_challengers(partitions: Mapping, feature_order: Sequence[str] = FEATURE_ORDER,
                    seed: int = 7, max_review_rate: float = 0.2, include_tree: bool = True,
                    monotonic_constraints: Mapping[str, int] | None = None,
                    bootstrap_repetitions: int = 200, include_frozen_stress: bool = True) -> dict:
    """Fit fixed challenger specifications; holdout labels are used solely for final diagnostics."""
    np, HGB, Imputer, Logistic, Pipeline, Scaler, threadpool_limits = _research_dependencies()
    names = list(feature_order)
    if not names or len(names) != len(set(names)) or any(not isinstance(name, str) or not name for name in names):
        raise ValueError("feature_order must contain unique nonempty names")
    train, calibration, holdout = (partitions[key] for key in ("train", "calibration", "holdout"))
    # Revalidate chronology and partition membership: arbitrary caller-supplied lists are not trusted.
    manifest = partitions["manifest"]
    rebuilt = temporal_entity_split([*train, *calibration, *holdout], **{
        "train_end": manifest["cutoffs"]["train"], "calibration_end": manifest["cutoffs"]["calibration"],
        "holdout_end": manifest["cutoffs"]["holdout"], "maturity_days": manifest["maturity_days"],
        "embargo_days": manifest["embargo_days"]})
    for key in ("train", "calibration", "holdout"):
        supplied = sorted((_time(row["as_of"]), row["customer_id"]) for row in partitions[key])
        reconstructed = sorted((_time(row["as_of"]), row["customer_id"]) for row in rebuilt[key])
        if supplied != reconstructed:
            raise ValueError("provided partitions violate temporal or customer separation")
    x_train, x_cal, x_hold = (_matrix(rows, names, np) for rows in (train, calibration, holdout))
    y_train, y_cal, y_hold = ([row["label"] for row in rows] for rows in (train, calibration, holdout))
    if any(set(y) != {0, 1} for y in (y_train, y_cal, y_hold)):
        raise ValueError("both outcome classes are required in every experiment partition")
    if any(len({row["customer_id"] for row in rows}) != len(rows) for rows in (train, calibration, holdout)):
        raise ValueError("fit_challengers requires one assessment per customer; select an anchor before fitting")
    constraint_map = dict(monotonic_constraints or {})
    if set(constraint_map) - set(names) or any(type(v) is not int or v not in (-1, 0, 1) for v in constraint_map.values()):
        raise ValueError("monotonic constraints must map declared features to integer -1, 0 or 1")
    logistic = Pipeline([("imputer", Imputer(strategy="median", add_indicator=True, keep_empty_features=True)),
                         ("scaler", Scaler()), ("classifier", Logistic(C=1.0, solver="lbfgs", max_iter=1000,
                                                                      random_state=seed))])
    prevalence = mean(y_train)
    models, results = {"logistic": logistic}, {}
    if include_tree:
        models["hist_gradient_boosting"] = HGB(max_iter=100, learning_rate=0.07, max_leaf_nodes=15,
                                              min_samples_leaf=25, l2_regularization=1.0, early_stopping=False,
                                              monotonic_cst=[constraint_map.get(name, 0) for name in names],
                                              random_state=seed)
    version_info = {package: version(package) for package in ("numpy", "scipy", "scikit-learn", "threadpoolctl")}
    baseline_cal = [prevalence] * len(y_cal)
    baseline_hold = [prevalence] * len(y_hold)
    baseline_threshold = choose_threshold(y_cal, baseline_cal, max_review_rate)
    results["prevalence_baseline"] = {
        "threshold_selection": baseline_threshold,
        "holdout_metrics": binary_metrics(y_hold, baseline_hold, baseline_threshold["threshold"]),
        "metadata": {"training_prevalence": prevalence, "fit_partition": "train",
                     "training_data_sha256": _json_digest(train)}}
    logistic_export, hold_predictions = None, {}
    with threadpool_limits(limits=1):
        for name, model in models.items():
            model.fit(x_train, y_train)
            cal_prob = model.predict_proba(x_cal)[:, 1].tolist()
            hold_prob = model.predict_proba(x_hold)[:, 1].tolist()
            threshold = choose_threshold(y_cal, cal_prob, max_review_rate)
            metadata = {"model": name, "feature_order": names, "seed": seed, "versions": version_info,
                        "python": platform.python_version(), "fit_partition": "train",
                        "threshold_partition": "calibration", "evaluation_partition": "holdout",
                        "hyperparameters_predeclared": True, "probability_recalibration": "none",
                        "training_rows": len(train), "training_data_sha256": _json_digest(train),
                        "limitations": LIMITATIONS}
            if name == "logistic":
                imputer, scaler, classifier = (model.named_steps[k] for k in ("imputer", "scaler", "classifier"))
                iterations = int(max(classifier.n_iter_))
                if iterations >= classifier.max_iter:
                    raise RuntimeError("logistic solver reached iteration cap; experiment is not accepted")
                logistic_export = {"format": "crw-logistic-json-v1", "feature_order": names,
                                   "missing_indicator_indices": imputer.indicator_.features_.tolist(),
                                   "transformed_feature_order": imputer.get_feature_names_out(names).tolist(),
                                   "imputation_medians": imputer.statistics_.tolist(),
                                   "scaler_mean": scaler.mean_.tolist(), "scaler_scale": scaler.scale_.tolist(),
                                   "coefficients": classifier.coef_[0].tolist(), "intercept": float(classifier.intercept_[0]),
                                   "selected_threshold": threshold["threshold"], "metadata": metadata}
                replay = predict_logistic_json(logistic_export, [row["features"] for row in holdout])
                replay_error = max(abs(a - b) for a, b in zip(replay, hold_prob))
                if replay_error > 1e-12:
                    raise RuntimeError("numeric JSON replay differs from fitted pipeline")
                metadata.update({"solver_iterations": iterations, "max_json_replay_absolute_error": replay_error,
                                 "hyperparameters": {"C": 1.0, "solver": "lbfgs", "max_iter": 1000}})
            else:
                metadata.update({"monotonic_constraints": constraint_map, "artifact": "metadata only; refit from seeds",
                                 "hyperparameters": {"max_iter": 100, "learning_rate": 0.07, "max_leaf_nodes": 15,
                                                     "min_samples_leaf": 25, "l2_regularization": 1.0,
                                                     "early_stopping": False}})
                monotonic_probes = []
                for feature, direction in constraint_map.items():
                    if direction == 0:
                        continue
                    index = names.index(feature)
                    observed_values = x_train[:, index][~np.isnan(x_train[:, index])]
                    if not len(observed_values):
                        monotonic_probes.append({"feature": feature, "direction": direction,
                                                 "status": "no numeric training support", "tested_pairs": 0,
                                                 "violations": None})
                        continue
                    grid = np.linspace(float(observed_values.min()), float(observed_values.max()), 11)
                    tested_pairs = violations = 0
                    for anchor in x_hold[:25]:
                        probe = np.tile(anchor, (len(grid), 1))
                        probe[:, index] = grid
                        predictions = model.predict_proba(probe)[:, 1]
                        differences = direction * np.diff(predictions)
                        tested_pairs += len(differences)
                        violations += int(np.sum(differences < -1e-12))
                    monotonic_probes.append({"feature": feature, "direction": direction, "status": "grid_probe",
                                             "tested_pairs": tested_pairs, "violations": violations,
                                             "grid": grid.tolist()})
                metadata["monotonic_probes"] = monotonic_probes
                metadata["monotonic_probe_limit"] = "finite grids at up to 25 holdout anchors; not exhaustive proof"
            results[name] = {"metadata": metadata, "threshold_selection": threshold,
                             "holdout_metrics": binary_metrics(y_hold, hold_prob, threshold["threshold"]),
                             "holdout_calibration": calibration_bins(y_hold, hold_prob),
                             "holdout_segments": segment_metrics(y_hold, hold_prob, [r["segment"] for r in holdout],
                                                                 threshold["threshold"]),
                             "brier_delta_vs_prevalence": paired_bootstrap_delta(
                                 y_hold, baseline_hold, hold_prob, metric="brier", repetitions=bootstrap_repetitions,
                                 seed=seed, groups=[r["customer_id"] for r in holdout])}
            hold_predictions[name] = hold_prob
    if include_tree:
        results["hist_gradient_boosting"]["auc_delta_vs_logistic"] = paired_bootstrap_delta(
            y_hold, hold_predictions["logistic"], hold_predictions["hist_gradient_boosting"],
            repetitions=bootstrap_repetitions, seed=seed, groups=[r["customer_id"] for r in holdout])
    importance = permutation_importance(lambda rows: predict_logistic_json(logistic_export, rows),
                                        [r["features"] for r in holdout], y_hold, metric="brier", repetitions=5, seed=seed)
    for result in results.values():
        observed_rate = result["holdout_metrics"]["review_rate"]["value"]
        result["holdout_capacity_diagnostic"] = {
            "observed_review_rate": observed_rate, "calibration_capacity_target": max_review_rate,
            "exceeds_target": observed_rate > max_review_rate + 1e-12,
            "excess_rate": max(0.0, observed_rate - max_review_rate),
            "interpretation": "a frozen calibration threshold does not guarantee capacity in a later population"}
    frozen_results = {}
    if include_frozen_stress:
        stress_scenarios = [{"name": "zero_intervention"}, {"name": "label_noise_15pct", "label_noise": 0.15}]
        mask_features = [feature for feature in ("velocity_change", "flow_through") if feature in names]
        if mask_features:
            stress_scenarios.append({"name": "missing_behavior_features", "mask_features": mask_features})
        if "jurisdiction_exposure" in names:
            stress_scenarios.append({"name": "jurisdiction_input_shift", "feature_offsets": {"jurisdiction_exposure": 0.25},
                                     "clip_bounds": {"jurisdiction_exposure": [0.0, 1.0]}})
        artifact_before = _json_digest(logistic_export)
        with threadpool_limits(limits=1):
            for name, result in results.items():
                if name == "prevalence_baseline":
                    def predictor(rows, fixed_prevalence=prevalence):
                        return [fixed_prevalence] * len(rows)
                elif name == "logistic":
                    def predictor(rows, fixed_model=logistic_export):
                        return predict_logistic_json(fixed_model, rows)
                else:
                    def predictor(rows, fitted_model=models[name]):
                        return fitted_model.predict_proba(_matrix([{"features": row} for row in rows], names, np))[:, 1].tolist()
                frozen_results[name] = evaluate_frozen_stress(predictor, holdout, result["metadata"],
                                                              result["threshold_selection"], stress_scenarios, seed=seed)
        if _json_digest(logistic_export) != artifact_before:
            raise RuntimeError("frozen stress changed the numeric logistic model")
        frozen_results["logistic"]["integrity"]["numeric_model_sha256_before"] = artifact_before
        frozen_results["logistic"]["integrity"]["numeric_model_sha256_after"] = _json_digest(logistic_export)
    return {"models": results, "logistic_model_json": logistic_export, "logistic_permutation_importance": importance,
            "frozen_model_stress": frozen_results, "split": manifest, "limitations": LIMITATIONS}


def run_research_experiment(n: int = 3000, seeds: Sequence[int] = (7, 19, 41),
                            include_stress: bool = True, include_tree: bool = True,
                            bootstrap_repetitions: int = 200) -> dict:
    """Reproducible multi-seed experiment plus refitted label-noise/prevalence sensitivity."""
    if type(n) is not int or n < 300:
        raise ValueError("n must be an integer >=300; small partitions may still lack class support")
    if not seeds or len(seeds) != len(set(seeds)) or any(type(seed) is not int for seed in seeds):
        raise ValueError("seeds must be a nonempty unique sequence of integers")
    regimes = [("base", 0.0, 0.0)]
    if include_stress:
        regimes.extend([("label_noise_15pct", 0.15, 0.0), ("lower_prevalence", 0.0, -1.0),
                        ("higher_prevalence", 0.0, 1.0)])
    experiments = []
    for regime, noise, shift in regimes:
        for seed in seeds:
            rows = generate_research_rows(n, seed, noise, shift)
            partitions = temporal_entity_split(rows, "2024-07-01T00:00:00Z", "2024-10-01T00:00:00Z",
                                               "2025-02-15T00:00:00Z", embargo_days=7)
            experiment = fit_challengers(partitions, seed=seed, include_tree=include_tree,
                                         bootstrap_repetitions=bootstrap_repetitions,
                                         monotonic_constraints={"jurisdiction_exposure": 1, "ownership_opacity": 1},
                                         include_frozen_stress=regime == "base")
            experiments.append({"regime": regime, "seed": seed, "generator": {"customers": n,
                                "label_noise": noise, "prevalence_log_odds_shift": shift}, **experiment})
    summary = []
    for regime, _, _ in regimes:
        members = [row for row in experiments if row["regime"] == regime]
        for model in members[0]["models"]:
            metrics = {}
            for metric in ("roc_auc", "average_precision", "brier", "log_loss", "recall", "precision", "review_rate"):
                values = [member["models"][model]["holdout_metrics"][metric]["value"] for member in members]
                defined = [value for value in values if value is not None]
                metrics[metric] = {"mean": mean(defined) if defined else None,
                                   "minimum": min(defined) if defined else None,
                                   "maximum": max(defined) if defined else None,
                                   "defined_seed_count": len(defined), "seed_count": len(values)}
            summary.append({"regime": regime, "model": model, "metrics": metrics})
    report = {"schema_version": "crw-research-report-v1", "data_status": "synthetic_only",
              "generator": "latent-variable stochastic measurement/outcome process; independent of policy scoring",
              "seeds": list(seeds), "customers_per_experiment": n, "experiments": experiments, "summary": summary,
              "stress_design": "each regime refits from scratch; not an unchanged-model deployment stress test",
              "frozen_model_stress": [{"seed": e["seed"], "models": e["frozen_model_stress"]}
                                      for e in experiments if e["regime"] == "base"],
              "limitations": LIMITATIONS + ["Seed ranges are descriptive and are not confidence intervals.",
                                              "No model is selected as a winner from holdout results."]}
    json.dumps(report, allow_nan=False)
    return report
