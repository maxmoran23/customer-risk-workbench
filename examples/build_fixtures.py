"""Rebuild the compact, entirely invented walkthrough portfolio without randomness."""
from __future__ import annotations

import hashlib
from datetime import timedelta
from pathlib import Path

from crw.contracts import Customer, Transaction, timestamp
from crw.io import atomic_json, write_jsonl
from crw.policy import PROFILE_KEYS, reference_policy

ROOT = Path(__file__).resolve().parent
AS_OF = "2026-10-01T00:00:00Z"
UNIT = "SYNTHETIC_UNIT"


def prior(days: float) -> str:
    return (timestamp(AS_OF) - timedelta(days=days)).isoformat().replace("+00:00", "Z")


def build_records() -> tuple[list[Customer], list[Transaction]]:
    profiles = [
        {key: (0.0 if key == "screening_unresolved" else .05) for key in PROFILE_KEYS},
        {"ownership_opacity": .6, "business_complexity": .4, "geography_exposure": .7,
         "product_complexity": .5, "channel_opacity": .4, "source_of_funds_concern": .65,
         "adverse_information": .3, "pep_exposure": .1, "documentation_gap": .2,
         "screening_unresolved": 0, "cash_intensity": .5, "cross_border_exposure": .4},
        {"ownership_opacity": .9, "business_complexity": .8, "geography_exposure": .8,
         "product_complexity": .9, "channel_opacity": .8, "source_of_funds_concern": .9,
         "adverse_information": .7, "pep_exposure": .2, "documentation_gap": .5,
         "screening_unresolved": 1, "cash_intensity": .8, "cross_border_exposure": .6},
    ]
    segments = ("retail", "corporate", "small_business")
    expectations = (6000, 2000, 1200)
    customers, transactions = [], []
    for i, profile in enumerate(profiles):
        cid = f"example-customer-{i + 1:02d}"
        customers.append(Customer(
            customer_id=cid, as_of=prior(1), available_at=prior(1), segment=segments[i],
            onboarded_at=prior(400), history_start=prior(400), history_complete=True,
            profile=profile, expected_monthly_volume=expectations[i], source_id="invented-profile-v1",
        ))
        for j in range(80):
            if j < 60:
                days, amount = .25 + j / 2, 100
            else:
                days, amount = 30.5 + (j - 60) * 1.4, 300
            cash = (i == 1 and j % 2 == 0) or (i == 2 and j % 5 != 4)
            transactions.append(Transaction(
                transaction_id=f"example-transaction-{i + 1:02d}-{j:03d}", customer_id=cid,
                occurred_at=prior(days), available_at=prior(days), amount=amount,
                direction="in" if j % 2 else "out", channel="cash" if cash else "wire",
                counterparty_id=f"invented-counterparty-{i + 1:02d}-{j % 10:02d}",
                jurisdiction_risk=profile["geography_exposure"], source_id="invented-ledger-v1",
            ))
    return customers, transactions


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    customers, transactions = build_records()
    write_jsonl(ROOT / "customers.jsonl", customers)
    write_jsonl(ROOT / "transactions.jsonl", transactions)
    atomic_json(ROOT / "fixture-manifest.json", {
        "fixture_version": "1.0.0", "data_status": "synthetic_only", "as_of": AS_OF,
        "base_unit": UNIT, "customers": len(customers), "transactions": len(transactions),
        "transactions_per_customer": 80, "generator": "build_fixtures.py:build_records",
        "randomness": "none; explicitly constructed records", "policy_hash": reference_policy().digest,
        "files": {name: file_hash(ROOT / name) for name in ("customers.jsonl", "transactions.jsonl")},
        "interpretation": "Three constructed engineering fixtures, not a representative evaluation sample.",
    })
    print("Rebuilt 3 invented customers and 240 invented transactions in SYNTHETIC_UNIT.")


if __name__ == "__main__":
    main()
