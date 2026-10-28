from copy import deepcopy
import json

import pytest

from crw.learning import (
    FEATURE_ORDER, choose_threshold, evaluate_frozen_stress, fit_challengers, generate_research_rows,
    predict_logistic_json, run_research_experiment, temporal_entity_split,
)


def split(rows):
    return temporal_entity_split(rows, "2024-07-01T00:00:00Z", "2024-10-01T00:00:00Z", "2025-02-15T00:00:00Z")


def row(customer, assessment, observed, available):
    return {"customer_id": customer, "as_of": assessment, "feature_available_at": assessment,
            "outcome_observed_at": observed, "outcome_available_at": available,
            "label": 1, "segment": "generic", "features": {"a": 0.5}}


def test_generator_seed_stochasticity_and_no_score_label_dependency():
    a = generate_research_rows(300, seed=42)
    assert a == generate_research_rows(300, seed=42)
    assert a != generate_research_rows(300, seed=43)
    assert {r["label"] for r in a} == {0, 1}
    assert set(a[0]["features"]) == set(FEATURE_ORDER)
    assert all("score" not in key and "label" not in key for key in a[0]["features"])
    assert len(generate_research_rows(10, repeat_snapshots=2)) == 20
    assert len({r["customer_id"] for r in generate_research_rows(10, repeat_snapshots=2)}) == 10
    assert generate_research_rows(300, seed=42, prevalence_shift=1) != a


def test_split_purges_customer_overlap_and_censored_outcomes():
    rows = [row("crossing", "2024-01-01T00:00:00Z", "2024-02-01T00:00:00Z", "2024-02-02T00:00:00Z"),
            row("crossing", "2024-08-01T00:00:00Z", "2024-09-01T00:00:00Z", "2024-09-02T00:00:00Z"),
            row("good_train", "2024-01-01T00:00:00Z", "2024-02-01T00:00:00Z", "2024-02-02T00:00:00Z"),
            row("censored", "2024-06-15T00:00:00Z", "2024-07-15T00:00:00Z", "2024-07-16T00:00:00Z"),
            row("short", "2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z", "2024-01-03T00:00:00Z"),
            row("good_cal", "2024-08-01T00:00:00Z", "2024-09-01T00:00:00Z", "2024-09-02T00:00:00Z"),
            row("good_hold", "2024-11-01T00:00:00Z", "2024-12-01T00:00:00Z", "2024-12-02T00:00:00Z")]
    result = split(rows)
    assert [r["customer_id"] for r in result["train"]] == ["good_train"]
    assert [r["customer_id"] for r in result["calibration"]] == ["good_cal"]
    assert [r["customer_id"] for r in result["holdout"]] == ["good_hold"]
    assert result["manifest"]["excluded_rows"] == {"customer_crosses_partitions": 2,
        "outcome_unavailable_at_partition_cutoff": 1, "insufficient_outcome_horizon": 1}
    assert sum(result["manifest"]["row_counts"].values()) + sum(result["manifest"]["excluded_rows"].values()) == len(rows)


def test_split_rejects_feature_leakage_duplicate_and_naive_timestamps():
    source = row("a", "2024-01-01T00:00:00Z", "2024-02-01T00:00:00Z", "2024-02-02T00:00:00Z")
    bad = dict(source, feature_available_at="2024-01-01T00:00:01Z")
    with pytest.raises(ValueError, match="temporal leakage"):
        split([bad])
    with pytest.raises(ValueError, match="duplicate"):
        split([source, source])
    with pytest.raises(ValueError, match="timezone-aware"):
        split([dict(source, as_of="2024-01-01")])
    with pytest.raises(ValueError, match="chronology"):
        split([dict(source, outcome_available_at="2024-01-02T00:00:00Z")])


def test_threshold_cost_and_ties_respect_capacity():
    selection = choose_threshold([0, 1, 0, 1], [0.1, 0.8, 0.9, 0.7], max_review_rate=0.5)
    assert selection["threshold"] == 0.8
    assert selection["calibration_cost"] == 5
    none = choose_threshold([0, 1, 0, 1], [0.1, 0.8, 0.9, 0.7], max_review_rate=0.25)
    assert none["threshold"] == 1.0
    assert none["calibration_review_rate"] == 0
    ties = choose_threshold([1, 1, 0, 0], [0.8, 0.8, 0.8, 0.2], max_review_rate=0.5)
    assert ties["calibration_review_rate"] == 0


@pytest.fixture(scope="module")
def fitted():
    pytest.importorskip("sklearn")
    return fit_challengers(split(generate_research_rows(900, seed=7)), include_tree=True, bootstrap_repetitions=20,
                           monotonic_constraints={"jurisdiction_exposure": 1, "ownership_opacity": 1})


def test_research_export_is_json_numeric_and_replay_is_exact(fitted):
    exported = json.loads(json.dumps(fitted["logistic_model_json"], allow_nan=False))
    assert exported["feature_order"] == list(FEATURE_ORDER)
    assert exported["metadata"]["max_json_replay_absolute_error"] < 1e-12
    assert fitted["split"]["customer_overlap"] == 0
    assert {"prevalence_baseline", "logistic", "hist_gradient_boosting"} == set(fitted["models"])
    probes = fitted["models"]["hist_gradient_boosting"]["metadata"]["monotonic_probes"]
    assert len(probes) == 2 and all(p["tested_pairs"] > 0 and p["violations"] == 0 for p in probes)
    inputs = generate_research_rows(2)
    predicted = predict_logistic_json(exported, [r["features"] for r in inputs])
    assert len(predicted) == 2 and all(0 < value < 1 for value in predicted)
    broken = deepcopy(exported)
    broken["scaler_scale"][0] = 0
    with pytest.raises(ValueError, match="positive"):
        predict_logistic_json(broken, [r["features"] for r in inputs])
    with pytest.raises(ValueError, match="exactly match"):
        predict_logistic_json(exported, [{"unrecognized": 0.5}])


def test_preprocessing_and_threshold_do_not_read_holdout():
    pytest.importorskip("sklearn")
    original = split(generate_research_rows(800, seed=19))
    changed = deepcopy(original)
    for entry in changed["holdout"]:
        entry["features"]["velocity_change"] = 10_000.0
        entry["label"] = 1 - entry["label"]
    a = fit_challengers(original, include_tree=False, bootstrap_repetitions=20)
    b = fit_challengers(changed, include_tree=False, bootstrap_repetitions=20)
    # Exact equality verifies train statistics/coefficients and calibration-only threshold are unaffected.
    a_export, b_export = deepcopy(a["logistic_model_json"]), deepcopy(b["logistic_model_json"])
    # Replay error is a holdout arithmetic diagnostic, not a fitted parameter.
    a_export["metadata"].pop("max_json_replay_absolute_error")
    b_export["metadata"].pop("max_json_replay_absolute_error")
    assert a_export == b_export
    assert a["models"]["logistic"]["threshold_selection"] == b["models"]["logistic"]["threshold_selection"]
    assert a["models"]["logistic"]["holdout_metrics"] != b["models"]["logistic"]["holdout_metrics"]


def test_fit_revalidates_supplied_partition_membership():
    pytest.importorskip("sklearn")
    partitions = split(generate_research_rows(500))
    partitions["train"].append(partitions["holdout"].pop())
    with pytest.raises(ValueError, match="separation"):
        fit_challengers(partitions, include_tree=False, bootstrap_repetitions=20)


def test_all_missing_training_column_has_stable_json_replay():
    pytest.importorskip("sklearn")
    partitions = split(generate_research_rows(600, seed=7))
    for item in partitions["train"]:
        item["features"]["account_age_scaled"] = None
    result = fit_challengers(partitions, include_tree=False, bootstrap_repetitions=20)
    artifact = result["logistic_model_json"]
    assert artifact["imputation_medians"][5] == 0
    assert 5 in artifact["missing_indicator_indices"]
    assert artifact["metadata"]["max_json_replay_absolute_error"] < 1e-12


def test_complete_random_label_noise_is_not_score_derived():
    noisy = generate_research_rows(5000, seed=11, label_noise=0.5)
    fraction = sum(r["label"] for r in noisy) / len(noisy)
    assert 0.45 < fraction < 0.55


def test_multiple_seeds_and_stress_are_explicit():
    pytest.importorskip("sklearn")
    report = run_research_experiment(n=600, seeds=(7, 19), include_stress=True, include_tree=False,
                                     bootstrap_repetitions=20)
    assert report["data_status"] == "synthetic_only"
    assert len(report["experiments"]) == 8
    assert len(report["summary"]) == 8
    assert {e["regime"] for e in report["experiments"]} == {
        "base", "label_noise_15pct", "lower_prevalence", "higher_prevalence"}
    assert all(entry["metrics"]["brier"]["seed_count"] == 2 for entry in report["summary"])
    assert len(report["frozen_model_stress"]) == 2
    assert all(not e["frozen_model_stress"] for e in report["experiments"] if e["regime"] != "base")
    json.dumps(report, allow_nan=False)


def test_frozen_models_preserve_parameters_threshold_and_zero_intervention(fitted):
    for model, report in fitted["frozen_model_stress"].items():
        integrity = report["integrity"]
        assert integrity["training_metadata_sha256_before"] == integrity["training_metadata_sha256_after"]
        assert integrity["threshold_selection_sha256_before"] == integrity["threshold_selection_sha256_after"]
        assert integrity["source_rows_sha256_before"] == integrity["source_rows_sha256_after"]
        assert not integrity["model_refit"] and not integrity["preprocessing_refit"] and not integrity["threshold_reselected"]
        zero = next(s for s in report["scenarios"] if s["name"] == "zero_intervention")
        assert zero["metrics"] == report["baseline_metrics"]
        assert zero["probabilities_in_customer_order"] == report["baseline_probabilities"]
        assert zero["labels_in_customer_order"] == report["baseline_labels"]
        assert zero["paired_changes"]["maximum_absolute_probability_change"] == 0
        assert report["threshold"] == fitted["models"][model]["threshold_selection"]["threshold"]
        for scenario in report["scenarios"]:
            assert scenario["customer_order_sha256"] == report["customer_order_sha256"]
            assert len(scenario["labels_in_customer_order"]) == len(report["customer_ids"])
    numeric_integrity = fitted["frozen_model_stress"]["logistic"]["integrity"]
    assert numeric_integrity["numeric_model_sha256_before"] == numeric_integrity["numeric_model_sha256_after"]


def test_frozen_label_noise_is_shared_across_models_and_does_not_change_predictions(fitted):
    noisy_labels = []
    for report in fitted["frozen_model_stress"].values():
        noisy = next(s for s in report["scenarios"] if s["name"] == "label_noise_15pct")
        assert noisy["probabilities_in_customer_order"] == report["baseline_probabilities"]
        assert noisy["paired_changes"]["label_flips"] > 0
        assert noisy["workload"]["review_count_delta"] == 0
        noisy_labels.append(noisy["labels_in_customer_order"])
    assert all(labels == noisy_labels[0] for labels in noisy_labels)


def test_frozen_feature_changes_leave_labels_and_training_artifact_unchanged(fitted):
    report = fitted["frozen_model_stress"]["logistic"]
    artifact = deepcopy(fitted["logistic_model_json"])
    for scenario in report["scenarios"]:
        if scenario["name"] in {"missing_behavior_features", "jurisdiction_input_shift"}:
            assert scenario["labels_in_customer_order"] == report["baseline_labels"]
            assert scenario["paired_changes"]["changed_feature_cells"] > 0
            assert scenario["paired_changes"]["maximum_absolute_probability_change"] > 0
    rows = split(generate_research_rows(900, seed=7))["holdout"]
    repeated = evaluate_frozen_stress(lambda records: predict_logistic_json(artifact, records), rows,
                                      artifact["metadata"], fitted["models"]["logistic"]["threshold_selection"],
                                      [{"name": "zero_intervention"}])
    assert artifact == fitted["logistic_model_json"]
    assert repeated["baseline_metrics"] == report["baseline_metrics"]


def test_frozen_unsupported_metrics_and_invalid_scenarios_are_explicit():
    rows = [{"customer_id": "a", "features": {"x": 0.2}, "label": 0},
            {"customer_id": "b", "features": {"x": 0.3}, "label": 0}]
    def predict(records):
        return [record["x"] for record in records]
    result = evaluate_frozen_stress(predict, rows, {"training_data_sha256": "fixture"}, {"threshold": 0.5},
                                    [{"name": "unchanged"}, {"name": "flip_all", "label_noise": 1.0}])
    assert result["scenarios"][0]["metrics"]["roc_auc"]["value"] is None
    assert result["scenarios"][1]["metric_deltas"]["recall"]["value"] is None
    assert result["scenarios"][1]["metric_deltas"]["recall"]["reason"]
    assert result["scenarios"][1]["labels_in_customer_order"] == [1, 1]
    with pytest.raises(ValueError, match="declared features"):
        evaluate_frozen_stress(predict, rows, {}, {"threshold": 0.5},
                              [{"name": "bad", "feature_offsets": {"unknown": 1}}])
    with pytest.raises(ValueError, match="unique"):
        evaluate_frozen_stress(predict, rows + [rows[0]], {}, {"threshold": 0.5}, [{"name": "bad"}])
