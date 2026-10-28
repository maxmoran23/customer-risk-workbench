from crw.features import build_features
from crw.patterns import evaluate_condition, evaluate_patterns, reference_patterns
from crw.contracts import ContractError
from crw.stress import stress_portfolio
import pytest
from copy import deepcopy

AS_OF = "2026-10-01T00:00:00Z"


def test_three_valued_logic(customer, events):
    f = build_features(customer, events, AS_OF)
    missing = {"feature": "profile.ownership_opacity", "op": "gt", "value": 0.5}
    f.values["profile.ownership_opacity"] = None
    false = {"feature": "profile.business_complexity", "op": "gt", "value": 0.9}
    true = {"not": false}
    assert evaluate_condition({"all": [missing, false]}, f)["state"] == "FALSE"
    assert evaluate_condition({"any": [missing, true]}, f)["state"] == "TRUE"
    assert evaluate_condition({"not": missing}, f)["state"] == "UNKNOWN"
    assert evaluate_condition({"all": [missing, true]}, f)["state"] == "UNKNOWN"


@pytest.mark.parametrize(
    "condition",
    [
        {"all": []},
        {"feature": "made_up", "op": "gt", "value": 1},
        {"feature": "profile.ownership_opacity", "op": "eval", "value": 1},
        {"all": [], "any": []},
    ],
)
def test_predicate_rejection(condition, customer, events):
    with pytest.raises(ContractError):
        evaluate_condition(condition, build_features(customer, events, AS_OF))


def test_pattern_registry_complete(customer, events):
    result = evaluate_patterns(build_features(customer, events, AS_OF))
    assert len(result) == len(reference_patterns()) == 20
    assert len({r["id"] for r in result}) == 20
    assert all(r["benign_explanation"] and r["next_evidence"] and r["evaluation"] for r in result)


def test_stress_preserves_source_and_screening_score(customer, events, policy):
    f = build_features(customer, events, AS_OF)
    original = f.to_dict()
    report = stress_portfolio([(customer.customer_id, f)], policy, AS_OF)
    assert f.to_dict() == original
    screening = next(r for r in report["experiments"] if r["id"] == "screening_unresolved")
    assert screening["mean_delta"] == 0
    missing = next(r for r in report["experiments"] if r["id"] == "ownership_unknown")
    assert missing["migrations"][0]["to"] == "REVIEW_REQUIRED"
    assert missing["complete_paired_n"] == 0
    assert missing["mean_complete_score_delta"] is None
    assert missing["examples"][0]["after_score"] is None
    assert missing["examples"][0]["after_bounds"][1] > missing["examples"][0]["after_bounds"][0]
    assert "provisional lower bound" in missing["delta_basis"]


def test_stress_rejects_duplicate_customer_baselines(customer, events, policy):
    first = build_features(customer, events, AS_OF)
    second = deepcopy(first)
    first.values["profile.ownership_opacity"] = 0.1
    second.values["profile.ownership_opacity"] = 0.9
    with pytest.raises(ContractError, match="unique customer IDs"):
        stress_portfolio([(customer.customer_id, first), (customer.customer_id, second)], policy, AS_OF)
