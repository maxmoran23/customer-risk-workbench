"""Availability-aware aggregate features with explicit support and retention."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
from typing import Iterable

from .contracts import ContractError, Customer, Transaction, identifier, timestamp, utc

WINDOWS = {"1d": 1, "7d": 7, "30d": 30, "90d": 90, "180d": 180, "365d": 365}
LAST_N = {"last4": 4, "last10": 10, "last25": 25, "last50": 50}
METRICS = (
    "count",
    "total",
    "in_total",
    "out_total",
    "cash_share",
    "digital_share",
    "counterparty_count",
    "high_risk_share",
    "flow_through",
    "concentration",
    "mean_amount",
    "max_amount",
    "jurisdiction_coverage",
)


def digest(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


@dataclass
class FeatureSet:
    values: dict[str, float | None]
    quality: dict
    lineage: dict

    def to_dict(self):
        return {"values": self.values, "quality": self.quality, "lineage": self.lineage}


def aggregate(events: list[Transaction]) -> dict[str, float | None]:
    n = len(events)
    total = math.fsum(t.amount for t in events)
    incoming = math.fsum(t.amount for t in events if t.direction == "in")
    outgoing = math.fsum(t.amount for t in events if t.direction == "out")
    counterparties = Counter(t.counterparty_id for t in events)
    known = [t for t in events if t.jurisdiction_risk is not None]
    # Empty/zero-value populations do not establish a low behavioral ratio.
    return {
        "count": float(n),
        "total": total,
        "in_total": incoming,
        "out_total": outgoing,
        "cash_share": math.fsum(t.amount for t in events if t.channel == "cash") / total if total else None,
        "digital_share": math.fsum(t.amount for t in events if t.channel == "digital") / total
        if total
        else None,
        "counterparty_count": float(len(counterparties)),
        "high_risk_share": (
            math.fsum(t.amount * t.jurisdiction_risk for t in known) / total
            if total and len(known) == n
            else None
        ),
        "flow_through": min(incoming, outgoing) / max(incoming, outgoing)
        if max(incoming, outgoing)
        else None,
        "concentration": max(counterparties.values()) / n if n else None,
        "mean_amount": total / n if n else None,
        "max_amount": max((t.amount for t in events), default=None),
        "jurisdiction_coverage": len(known) / n if n else None,
    }


def build_features(
    customer: Customer,
    transactions: Iterable[Transaction],
    as_of: str,
    *,
    base_unit: str = "SYNTHETIC_UNIT",
) -> FeatureSet:
    base_unit = identifier(base_unit, "base_unit")
    cutoff = timestamp(as_of)
    if timestamp(customer.as_of) > cutoff or timestamp(customer.available_at) > cutoff:
        raise ContractError("profile was not effective and available at the assessment cutoff")
    seen: set[str] = set()
    events = []
    excluded_future = excluded_unavailable = 0
    for t in transactions:
        if t.customer_id != customer.customer_id:
            raise ContractError("foreign customer transaction in feature input")
        if t.transaction_id in seen:
            raise ContractError("duplicate transaction_id in feature input")
        seen.add(t.transaction_id)
        event_time = timestamp(t.occurred_at)
        if event_time < timestamp(customer.onboarded_at):
            raise ContractError("transaction predates onboarding")
        if event_time > cutoff:
            excluded_future += 1
        elif timestamp(t.available_at) > cutoff:
            excluded_unavailable += 1
        elif event_time >= timestamp(customer.history_start):
            events.append(t)
    events.sort(key=lambda t: (timestamp(t.occurred_at), t.transaction_id))
    values: dict[str, float | None] = {f"profile.{k}": v for k, v in customer.profile.items()}
    support = {}
    complete = {}
    history_days = (cutoff - timestamp(customer.history_start)).total_seconds() / 86400
    for window, days in WINDOWS.items():
        rows = [t for t in events if 0 <= (cutoff - timestamp(t.occurred_at)).total_seconds() < days * 86400]
        support[window] = len(rows)
        complete[window] = customer.history_complete and history_days >= days
        values.update({f"txn.{window}.{k}": v for k, v in aggregate(rows).items()})
    for window, n in LAST_N.items():
        rows = events[-n:]
        support[window] = len(rows)
        complete[window] = customer.history_complete and len(rows) >= n
        values.update({f"txn.{window}.{k}": v for k, v in aggregate(rows).items()})
    support["lifetime"] = len(events)
    complete["lifetime"] = customer.history_complete and customer.history_start == customer.onboarded_at
    values.update({f"txn.lifetime.{k}": v for k, v in aggregate(events).items()})
    values["txn.30d.expected_volume_ratio"] = (
        values["txn.30d.total"] / customer.expected_monthly_volume
        if customer.expected_monthly_volume and complete["30d"]
        else None
    )
    previous_30 = [
        t for t in events if 30 * 86400 <= (cutoff - timestamp(t.occurred_at)).total_seconds() < 60 * 86400
    ]
    previous_total = math.fsum(t.amount for t in previous_30)
    values["txn.30d.growth_ratio"] = (
        values["txn.30d.total"] / previous_total
        if previous_total and history_days >= 60 and customer.history_complete
        else None
    )
    values["profile_age_days"] = (cutoff - timestamp(customer.as_of)).total_seconds() / 86400
    values["tenure_days"] = (cutoff - timestamp(customer.onboarded_at)).total_seconds() / 86400
    values["observed_history_days"] = history_days
    lineage = {
        "cutoff": utc(as_of),
        "customer_id": customer.customer_id,
        "customer_snapshot": digest(customer.to_dict()),
        "event_digest": digest([t.to_dict() for t in events]),
        "source_ids": sorted({customer.source_id} | {t.source_id for t in events}),
        "feature_version": "1.0.0",
        "window_boundary": "(cutoff-duration, cutoff]",
        "last_n_tie_break": "occurred_at then transaction_id",
        "unit": base_unit,
    }
    quality = {
        "included_transactions": len(events),
        "excluded_future": excluded_future,
        "excluded_unavailable": excluded_unavailable,
        "support": support,
        "complete_windows": complete,
        "history_complete": customer.history_complete,
        "observed_history_days": history_days,
        "profile_missing": sorted(k for k, v in customer.profile.items() if v is None),
    }
    return FeatureSet(values, quality, lineage)


def feature_catalog(profile_keys: Iterable[str]) -> list[dict]:
    rows = [
        {
            "name": f"profile.{k}",
            "unit": "normalized 0..1",
            "meaning": "Adapter-supplied evidence; illustrative policy mapping",
        }
        for k in sorted(profile_keys)
    ]
    definitions = {
        "count": ("events", "Observed transaction count"),
        "total": ("base unit", "Observed amount sum"),
        "in_total": ("base unit", "Incoming amount sum"),
        "out_total": ("base unit", "Outgoing amount sum"),
        "cash_share": ("fraction", "Cash amount / total amount"),
        "digital_share": ("fraction", "Digital channel amount / total amount"),
        "counterparty_count": ("counterparties", "Distinct opaque counterparty IDs"),
        "high_risk_share": (
            "fraction",
            "Amount-weighted supplied jurisdiction risk; unknown if any exposure unmapped",
        ),
        "flow_through": ("fraction", "min(in,out) / max(in,out); aggregate balance proxy, not traced funds"),
        "concentration": ("fraction", "Largest counterparty event count / event count"),
        "mean_amount": ("base unit", "Total / count"),
        "max_amount": ("base unit", "Largest observed amount"),
        "jurisdiction_coverage": ("fraction", "Mapped events / all events"),
    }
    for w in [*WINDOWS, "lifetime", *LAST_N]:
        rows += [
            {"name": f"txn.{w}.{m}", "unit": definitions[m][0], "meaning": definitions[m][1]} for m in METRICS
        ]
    rows += [
        {"name": name, "unit": unit, "meaning": meaning}
        for name, unit, meaning in [
            (
                "txn.30d.expected_volume_ratio",
                "ratio",
                "30-day observed / declared monthly expectation; full window required",
            ),
            (
                "txn.30d.growth_ratio",
                "ratio",
                "30-day total / preceding 30 days; positive denominator and 60-day history required",
            ),
            ("profile_age_days", "days", "Cutoff minus effective profile timestamp"),
            ("tenure_days", "days", "Cutoff minus onboarding"),
            ("observed_history_days", "days", "Cutoff minus retained history start"),
        ]
    ]
    return rows
