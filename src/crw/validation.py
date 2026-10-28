"""Dependency-free diagnostics with explicit denominators and undefined values.

An outcome probability is required for probability metrics. A policy risk index
must not be divided by 100 and silently relabeled as a calibrated probability.
"""
from __future__ import annotations

from bisect import bisect_right
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
import math
import random
from statistics import NormalDist, mean, median, variance
from typing import Any


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


def _integer(value: Any, name: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def _level(confidence: float) -> float:
    confidence = _finite(confidence, "confidence")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be in (0,1)")
    return confidence


def _metric(value: float | None, reason: str | None = None) -> dict:
    return {"value": value, "reason": reason}


def _ratio(numerator: float, denominator: float, reason: str) -> dict:
    return _metric(numerator / denominator) if denominator else _metric(None, reason)


def _vectors(y_true: Sequence[int], scores: Sequence[float], probability: bool = False) -> tuple[list, list]:
    if len(y_true) != len(scores) or not len(y_true):
        raise ValueError("labels and scores must have equal nonzero lengths")
    labels = list(y_true)
    if any(type(y) is not int or y not in (0, 1) for y in labels):
        raise ValueError("labels must be integer 0 or 1")
    values = [_finite(p, "score") for p in scores]
    if probability and any(p < 0 or p > 1 for p in values):
        raise ValueError("probabilities must be in [0,1]")
    return labels, values


def roc_auc(y_true: Sequence[int], scores: Sequence[float]) -> dict:
    """Pairwise concordance probability, granting exactly half credit to ties."""
    labels, values = _vectors(y_true, scores)
    positives = sum(labels)
    negatives = len(labels) - positives
    if not positives or not negatives:
        return _metric(None, "requires both outcome classes")
    groups: dict[float, list[int]] = defaultdict(lambda: [0, 0])
    for y, score in zip(labels, values):
        groups[score][y] += 1
    negatives_below, concordance = 0, 0.0
    for value in sorted(groups):
        neg, pos = groups[value]
        concordance += pos * (negatives_below + neg / 2)
        negatives_below += neg
    return _metric(concordance / (positives * negatives))


def average_precision(y_true: Sequence[int], scores: Sequence[float]) -> dict:
    """Non-interpolated precision-recall area; tied predictions enter together."""
    labels, values = _vectors(y_true, scores)
    positives = sum(labels)
    if not positives:
        return _metric(None, "requires at least one positive outcome")
    groups: dict[float, list[int]] = defaultdict(lambda: [0, 0])
    for y, score in zip(labels, values):
        groups[score][y] += 1
    seen, true_positive, area = 0, 0, 0.0
    for value in sorted(groups, reverse=True):
        neg, pos = groups[value]
        seen += neg + pos
        true_positive += pos
        area += (pos / positives) * (true_positive / seen)
    return _metric(area)


def wilson_interval(successes: int, n: int, confidence: float = 0.95) -> dict:
    """Two-sided Wilson score interval for independent Bernoulli observations."""
    _integer(n, "n")
    _integer(successes, "successes")
    confidence = _level(confidence)
    if successes > n:
        raise ValueError("successes cannot exceed n")
    if not n:
        return {"lower": None, "upper": None, "reason": "no observations", "n": 0,
                "successes": 0, "confidence": confidence, "method": "wilson"}
    z = -NormalDist().inv_cdf((1 - confidence) / 2)
    p, z2 = successes / n, z * z
    center = (p + z2 / (2 * n)) / (1 + z2 / n)
    radius = z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / (1 + z2 / n)
    return {"lower": max(0.0, center - radius), "upper": min(1.0, center + radius),
            "reason": None, "n": n, "successes": successes, "confidence": confidence, "method": "wilson"}


def calibration_bins(y_true: Sequence[int], probabilities: Sequence[float], n_bins: int = 10) -> dict:
    labels, values = _vectors(y_true, probabilities, probability=True)
    _integer(n_bins, "n_bins", 1)
    bins = [[] for _ in range(n_bins)]
    for y, p in zip(labels, values):
        bins[min(int(p * n_bins), n_bins - 1)].append((y, p))
    result, ece = [], 0.0
    for i, pairs in enumerate(bins):
        n = len(pairs)
        observed = sum(y for y, _ in pairs) / n if n else None
        predicted = sum(p for _, p in pairs) / n if n else None
        if n:
            ece += n / len(labels) * abs(observed - predicted)
        result.append({"lower": i / n_bins, "upper": (i + 1) / n_bins,
                       "upper_inclusive": i == n_bins - 1, "n": n,
                       "mean_probability": predicted, "outcome_rate": observed,
                       "outcome_rate_interval": wilson_interval(sum(y for y, _ in pairs), n)})
    return {"bins": result, "expected_calibration_error": ece, "n": len(labels),
            "method": "equal-width; ECE depends on binning and is not a standalone calibration test"}


def binary_metrics(y_true: Sequence[int], probabilities: Sequence[float], threshold: float = 0.5) -> dict:
    labels, values = _vectors(y_true, probabilities, probability=True)
    threshold = _finite(threshold, "threshold")
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be in [0,1]")
    counts = Counter((y, int(p >= threshold)) for y, p in zip(labels, values))
    tn, fp, fn, tp = (counts[k] for k in ((0, 0), (0, 1), (1, 0), (1, 1)))
    n = len(labels)
    impossible = any((y == 1 and p == 0) or (y == 0 and p == 1) for y, p in zip(labels, values))
    loss = None if impossible else -sum(math.log(p) if y else math.log1p(-p)
                                       for y, p in zip(labels, values)) / n
    return {"n": n, "positives": tp + fn, "negatives": tn + fp, "threshold": threshold,
            "prevalence": (tp + fn) / n, "confusion": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
            "roc_auc": roc_auc(labels, values), "average_precision": average_precision(labels, values),
            "brier": _metric(sum((p - y) ** 2 for y, p in zip(labels, values)) / n),
            "log_loss": _metric(loss, "infinite: certainty assigned to an incorrect outcome" if impossible else None),
            "accuracy": _ratio(tp + tn, n, "no observations"),
            "precision": _ratio(tp, tp + fp, "no predicted positives"),
            "recall": _ratio(tp, tp + fn, "no observed positives"),
            "specificity": _ratio(tn, tn + fp, "no observed negatives"),
            "false_positive_rate": _ratio(fp, fp + tn, "no observed negatives"),
            "negative_predictive_value": _ratio(tn, tn + fn, "no predicted negatives"),
            "f1": _ratio(2 * tp, 2 * tp + fp + fn, "no observed or predicted positives"),
            "review_rate": _metric((tp + fp) / n),
            "recall_interval": wilson_interval(tp, tp + fn),
            "precision_interval": wilson_interval(tp, tp + fp)}


def proportion_sample_size(margin: float, confidence: float = 0.95,
                           population_size: int | None = None, assumed_proportion: float = 0.5) -> dict:
    """Normal-approximation planning with optional finite-population correction."""
    margin = _finite(margin, "margin")
    p = _finite(assumed_proportion, "assumed_proportion")
    confidence = _level(confidence)
    if not 0 < margin < 1 or not 0 < p < 1:
        raise ValueError("margin and assumed_proportion must be in (0,1)")
    if population_size is not None:
        _integer(population_size, "population_size", 1)
    z = -NormalDist().inv_cdf((1 - confidence) / 2)
    n0 = z * z * p * (1 - p) / (margin * margin)
    corrected = n0 if population_size is None else population_size * n0 / (population_size - 1 + n0)
    return {"sample_size": max(1, math.ceil(corrected)), "unrounded": corrected,
            "infinite_population_unrounded": n0, "population_size": population_size,
            "margin": margin, "confidence": confidence, "assumed_proportion": p,
            "method": "normal approximation; simple random sampling without replacement",
            "limitations": "not an event-count, power, clustering, bias, or model-validation guarantee"}


def zero_failure_upper_bound(n: int, confidence: float = 0.95) -> dict:
    _integer(n, "n", 1)
    confidence = _level(confidence)
    return {"upper": -math.expm1(math.log1p(-confidence) / n), "lower": 0.0, "n": n,
            "confidence": confidence, "method": "exact one-sided binomial; zero observed failures"}


def zero_failure_sample_size(maximum_rate: float, confidence: float = 0.95) -> dict:
    rate = _finite(maximum_rate, "maximum_rate")
    confidence = _level(confidence)
    if not 0 < rate < 1:
        raise ValueError("maximum_rate must be in (0,1)")
    n = math.ceil(math.log1p(-confidence) / math.log1p(-rate))
    return {"sample_size": n, "maximum_rate": rate, "confidence": confidence,
            "assumption": "independent trials with zero observed failures"}


def stratified_sample(records: Sequence[Mapping], stratum_key: str, allocation: Mapping[str, int],
                      seed: int = 7, id_key: str = "customer_id") -> dict:
    """Reproducible SRS without replacement within every stratum; includes design weights."""
    if not records:
        raise ValueError("records cannot be empty")
    grouped: dict[str, list[dict]] = defaultdict(list)
    seen = set()
    for row in records:
        identifier, stratum = row.get(id_key), row.get(stratum_key)
        if not isinstance(identifier, str) or not identifier or identifier in seen:
            raise ValueError("sampling unit IDs must be unique nonempty strings")
        if not isinstance(stratum, str) or not stratum:
            raise ValueError("strata must be nonempty strings")
        seen.add(identifier)
        grouped[stratum].append(dict(row))
    if set(grouped) != set(allocation):
        raise ValueError("allocation must include every stratum exactly once")
    rng, selected, design = random.Random(seed), [], []
    for stratum in sorted(grouped):
        population = sorted(grouped[stratum], key=lambda row: row[id_key])
        count = _integer(allocation[stratum], "allocation", 1)
        if count > len(population):
            raise ValueError("allocation cannot exceed stratum population")
        probability = count / len(population)
        chosen = sorted(rng.sample(population, count), key=lambda row: row[id_key])
        design.append({"stratum": stratum, "population_size": len(population), "sample_size": count,
                       "inclusion_probability": probability, "weight": 1 / probability})
        selected.extend({"record": row, "stratum": stratum, "inclusion_probability": probability,
                         "weight": 1 / probability} for row in chosen)
    return {"sample": selected, "design": design, "seed": seed, "population_size": len(records),
            "sample_size": len(selected), "method": "stratified simple random sampling without replacement"}


def stratified_proportion(sample: Sequence[Mapping], population_sizes: Mapping[str, int],
                          outcome_key: str = "label", stratum_key: str = "segment") -> dict:
    """Design-weighted rate and SRS variance, including stratum finite-population corrections."""
    groups: dict[str, list[int]] = defaultdict(list)
    for row in sample:
        label = row.get(outcome_key)
        if type(label) is not int or label not in (0, 1):
            raise ValueError("sample outcomes must be integer 0 or 1")
        groups[row[stratum_key]].append(label)
    if set(groups) != set(population_sizes):
        raise ValueError("every population stratum must have sampled observations")
    for key, size in population_sizes.items():
        _integer(size, "stratum population size", 1)
        if len(groups[key]) > size:
            raise ValueError("sample exceeds stratum population")
    total = sum(population_sizes.values())
    if not total:
        raise ValueError("population cannot be empty")
    estimate, var = 0.0, 0.0
    variance_available = True
    for stratum, values in groups.items():
        n, population = len(values), population_sizes[stratum]
        weight = population / total
        estimate += weight * mean(values)
        if n == population:
            continue
        if n < 2:
            variance_available = False
        else:
            var += weight * weight * (1 - n / population) * variance(values) / n
    return {"estimate": estimate, "standard_error": math.sqrt(var) if variance_available else None,
            "reason": None if variance_available else "non-census stratum with fewer than two observations",
            "population_size": total, "sample_size": len(sample),
            "method": "stratum population-weighted estimator; design-based SRS variance"}


def _nullable_values(values: Sequence[float | None]) -> list[float | None]:
    if not len(values):
        raise ValueError("distribution must contain at least one observation")
    return [None if value is None else _finite(value, "distribution value") for value in values]


def _quantile(values: Sequence[float], q: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[min(lower + 1, len(ordered) - 1)] * fraction


def fit_reference_bins(reference: Sequence[float | None], n_bins: int = 10) -> dict:
    """Persist these bins; never refit quantiles to the comparison population."""
    values = _nullable_values(reference)
    _integer(n_bins, "n_bins", 1)
    numeric = [v for v in values if v is not None]
    boundaries = sorted(set(_quantile(numeric, i / n_bins) for i in range(n_bins + 1))) if numeric else []
    return {"boundaries": boundaries, "requested_interior_bins": n_bins,
            "reference_n": len(values), "reference_numeric_n": len(numeric),
            "method": "reference quantiles with separate underflow, overflow and missing bins"}


def _bin_counts(values: Sequence[float | None], boundaries: Sequence[float]) -> tuple[list[int], list[str]]:
    if not boundaries:
        return [sum(v is not None for v in values), sum(v is None for v in values)], ["numeric", "missing"]
    if len(boundaries) == 1:
        labels = ["below_reference", "equal_reference", "above_reference", "missing"]
    else:
        labels = ["below_reference"] + [f"interior_{i}" for i in range(len(boundaries) - 1)]
        labels += ["above_reference", "missing"]
    counts = [0] * len(labels)
    for value in values:
        if value is None:
            index = len(counts) - 1
        elif value < boundaries[0]:
            index = 0
        elif value > boundaries[-1]:
            index = len(counts) - 2
        elif len(boundaries) == 1:
            index = 1
        else:
            index = 1 + min(bisect_right(boundaries, value) - 1, len(boundaries) - 2)
        counts[index] += 1
    return counts, labels


def population_stability_index(reference: Sequence[float | None], current: Sequence[float | None],
                               reference_bins: Mapping | None = None, n_bins: int = 10,
                               pseudocount: float = 0.5) -> dict:
    baseline, comparison = _nullable_values(reference), _nullable_values(current)
    pseudocount = _finite(pseudocount, "pseudocount")
    if pseudocount <= 0:
        raise ValueError("pseudocount must be positive")
    spec = dict(reference_bins) if reference_bins is not None else fit_reference_bins(baseline, n_bins)
    boundaries = [_finite(v, "boundary") for v in spec["boundaries"]]
    if boundaries != sorted(set(boundaries)):
        raise ValueError("bin boundaries must be strictly increasing")
    expected, labels = _bin_counts(baseline, boundaries)
    observed, _ = _bin_counts(comparison, boundaries)
    k, result, total = len(expected), [], 0.0
    for label, a, b in zip(labels, expected, observed):
        p = (a + pseudocount) / (len(baseline) + k * pseudocount)
        q = (b + pseudocount) / (len(comparison) + k * pseudocount)
        contribution = (q - p) * math.log(q / p)
        total += contribution
        result.append({"bin": label, "reference_count": a, "current_count": b,
                       "reference_share": p, "current_share": q, "contribution": contribution})
    return {"value": total, "reference_n": len(baseline), "current_n": len(comparison),
            "bins": result, "bin_specification": spec, "pseudocount": pseudocount,
            "interpretation": "descriptive drift measure; no universal materiality or significance cutoff"}


def distribution_drift(reference: Sequence[float | None], current: Sequence[float | None]) -> dict:
    ref, cur = _nullable_values(reference), _nullable_values(current)
    a = sorted(v for v in ref if v is not None)
    b = sorted(v for v in cur if v is not None)
    report = {"reference_n": len(ref), "current_n": len(cur), "reference_numeric_n": len(a),
              "current_numeric_n": len(b), "reference_missing_rate": 1 - len(a) / len(ref),
              "current_missing_rate": 1 - len(b) / len(cur),
              "psi": population_stability_index(ref, cur),
              "limitations": "descriptive effects; no p-values, causality, or universal drift thresholds"}
    if not a or not b:
        report.update({key: _metric(None, "both populations require numeric observations")
                       for key in ("ks_statistic", "wasserstein_distance", "mean_difference",
                                   "median_difference", "standardized_mean_difference", "rank_biserial")})
        return report
    ia = ib = 0
    ks = wasserstein = 0.0
    previous = min(a[0], b[0])
    for value in sorted(set(a + b)):
        wasserstein += abs(ia / len(a) - ib / len(b)) * (value - previous)
        while ia < len(a) and a[ia] <= value:
            ia += 1
        while ib < len(b) and b[ib] <= value:
            ib += 1
        ks = max(ks, abs(ia / len(a) - ib / len(b)))
        previous = value
    difference = mean(b) - mean(a)
    degrees = len(a) + len(b) - 2
    pooled = (((len(a) - 1) * (variance(a) if len(a) > 1 else 0)
               + (len(b) - 1) * (variance(b) if len(b) > 1 else 0)) / degrees) if degrees else 0
    standardized = difference / math.sqrt(pooled) if pooled > 0 else (0.0 if difference == 0 else None)
    report.update({"ks_statistic": _metric(ks), "wasserstein_distance": _metric(wasserstein),
                   "mean_difference": _metric(difference), "median_difference": _metric(median(b) - median(a)),
                   "standardized_mean_difference": _metric(standardized, "zero pooled variation" if standardized is None else None),
                   "rank_biserial": _metric(2 * roc_auc([0] * len(a) + [1] * len(b), a + b)["value"] - 1)})
    return report


def migration_matrix(before: Sequence[str], after: Sequence[str], band_order: Sequence[str] | None = None) -> dict:
    if not len(before) or len(before) != len(after):
        raise ValueError("paired bands must have equal nonzero lengths")
    if any(not isinstance(value, str) or not value for value in list(before) + list(after)):
        raise ValueError("bands must be nonempty strings; use an explicit abstention label")
    observed = set(before) | set(after)
    bands = list(band_order) if band_order is not None else sorted(observed)
    if len(bands) != len(set(bands)) or not observed.issubset(bands):
        raise ValueError("band_order must uniquely include every observed band")
    lookup = {band: i for i, band in enumerate(bands)}
    counts = [[0 for _ in bands] for _ in bands]
    for old, new in zip(before, after):
        counts[lookup[old]][lookup[new]] += 1
    result = {"bands": bands, "counts": counts,
              "row_proportions": [[value / sum(row) if sum(row) else None for value in row] for row in counts],
              "n": len(before), "changed": sum(a != b for a, b in zip(before, after)),
              "direction_available": band_order is not None}
    if band_order is not None:
        result.update({"upward": sum(lookup[b] > lookup[a] for a, b in zip(before, after)),
                       "downward": sum(lookup[b] < lookup[a] for a, b in zip(before, after))})
    return result


def segment_metrics(y_true: Sequence[int], probabilities: Sequence[float], segments: Sequence[str],
                    threshold: float = 0.5, min_n: int = 50, min_events: int = 5) -> dict:
    labels, values = _vectors(y_true, probabilities, probability=True)
    threshold = _finite(threshold, "threshold")
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be in [0,1]")
    if len(segments) != len(labels) or any(not isinstance(s, str) or not s for s in segments):
        raise ValueError("one nonempty segment label is required for each observation")
    _integer(min_n, "min_n", 1)
    _integer(min_events, "min_events", 1)
    result = {}
    for segment in sorted(set(segments)):
        indices = [i for i, s in enumerate(segments) if s == segment]
        y, p = [labels[i] for i in indices], [values[i] for i in indices]
        supported = len(y) >= min_n and min(sum(y), len(y) - sum(y)) >= min_events
        result[segment] = {"n": len(y), "positives": sum(y), "negatives": len(y) - sum(y),
                           "status": "supported_for_descriptive_reporting" if supported else "insufficient_support",
                           "metrics": binary_metrics(y, p, threshold) if supported else None}
    return {"segments": result, "minimum_n": min_n, "minimum_each_class": min_events,
            "limitations": "support gates are illustrative; passing is not a fairness or validation finding"}


def _metric_value(y: Sequence[int], p: Sequence[float], metric: str) -> float | None:
    if metric not in {"roc_auc", "average_precision", "brier", "log_loss"}:
        raise ValueError("metric must be roc_auc, average_precision, brier, or log_loss")
    if metric == "roc_auc":
        return roc_auc(y, p)["value"]
    if metric == "average_precision":
        return average_precision(y, p)["value"]
    if metric == "brier":
        return sum((probability - label) ** 2 for label, probability in zip(y, p)) / len(y)
    if any((label == 1 and probability == 0) or (label == 0 and probability == 1)
           for label, probability in zip(y, p)):
        return None
    return -sum(math.log(probability) if label else math.log1p(-probability)
                for label, probability in zip(y, p)) / len(y)


def paired_bootstrap_delta(y_true: Sequence[int], first: Sequence[float], second: Sequence[float],
                           metric: str = "roc_auc", repetitions: int = 1000, seed: int = 7,
                           confidence: float = 0.95, groups: Sequence[str] | None = None) -> dict:
    labels, a = _vectors(y_true, first, probability=True)
    _, b = _vectors(y_true, second, probability=True)
    _integer(repetitions, "repetitions", 20)
    confidence = _level(confidence)
    if groups is not None and (len(groups) != len(labels)
                               or any(not isinstance(g, str) or not g for g in groups)):
        raise ValueError("groups must provide a nonempty string for each row")
    clusters: dict[Any, list[int]] = defaultdict(list)
    for i in range(len(labels)):
        clusters[groups[i] if groups is not None else i].append(i)
    keys = sorted(clusters)
    rng, deltas = random.Random(seed), []
    base_a, base_b = _metric_value(labels, a, metric), _metric_value(labels, b, metric)
    if base_a is not None and base_b is not None:
        for _ in range(repetitions):
            indices = [i for key in rng.choices(keys, k=len(keys)) for i in clusters[key]]
            sample_y = [labels[i] for i in indices]
            va = _metric_value(sample_y, [a[i] for i in indices], metric)
            vb = _metric_value(sample_y, [b[i] for i in indices], metric)
            if va is not None and vb is not None:
                deltas.append(vb - va)
    sufficient = len(deltas) >= math.ceil(0.9 * repetitions) and len(keys) >= 2
    alpha = (1 - confidence) / 2
    return {"metric": metric, "delta": base_b - base_a if base_a is not None and base_b is not None else None,
            "direction": "second minus first", "higher_is_better": metric in {"roc_auc", "average_precision"},
            "lower": _quantile(deltas, alpha) if sufficient else None,
            "upper": _quantile(deltas, 1 - alpha) if sufficient else None,
            "reason": None if sufficient else "fewer than 90% valid replicates or fewer than two sampling units",
            "confidence": confidence, "repetitions": repetitions, "valid_replicates": len(deltas),
            "skipped_replicates": repetitions - len(deltas), "seed": seed, "sampling_units": len(keys),
            "method": "paired cluster percentile bootstrap" if groups is not None else "paired IID percentile bootstrap",
            "limitations": "fixed fitted models; excludes training, label, temporal dependence and selection uncertainty"}


def sensitivity_analysis(predict: Callable[[dict], float], baseline: Mapping[str, float | None],
                         perturbations: Mapping[str, Sequence[float | None]]) -> dict:
    base = dict(baseline)
    original = _finite(predict(dict(base)), "prediction")
    result = {}
    for feature, values in perturbations.items():
        if feature not in base or not len(values):
            raise ValueError("every perturbed feature must exist and have test values")
        cases = []
        for value in values:
            if value is not None:
                _finite(value, "perturbation")
            changed = dict(base)
            changed[feature] = value
            predicted = _finite(predict(changed), "prediction")
            cases.append({"input": value, "output": predicted, "delta": predicted - original})
        numeric = sorted((c for c in cases if c["input"] is not None), key=lambda c: c["input"])
        result[feature] = {"cases": cases,
                           "nondecreasing_violations": sum(b["output"] < a["output"] - 1e-12
                                                           for a, b in zip(numeric, numeric[1:])),
                           "maximum_absolute_delta": max(abs(c["delta"]) for c in cases)}
    return {"baseline_output": original, "features": result,
            "limitations": "one-feature-at-a-time perturbations may be infeasible; not causal effects"}


def permutation_importance(predict: Callable[[list[dict]], Sequence[float]], rows: Sequence[Mapping],
                           y_true: Sequence[int], features: Sequence[str] | None = None,
                           metric: str = "brier", repetitions: int = 10, seed: int = 7) -> dict:
    if not rows:
        raise ValueError("rows cannot be empty")
    _integer(repetitions, "repetitions", 1)
    baseline_rows = [dict(row) for row in rows]
    labels, scores = _vectors(y_true, predict([dict(r) for r in baseline_rows]), probability=True)
    selected = list(features) if features is not None else sorted(baseline_rows[0])
    if len(selected) != len(set(selected)) or any(f not in row for f in selected for row in rows):
        raise ValueError("permuted features must be unique and present in every row")
    baseline = _metric_value(labels, scores, metric)
    rng, result = random.Random(seed), {}
    for feature in selected:
        changes = []
        for _ in range(repetitions):
            column = [row[feature] for row in baseline_rows]
            rng.shuffle(column)
            changed = [dict(row, **{feature: value}) for row, value in zip(baseline_rows, column)]
            _, probabilities = _vectors(labels, predict(changed), probability=True)
            value = _metric_value(labels, probabilities, metric)
            if value is not None and baseline is not None:
                changes.append((baseline - value) if metric in {"roc_auc", "average_precision"} else value - baseline)
        result[feature] = {"mean_degradation": mean(changes) if changes else None,
                           "repeat_deltas": changes, "valid_repetitions": len(changes)}
    return {"metric": metric, "baseline": baseline, "features": result, "seed": seed,
            "repetitions": repetitions, "limitations": "marginal shuffling breaks dependence; not causal importance"}
