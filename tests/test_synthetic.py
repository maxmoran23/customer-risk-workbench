import random

import pytest

from crw.contracts import ContractError, Customer, Transaction, timestamp
from crw.features import build_features
from crw.synthetic import DEFAULT_AS_OF, PROFILE_KEYS, generate_portfolio, iter_portfolio


def test_seed_replays_the_identical_materialized_portfolio():
    first = generate_portfolio(customers=5, transactions_per_customer=12, seed=51)
    second = generate_portfolio(customers=5, transactions_per_customer=12, seed=51)
    assert first == second
    assert first != generate_portfolio(customers=5, transactions_per_customer=12, seed=52)


def test_streamed_records_equal_materialized_records():
    customers, transactions = generate_portfolio(8, 11, seed=75)
    streamed = list(iter_portfolio(8, 11, seed=75))
    assert customers == [customer for customer, _ in streamed]
    assert transactions == [event for _, events in streamed for event in events]


def test_population_extension_preserves_existing_customer_prefix():
    smaller = list(iter_portfolio(3, 14, seed=9))
    larger = list(iter_portfolio(7, 14, seed=9))
    assert smaller == larger[:3]


def test_large_requested_population_can_yield_one_record():
    generator = iter_portfolio(1_000_000_000, 2, seed=1)
    customer, transactions = next(generator)
    assert customer.customer_id == "syn-c-000000000"
    assert len(transactions) == 2
    generator.close()


def test_generator_does_not_touch_global_random_state():
    before = random.getstate()
    generate_portfolio(4, 12)
    assert random.getstate() == before


def test_contract_roundtrip_unique_ids_and_valid_time_relationships():
    customers, transactions = generate_portfolio(20, 40)
    assert len({c.customer_id for c in customers}) == 20
    assert len({t.transaction_id for t in transactions}) == 800
    customer_map = {c.customer_id: c for c in customers}
    for c in customers:
        assert Customer.from_dict(c.to_dict()) == c
        assert set(c.profile) == set(PROFILE_KEYS)
        assert c.history_complete is True
        assert c.history_start == c.onboarded_at
    for t in transactions:
        assert Transaction.from_dict(t.to_dict()) == t
        assert timestamp(t.available_at) >= timestamp(t.occurred_at)
        assert timestamp(t.occurred_at) >= timestamp(customer_map[t.customer_id].onboarded_at)
        assert t.amount >= 0


def test_every_generated_customer_can_build_features_without_cross_customer_rows():
    for customer, events in iter_portfolio(30, 40, seed=777):
        features = build_features(customer, events, DEFAULT_AS_OF)
        assert features.quality["included_transactions"] + features.quality["excluded_unavailable"] == 40
        assert features.quality["history_complete"] is True


def test_explicit_all_missing_fixture_preserves_unknown_values():
    customers, transactions = generate_portfolio(2, 5, missing_rate=1)
    assert all(value is None for c in customers for value in c.profile.values())
    assert all(t.jurisdiction_risk is None for t in transactions)


def test_empty_populations_and_empty_customer_ledgers_are_supported():
    assert generate_portfolio(0, 5) == ([], [])
    customers, transactions = generate_portfolio(2, 0)
    assert len(customers) == 2
    assert transactions == []
    assert all(c.expected_monthly_volume > 0 for c in customers)


@pytest.mark.parametrize("kwargs", [
    {"customers": -1}, {"customers": True}, {"customers": 1.2},
    {"transactions_per_customer": -1}, {"transactions_per_customer": False},
    {"seed": 1.5}, {"seed": True}, {"missing_rate": -0.1},
    {"missing_rate": 1.1}, {"missing_rate": float("nan")},
    {"missing_rate": True}, {"as_of": "2026-10-01"},
])
def test_invalid_generator_arguments_fail(kwargs):
    with pytest.raises(ContractError):
        generate_portfolio(**kwargs)
