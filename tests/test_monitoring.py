from dataclasses import replace
import pytest
from crw.features import build_features
from crw.scoring import score
from crw.policy import Policy
from crw.monitoring import monitor_portfolios, attribute_change, review_sample, validate_assessment
from crw.contracts import ContractError

AS_OF = "2026-10-01T00:00:00Z"


def test_population_integrity_and_missing_handling(customer, events, policy):
    a = score(build_features(customer, events, AS_OF), policy, customer.customer_id, AS_OF)
    b = score(
        build_features(
            replace(customer, profile={**customer.profile, "ownership_opacity": None}), events, AS_OF
        ),
        policy,
        customer.customer_id,
        AS_OF,
    )
    report = monitor_portfolios([a], [b], min_n=1)
    assert report["matched_customers"] == 1
    assert report["current"]["incomplete_scores"] == 1
    assert report["paired_migration"]["changed"] == 1
    assert report["paired_migration"]["direction_available"] is False
    assert report["score_drift"]["current_missing_rate"] == 1
    with pytest.raises(ContractError):
        monitor_portfolios([a, a], [b])
    with pytest.raises(ContractError):
        validate_assessment({**a, "provisional_index": 999})


def test_crossed_attribution(customer, events, policy):
    old = build_features(customer, events, AS_OF)
    new = build_features(
        replace(customer, profile={**customer.profile, "ownership_opacity": 0.3}), events, AS_OF
    )
    config = policy.to_dict()
    config["factors"][0]["weight"] = 20
    report = attribute_change(old, new, policy, Policy.from_dict(config))
    assert report["data_effect"] == pytest.approx(3)
    assert report["policy_effect"] == pytest.approx(2)
    assert report["total_provisional_change"] == pytest.approx(5)
    assert report["interaction"] == pytest.approx(2)


def test_review_sampling(customer, events, policy):
    a = score(build_features(customer, events, AS_OF), policy, customer.customer_id, AS_OF)
    result = review_sample([a], per_band=20)
    assert result["allocation"][a["band"]] == 1
    assert result == review_sample([a], per_band=20)


def test_monitoring_and_attribution_reject_unit_mismatch(customer, events, policy):
    old = build_features(customer, events, AS_OF, base_unit="UNIT_A")
    new = build_features(customer, events, AS_OF, base_unit="UNIT_B")
    a = score(old, policy, customer.customer_id, AS_OF)
    b = score(new, policy, customer.customer_id, AS_OF)
    with pytest.raises(ContractError, match="different amount units"):
        monitor_portfolios([a], [b])
    with pytest.raises(ContractError, match="consistent amount unit"):
        attribute_change(old, new, policy, policy)
