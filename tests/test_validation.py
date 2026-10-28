import math

import pytest
from hypothesis import given, strategies as st

from crw.validation import (
    average_precision, binary_metrics, calibration_bins, distribution_drift,
    fit_reference_bins, migration_matrix, paired_bootstrap_delta, permutation_importance,
    population_stability_index, proportion_sample_size, roc_auc, segment_metrics,
    sensitivity_analysis, stratified_proportion, stratified_sample, wilson_interval,
    zero_failure_sample_size, zero_failure_upper_bound,
)


def test_auc_pairwise_ties_and_order_invariance():
    y, p = [1, 0, 1, 0], [0.7, 0.7, 0.9, 0.1]
    # Positive .7 beats .1 and ties .7; positive .9 beats both negatives: 3.5 / 4.
    assert roc_auc(y, p)["value"] == 0.875
    assert roc_auc(y[::-1], p[::-1]) == roc_auc(y, p)
    assert roc_auc([1, 0], [2.0, 2.0])["value"] == 0.5
    assert roc_auc([1, 1], [0.0, 1.0])["value"] is None


def test_average_precision_ties_are_atomic():
    # First threshold captures one positive with precision 1; second adds one positive and one negative.
    assert average_precision([1, 0, 1], [0.9, 0.5, 0.5])["value"] == pytest.approx(0.5 + 1 / 3)
    assert average_precision([1, 0, 1], [0.5, 0.5, 0.5])["value"] == pytest.approx(2 / 3)
    assert average_precision([0, 0], [0.4, 0.7])["value"] is None
    assert average_precision([1, 1], [0.4, 0.7])["value"] == 1


def test_probability_metrics_independent_arithmetic():
    result = binary_metrics([0, 1, 0, 1], [0.1, 0.8, 0.7, 0.4], threshold=0.5)
    assert result["confusion"] == {"tn": 1, "fp": 1, "fn": 1, "tp": 1}
    assert result["brier"]["value"] == pytest.approx((0.01 + 0.04 + 0.49 + 0.36) / 4)
    assert result["log_loss"]["value"] == pytest.approx(-math.log(0.9 * 0.8 * 0.3 * 0.4) / 4)
    for metric in ("precision", "recall", "specificity", "f1", "accuracy", "review_rate"):
        assert result[metric]["value"] == 0.5
    assert binary_metrics([0, 1], [0, 1])["log_loss"]["value"] == 0
    infinite = binary_metrics([0, 1], [1, 0])["log_loss"]
    assert infinite["value"] is None and "infinite" in infinite["reason"]


def test_undefined_denominators_do_not_become_zero():
    result = binary_metrics([0, 0], [0.1, 0.2])
    assert result["precision"]["value"] is None
    assert result["recall"]["value"] is None
    assert result["roc_auc"]["value"] is None
    assert result["f1"]["value"] is None
    assert result["specificity"]["value"] == 1
    assert result["recall_interval"]["lower"] is None


@pytest.mark.parametrize("labels,probabilities", [([], []), ([0], [0.2, 0.3]), ([2], [0.2]),
                                                       ([1], [float('nan')]), ([1], [float('inf')]),
                                                       ([1], [-0.1]), ([1], [1.1]), ([True], [0.5])])
def test_metrics_reject_invalid_input(labels, probabilities):
    with pytest.raises(ValueError):
        binary_metrics(labels, probabilities)


def test_calibration_bins_boundary_membership_and_ece():
    result = calibration_bins([0, 1, 1, 1], [0.0, 0.5, 0.7, 1.0], n_bins=2)
    assert [b["n"] for b in result["bins"]] == [1, 3]
    assert result["bins"][1]["mean_probability"] == pytest.approx(2.2 / 3)
    assert result["expected_calibration_error"] == pytest.approx(0.2)
    assert calibration_bins([1], [1], n_bins=10)["bins"][0]["outcome_rate"] is None


def test_wilson_reference_example_and_boundary():
    interval = wilson_interval(20, 100)
    assert interval["lower"] == pytest.approx(0.1333669333310325)
    assert interval["upper"] == pytest.approx(0.2888291655931589)
    assert wilson_interval(0, 10)["lower"] == pytest.approx(0)
    assert wilson_interval(0, 10)["upper"] > 0
    assert wilson_interval(10, 10)["upper"] == pytest.approx(1)
    assert wilson_interval(0, 0)["reason"] == "no observations"
    with pytest.raises(ValueError):
        wilson_interval(4, 3)


def test_sample_planning_and_exact_zero_failure():
    assert proportion_sample_size(0.05)["sample_size"] == 385
    assert proportion_sample_size(0.05, population_size=1000)["sample_size"] == 278
    assert proportion_sample_size(0.05, population_size=1)["sample_size"] == 1
    bound = zero_failure_upper_bound(100)
    assert bound["upper"] == pytest.approx(1 - 0.05 ** (1 / 100))
    planned = zero_failure_sample_size(0.01)
    n = planned["sample_size"]
    assert n == 299
    assert zero_failure_upper_bound(n)["upper"] <= 0.01
    assert zero_failure_upper_bound(n - 1)["upper"] > 0.01


def test_stratified_sample_weights_reproducibility_and_order_stability():
    records = [{"customer_id": str(i), "segment": "A" if i < 8 else "B"} for i in range(10)]
    sample = stratified_sample(records, "segment", {"A": 2, "B": 2}, seed=17)
    assert sample == stratified_sample(records[::-1], "segment", {"B": 2, "A": 2}, seed=17)
    assert len({row["record"]["customer_id"] for row in sample["sample"]}) == 4
    assert sum(row["weight"] for row in sample["sample"]) == 10
    assert sample["design"][0]["weight"] == 4
    with pytest.raises(ValueError):
        stratified_sample(records, "segment", {"A": 2, "B": 3})
    with pytest.raises(ValueError):
        stratified_sample(records, "segment", {"A": 2})
    with pytest.raises(ValueError):
        stratified_sample(records + [records[0]], "segment", {"A": 2, "B": 2})


def test_stratified_estimation_weights_and_variance():
    sample = [{"segment": "A", "label": 0}, {"segment": "A", "label": 1},
              {"segment": "B", "label": 1}, {"segment": "B", "label": 1}]
    result = stratified_proportion(sample, {"A": 8, "B": 2})
    assert result["estimate"] == pytest.approx(0.6)
    # W_A^2 * (1 - n_A / N_A) * s_A^2 / n_A; stratum B is a census.
    assert result["standard_error"] == pytest.approx(math.sqrt(0.8 ** 2 * 0.75 * 0.5 / 2))
    tiny = stratified_proportion([{"segment": "A", "label": 1}], {"A": 10})
    assert tiny["standard_error"] is None


def test_psi_fixed_bins_missing_and_overflow():
    reference = [0, 1, 2, 3, None]
    spec = fit_reference_bins(reference, 2)
    result = population_stability_index(reference, [-1, 0, 4, None, None], reference_bins=spec)
    assert result["value"] > 0
    assert sum(row["reference_count"] for row in result["bins"]) == 5
    assert sum(row["current_count"] for row in result["bins"]) == 5
    assert result["bins"][0]["current_count"] == 1
    assert result["bins"][-2]["current_count"] == 1
    assert result["bins"][-1]["current_count"] == 2
    assert sum(row["reference_share"] for row in result["bins"]) == pytest.approx(1)
    assert population_stability_index(reference, reference)["value"] == 0


def test_psi_degenerate_distributions_still_detect_drift():
    constant = population_stability_index([4] * 5, [4] * 5)
    assert constant["value"] == 0
    shifted = population_stability_index([4] * 5, [5] * 5)
    assert shifted["value"] > 0
    assert shifted["bins"][1]["reference_count"] == 5
    assert shifted["bins"][2]["current_count"] == 5
    assert population_stability_index([None] * 5, [None] * 5)["value"] == 0
    assert population_stability_index([None] * 5, [0] * 5)["value"] > 0


def test_drift_effects_independently_calculated():
    report = distribution_drift([0, 0, 1, 1], [1, 1, 2, 2])
    assert report["ks_statistic"]["value"] == 0.5
    assert report["wasserstein_distance"]["value"] == 1
    assert report["mean_difference"]["value"] == 1
    assert report["median_difference"]["value"] == 1
    assert report["rank_biserial"]["value"] == 0.75
    assert report["standardized_mean_difference"]["value"] == pytest.approx(math.sqrt(3))
    zero_variance = distribution_drift([1, 1], [2, 2])
    assert zero_variance["standardized_mean_difference"]["value"] is None
    assert zero_variance["ks_statistic"]["value"] == 1
    assert distribution_drift([None], [1])["ks_statistic"]["value"] is None


def test_migrations_include_zero_origin_rows():
    result = migration_matrix(["low", "low", "high"], ["medium", "low", "low"], ["low", "medium", "high"])
    assert result["counts"] == [[1, 1, 0], [0, 0, 0], [1, 0, 0]]
    assert result["row_proportions"][1] == [None, None, None]
    assert result["upward"] == result["downward"] == 1
    assert result["changed"] == 2
    assert not migration_matrix(["low"], ["high"])["direction_available"]


def test_segment_support_gates():
    result = segment_metrics([0, 1, 0, 0], [0.1, 0.9, 0.4, 0.3], ["a", "a", "b", "b"], min_n=2, min_events=1)
    assert result["segments"]["a"]["metrics"]["roc_auc"]["value"] == 1
    assert result["segments"]["b"]["metrics"] is None


def test_bootstrap_pairing_cluster_counts_and_determinism():
    y, a, b = [0, 1] * 10, [0.2, 0.8] * 10, [0.3, 0.7] * 10
    result = paired_bootstrap_delta(y, a, b, "brier", repetitions=50, groups=[str(i // 2) for i in range(20)])
    assert result["delta"] == pytest.approx(0.05)
    assert result["lower"] == pytest.approx(0.05)
    assert result["upper"] == pytest.approx(0.05)
    assert result["sampling_units"] == 10
    assert result == paired_bootstrap_delta(y, a, b, "brier", repetitions=50, groups=[str(i // 2) for i in range(20)])
    identical = paired_bootstrap_delta(y, a, a, repetitions=50)
    assert identical["lower"] == identical["upper"] == 0
    unsupported = paired_bootstrap_delta([1, 1], [0.1, 0.3], [0.2, 0.4], repetitions=20)
    assert unsupported["delta"] is None and unsupported["lower"] is None
    assert unsupported["skipped_replicates"] == 20


def test_sensitivity_monotonicity_and_no_mutation():
    baseline = {"a": 0.3, "b": 0.5}
    report = sensitivity_analysis(lambda r: 2 * r["a"] + r["b"], baseline, {"a": [0, 0.5, 1]})
    assert report["baseline_output"] == 1.1
    assert report["features"]["a"]["nondecreasing_violations"] == 0
    assert report["features"]["a"]["maximum_absolute_delta"] == pytest.approx(1.4)
    assert baseline == {"a": 0.3, "b": 0.5}


def test_permutation_determinism_signal_and_no_mutation():
    rows = [{"a": 0.1, "b": 0.7}, {"a": 0.9, "b": 0.7}] * 20
    y = [0, 1] * 20
    def predict(records):
        return [row["a"] for row in records]
    result = permutation_importance(predict, rows, y, repetitions=4)
    assert result["features"]["a"]["mean_degradation"] > 0
    assert result["features"]["b"]["mean_degradation"] == 0
    assert result == permutation_importance(predict, rows, y, repetitions=4)
    assert rows[0] == {"a": 0.1, "b": 0.7}


@given(st.lists(st.tuples(st.integers(0, 1), st.integers(-3, 3)), min_size=2, max_size=50))
def test_auc_matches_quadratic_independent_oracle(pairs):
    y, scores = zip(*pairs)
    positive = [score for label, score in pairs if label]
    negative = [score for label, score in pairs if not label]
    observed = roc_auc(y, scores)["value"]
    if not positive or not negative:
        assert observed is None
    else:
        expected = sum((a > b) + 0.5 * (a == b) for a in positive for b in negative)
        assert observed == pytest.approx(expected / (len(positive) * len(negative)))


def test_against_optional_sklearn_and_scipy():
    sklearn = pytest.importorskip("sklearn.metrics")
    scipy = pytest.importorskip("scipy.stats")
    y = [0, 1, 1, 0, 1, 0, 0, 1]
    p = [0.1, 0.2, 0.6, 0.6, 0.6, 0.8, 0.4, 0.8]
    report = binary_metrics(y, p)
    assert report["roc_auc"]["value"] == pytest.approx(sklearn.roc_auc_score(y, p))
    assert report["average_precision"]["value"] == pytest.approx(sklearn.average_precision_score(y, p))
    assert report["brier"]["value"] == pytest.approx(sklearn.brier_score_loss(y, p))
    assert report["log_loss"]["value"] == pytest.approx(sklearn.log_loss(y, p))
    a, b = [1, 1, 2, 5, 7], [-1, 2, 2, 3, 4, 5]
    drift = distribution_drift(a, b)
    assert drift["ks_statistic"]["value"] == pytest.approx(scipy.ks_2samp(a, b).statistic)
    assert drift["wasserstein_distance"]["value"] == pytest.approx(scipy.wasserstein_distance(a, b))
