from dataclasses import replace
import math
import pytest
from hypothesis import given, strategies as st

from crw.contracts import ContractError, Customer, utc
from crw.features import build_features, aggregate, feature_catalog
from crw.policy import PROFILE_KEYS, Policy, reference_policy
from crw.scoring import score, severity, compare_assessments

AS_OF = "2026-10-01T00:00:00Z"


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, True, "1"])
def test_invalid_amount(events, value):
    with pytest.raises(ContractError):
        replace(events[0], amount=value)


def test_strict_contract(customer):
    for edit in ({"extra": 1}, {"history_complete": "yes"}, {"as_of": "2026-09-01"}):
        with pytest.raises(ContractError):
            Customer.from_dict({**customer.to_dict(), **edit})
    record = customer.to_dict()
    del record["history_complete"]
    with pytest.raises(ContractError):
        Customer.from_dict(record)


def test_timestamp_canonical_sort():
    assert utc("2026-10-01T00:00:00Z") < utc("2026-10-01T00:00:00.000001Z")
    assert utc("2026-09-30T20:00:00-04:00") == utc(AS_OF)


def test_exact_window_boundaries(customer, events):
    a = replace(
        events[0], transaction_id="a", occurred_at="2026-09-30T00:00:00Z", available_at="2026-09-30T00:00:00Z"
    )
    b = replace(
        a,
        transaction_id="b",
        occurred_at="2026-09-30T00:00:00.000001Z",
        available_at="2026-09-30T00:00:00.000001Z",
    )
    c = replace(a, transaction_id="c", occurred_at=AS_OF, available_at=AS_OF)
    f = build_features(customer, [a, b, c], AS_OF)
    assert f.values["txn.1d.count"] == 2
    assert f.values["txn.7d.count"] == 3


def test_temporal_leakage(customer, events):
    future = replace(
        events[0],
        transaction_id="future",
        occurred_at="2026-10-02T00:00:00Z",
        available_at="2026-10-02T00:00:00Z",
    )
    delayed = replace(events[0], transaction_id="delayed", available_at="2026-10-02T00:00:00Z")
    base = build_features(customer, events, AS_OF)
    extra = build_features(customer, [*events, future, delayed], AS_OF)
    assert base.values == extra.values
    assert base.lineage == extra.lineage
    assert extra.quality["excluded_future"] == extra.quality["excluded_unavailable"] == 1
    with pytest.raises(ContractError):
        build_features(replace(customer, available_at="2026-10-02T00:00:00Z"), events, AS_OF)


def test_duplicate_or_foreign_rejected(customer, events):
    with pytest.raises(ContractError):
        build_features(customer, [events[0], events[0]], AS_OF)
    with pytest.raises(ContractError):
        build_features(customer, [replace(events[0], customer_id="foreign")], AS_OF)


def test_aggregate_independent_arithmetic(events):
    a = replace(events[0], amount=100, direction="in", channel="cash", jurisdiction_risk=0.2)
    b = replace(events[1], amount=300, direction="out", channel="wire", jurisdiction_risk=0.8)
    result = aggregate([a, b])
    assert result["total"] == 400
    assert result["cash_share"] == 0.25
    assert result["high_risk_share"] == pytest.approx(0.65)
    assert result["flow_through"] == pytest.approx(1 / 3)
    assert result["mean_amount"] == 200
    assert aggregate([a, replace(b, jurisdiction_risk=None)])["high_risk_share"] is None
    assert aggregate([])["flow_through"] is None


def test_window_order_invariance(customer, events):
    a = build_features(customer, events, AS_OF)
    b = build_features(customer, reversed(events), AS_OF)
    assert a.to_dict() == b.to_dict()
    assert a.values["txn.last4.count"] == 4
    assert a.values["txn.last4.total"] == 400


def test_missing_is_not_zero(customer, events, policy):
    before = score(build_features(customer, events, AS_OF), policy, customer.customer_id, AS_OF)
    absent = replace(customer, profile={**customer.profile, "ownership_opacity": None})
    after = score(build_features(absent, events, AS_OF), policy, customer.customer_id, AS_OF)
    assert after["score"] is None
    assert after["band"] == "REVIEW_REQUIRED"
    assert after["upper_bound"] > after["lower_bound"]
    assert after["lower_bound"] <= before["provisional_index"] <= after["upper_bound"]


def test_group_caps_and_nonduplicated_windows(customer, events, policy):
    all_cash = [replace(e, channel="cash") for e in events]
    result = score(build_features(customer, all_cash, AS_OF), policy, customer.customer_id, AS_OF)
    behavioral = next(g for g in result["groups"] if g["id"] == "behavior")
    assert behavioral["points"] == 15
    assert sum(r["raw_points"] for r in result["reasons"] if r["group"] == "behavior") > 15
    assert result["provisional_index"] == pytest.approx(sum(g["points"] for g in result["groups"]))


def test_screening_separate(customer, events, policy):
    base = score(build_features(customer, events, AS_OF), policy, customer.customer_id, AS_OF)
    changed = replace(customer, profile={**customer.profile, "screening_unresolved": 1})
    result = score(build_features(changed, events, AS_OF), policy, customer.customer_id, AS_OF)
    assert result["provisional_index"] == base["provisional_index"]
    assert result["review_flags"][0]["state"] == "TRUE"


@pytest.mark.parametrize("change", ["caps", "duplicate", "nan", "feature", "bands", "bool", "keys"])
def test_policy_validation(change):
    c = reference_policy().to_dict()
    if change == "caps":
        c["groups"][0]["cap"] = 24
    if change == "duplicate":
        c["factors"].append(c["factors"][0])
    if change == "nan":
        c["factors"][0]["weight"] = math.nan
    if change == "feature":
        c["factors"][0]["feature"] = "typo"
    if change == "bands":
        c["bands"][1]["minimum"] = 0
    if change == "bool":
        c["factors"][0]["min_support"] = True
    if change == "keys":
        c["unknown"] = "wrong"
    with pytest.raises(ContractError):
        Policy.from_dict(c)


@given(
    st.floats(min_value=0, max_value=1, allow_nan=False), st.floats(min_value=0, max_value=1, allow_nan=False)
)
def test_severity_monotonic(a, b):
    factor = {"feature": "test", "low": 0.2, "high": 0.8, "direction": "increasing"}
    assert severity(min(a, b), factor) <= severity(max(a, b), factor)


def test_catalog_and_policy_reachability():
    catalog = feature_catalog(PROFILE_KEYS)
    assert len(catalog) == len({r["name"] for r in catalog})
    names = {r["name"] for r in catalog}
    assert all(f["feature"] in names for f in reference_policy().to_dict()["factors"])


def test_comparison(customer, events, policy):
    a = score(build_features(customer, events, AS_OF), policy, customer.customer_id, AS_OF)
    b = score(
        build_features(
            replace(customer, profile={**customer.profile, "ownership_opacity": 0.9}), events, AS_OF
        ),
        policy,
        customer.customer_id,
        AS_OF,
    )
    c = compare_assessments(a, b)
    assert c["provisional_delta"] == pytest.approx(8)
    assert sum(c["group_deltas"].values()) == pytest.approx(8)
