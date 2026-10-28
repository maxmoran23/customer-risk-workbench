"""Reproducible, bounded-memory fixtures in invented base units.

These distributions are engineering fixtures, not estimates of customer populations,
financial-crime prevalence, or effectiveness. No real jurisdiction or personal identifier
is used. Segment labels describe operating contexts and do not determine risk.
"""
from __future__ import annotations

from datetime import timedelta
import math
import random
from typing import Iterator

from .contracts import ContractError, Customer, Transaction, timestamp

PROFILE_KEYS = (
    "ownership_opacity", "business_complexity", "geography_exposure",
    "product_complexity", "channel_opacity", "source_of_funds_concern",
    "adverse_information", "pep_exposure", "documentation_gap",
    "screening_unresolved", "cash_intensity", "cross_border_exposure",
)
SEGMENTS = ("retail", "small_business", "corporate", "nonprofit", "intermediary", "private_enterprise")
DEFAULT_AS_OF = "2026-10-01T00:00:00Z"


def _integer(value: int, name: str, minimum: int) -> None:
    if type(value) is not int or value < minimum:
        raise ContractError(f"{name} must be an integer >= {minimum}")


def _iso(value) -> str:
    return value.isoformat().replace("+00:00", "Z")


def iter_portfolio(
    customers: int = 100,
    transactions_per_customer: int = 40,
    seed: int = 42,
    as_of: str = DEFAULT_AS_OF,
    *,
    missing_rate: float = 0.0,
) -> Iterator[tuple[Customer, list[Transaction]]]:
    """Yield one complete customer and its events with O(events/customer) memory.

    A per-customer random stream makes prefixes stable when the customer count grows.
    ``missing_rate`` independently masks profile evidence and jurisdiction evidence;
    it never fills missing observations with a benign zero. Transactions span 395 days,
    with 65% placed in the most recent 30 days, and amounts share an invented unit.
    Generator-version 1 fixes semantics; reproduce with seed, arguments, and code hash.
    """
    _integer(customers, "customers", 0)
    _integer(transactions_per_customer, "transactions_per_customer", 0)
    if type(seed) is not int:
        raise ContractError("seed must be an integer")
    if isinstance(missing_rate, bool) or not isinstance(missing_rate, (float, int)) or not math.isfinite(missing_rate) or not 0 <= missing_rate <= 1:
        raise ContractError("missing_rate must be a finite number in [0,1]")
    cutoff = timestamp(as_of)
    for index in range(customers):
        rng = random.Random(f"crw-synthetic-v1:{seed}:{index}")
        customer_id = f"syn-c-{index:09d}"
        elevated = rng.random() < .18
        profile = {name: round(rng.betavariate(3.5, 1.7) if elevated else rng.betavariate(1.2, 6), 6)
                   for name in PROFILE_KEYS}
        # A review queue signal is a discrete unresolved-work state, not a suspicion label.
        profile["screening_unresolved"] = float(rng.random() < .04)
        profile["pep_exposure"] = round(rng.betavariate(1, 4), 6)
        if missing_rate:
            profile = {name: None if rng.random() < missing_rate else value for name, value in profile.items()}
        onboarded = cutoff - timedelta(days=400 + rng.randrange(800))
        profile_time = cutoff - timedelta(days=rng.randrange(60))
        magnitude = rng.lognormvariate(5, .9)
        cash_probability = .12 if not elevated else .4
        events = []
        for event_index in range(transactions_per_customer):
            age_days = rng.uniform(.001, 29.999) if rng.random() < .65 else rng.uniform(30, 395)
            event_time = cutoff - timedelta(seconds=round(age_days * 86400))
            amount = round(max(.01, rng.lognormvariate(math.log(magnitude), .8)), 2)
            channel = rng.choices(("cash", "wire", "card", "digital", "other"),
                                  (cash_probability, .35, .25, .2, .08), k=1)[0]
            jurisdiction = round(rng.betavariate(3, 2) if elevated else rng.betavariate(1, 8), 6)
            if rng.random() < missing_rate:
                jurisdiction = None
            events.append(Transaction(
                transaction_id=f"syn-t-{index:09d}-{event_index:07d}", customer_id=customer_id,
                occurred_at=_iso(event_time), available_at=_iso(event_time + timedelta(seconds=rng.randrange(300))),
                amount=amount, direction="in" if rng.random() < .5 else "out",
                counterparty_id=f"syn-p-{index:09d}-{rng.randrange(max(2, transactions_per_customer // 3 + 1)):06d}",
                channel=channel, jurisdiction_risk=jurisdiction, source_id="synthetic-ledger-v1",
            ))
        observed_30 = math.fsum(t.amount for t in events if (cutoff - timestamp(t.occurred_at)).total_seconds() < 30 * 86400)
        expected = round(max(1.0, observed_30 / (rng.uniform(2.1, 4.5) if elevated else rng.uniform(.7, 1.4))), 2)
        customer = Customer(
            customer_id=customer_id, as_of=_iso(profile_time), available_at=_iso(profile_time),
            segment=SEGMENTS[index % len(SEGMENTS)], onboarded_at=_iso(onboarded), profile=profile,
            expected_monthly_volume=expected, source_id="synthetic-profile-v1",
            history_start=_iso(onboarded), history_complete=True,
        )
        yield customer, events


def generate_portfolio(
    customers: int = 100,
    transactions_per_customer: int = 40,
    seed: int = 42,
    as_of: str = DEFAULT_AS_OF,
    *,
    missing_rate: float = 0.0,
) -> tuple[list[Customer], list[Transaction]]:
    """Materialize the seeded generator for small demos; stream large workloads instead."""
    records: list[Customer] = []
    transactions: list[Transaction] = []
    for customer, events in iter_portfolio(customers, transactions_per_customer, seed, as_of, missing_rate=missing_rate):
        records.append(customer)
        transactions.extend(events)
    return records, transactions
